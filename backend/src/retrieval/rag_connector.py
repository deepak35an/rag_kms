from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from src.models.session_model import SessionManager
from sentence_transformers import CrossEncoder
from langchain_core.documents import Document
from typing import Optional, Dict, List, Any
import numpy as np
import logging
import os
import asyncio
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from .bm25_retriever import BM25Retriever

try:
    from langchain_ollama import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Remove langchain_classic imports
# Replace create_history_aware_retriever etc with manual LCEL

logger = logging.getLogger(__name__)

class RAGConnector:
    def __init__(self, vectorstore, session_manager: SessionManager):
        """Initialize RAG connector with native vector store."""
        self.vectorstore = vectorstore
        self.session_manager = session_manager
        self.llm = self._initialize_llm()
        self.rag_chain = None
        self.semantic_cache = {}
        self.cache_threshold = 0.85
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.bm25_retriever = None

    # ... _initialize_llm kept as is ... (omitted in replacement if not targeted, but I will include it to be safe)
    def _initialize_llm(self):
        """Initialize LLM: only use local Ollama."""
        # --- Local Ollama (llama3.2:3b-instruct-q4_K_M) ---
        if OLLAMA_AVAILABLE:
            try:
                llm = ChatOllama(
                    model="gemma3:4b",
                    temperature=0.1,
                    num_predict=1024,
                )
                # Ping Ollama to confirm it's running
                llm.invoke("ping")
                logger.info("Using local Ollama LLM: gemma3:4b")
                return llm
            except Exception as e:
                logger.error(f"FATAL: Local Ollama LLM failed to initialize or is not reachable: {e}")
                logger.error("Please ensure Ollama is installed and running with 'ollama serve'.")
                return None
        else:
            logger.error("FATAL: langchain-ollama is not installed. LLM features will be disabled.")
            return None

    async def initialize_hybrid_retrieval(self):
        """Build BM25 index from all documents in vector store."""
        logger.info("Initializing hybrid retrieval (BM25 index build)...")
        try:
            # Scroll all docs from Qdrant
            corpus = self.vectorstore.scroll_all()
            if not corpus:
                logger.warning("Empty corpus retrieved from Qdrant. BM25 will not be available.")
                return
            
            # Initialize BM25 retriever
            self.bm25_retriever = BM25Retriever(corpus)
            logger.info(f"Hybrid retrieval initialized with {len(corpus)} documents.")
        except Exception as e:
            logger.error(f"Failed to initialize hybrid retrieval: {e}")

    def _get_retriever_lambda(self):
        """Returns a runnable lambda that performs hybrid search."""
        return RunnableLambda(lambda q: self.hybrid_similarity_search(q, k=10))

    async def hybrid_similarity_search(self, query: str, k: int = 10) -> List[Document]:
        """
        Execute Hybrid Retrieval Pipeline:
        1. Dense retrieval (25 chunks)
        2. BM25 retrieval (25 chunks)
        3. Fusion (Weighted Min-Max) -> Top 20
        4. Cross-encoder rerank top 15 -> Top 10
        """
        logger.info(f"Starting hybrid similarity search for: {query[:50]}...")
        
        # Stage 1: Parallel Execution
        dense_fetch = 25
        bm25_fetch = 25
        
        # Dense task
        dense_task = self.vectorstore.similarity_search(query, k=dense_fetch)
        
        # BM25 task
        if self.bm25_retriever:
            bm25_task = self.bm25_retriever.retrieve(query, bm25_fetch)
            
            # Run in parallel
            dense_docs, (bm25_ids, bm25_scores) = await asyncio.gather(dense_task, bm25_task)
        else:
            logger.warning("BM25 retriever not initialized. Falling back to dense search.")
            return await dense_task

        # Stage 2: Weighted Fusion (0.65 Dense / 0.35 BM25)
        # We need dense scores. Similarity search returns Document objects. 
        # VectorStore.similarity_search puts the score in metadata["distance"]
        dense_ids = [d.metadata.get("id") or str(hash(d.page_content)) for d in dense_docs]
        dense_scores = [d.metadata.get("distance", 0.0) for d in dense_docs]
        
        fused_results = self._fuse_with_minmax(
            dense_ids, dense_scores,
            bm25_ids, bm25_scores,
            dense_weight=0.65,
            bm25_weight=0.35
        )
        
        # Get top 20 fused results
        top_fused = fused_results[:20]
        
        # Stage 3: Selective Reranking on Top 15 Fused Results
        rerank_input_k = 15
        top_candidates = top_fused[:rerank_input_k]
        
        # Map IDs back to full documents
        doc_map = {d.metadata.get("id") or str(hash(d.page_content)): d for d in dense_docs}
        
        # For BM25 results not in dense_docs, we need to find them (optional complexity)
        # Simplified: Use dense_docs as the primary source for document content
        rerank_docs = []
        for doc_id, fusion_score in top_candidates:
            if doc_id in doc_map:
                doc = doc_map[doc_id]
                doc.metadata["fusion_score"] = fusion_score
                rerank_docs.append(doc)
            else:
                # If BM25 found something dense didn't, we'd normally fetch it.
                # For this implementation, we'll try to find it in the BM25 corpus if possible
                bm25_doc = next((d for d in self.bm25_retriever.corpus if d['id'] == doc_id), None)
                if bm25_doc:
                    doc = Document(
                        page_content=bm25_doc['text'],
                        metadata={**bm25_doc.get('metadata', {}), "fusion_score": fusion_score}
                    )
                    rerank_docs.append(doc)

        if not rerank_docs:
            return dense_docs[:k]

        # Stage 4: Cross-Encoder Rerank
        query_doc_pairs = [(query, d.page_content) for d in rerank_docs]
        ce_scores = await asyncio.to_thread(self.cross_encoder.predict, query_doc_pairs)
        
        # Normalize CE scores
        ce_norm = self._minmax_normalize(ce_scores.tolist())
        
        # Final Scoring (0.7 Fusion / 0.3 CE)
        final_docs = []
        for doc, ce_s in zip(rerank_docs, ce_norm):
            fusion_s = doc.metadata.get("fusion_score", 0.0)
            final_score = 0.7 * fusion_s + 0.3 * ce_s
            doc.metadata["relevance_score"] = float(final_score)
            final_docs.append(doc)
            
        # Stage 5: Sort and Deduplicate by Content
        final_docs.sort(key=lambda x: x.metadata.get("relevance_score", 0.0), reverse=True)
        
        seen_content = set()
        unique_results = []
        for doc in final_docs:
            # Normalize content for robust deduplication (strip and collapse whitespace)
            normalized_content = " ".join(doc.page_content.lower().split())
            content_hash = hash(normalized_content)
            
            if content_hash not in seen_content:
                unique_results.append(doc)
                seen_content.add(content_hash)
            if len(unique_results) >= k:
                break
                
        logger.info(f"Hybrid search returned {len(unique_results)} unique content chunks.")
        return unique_results

    async def generate_answer(self, question: str, k: int = 5) -> Dict[str, Any]:
        """
        Full RAG pipeline: hybrid retrieval -> LLM answer generation.
        Returns a dict with 'answer', 'sources', and 'retrieved_chunks'.
        """
        if not self.llm:
            raise ValueError("LLM not initialized. Check Ollama service or OPENROUTER_API_KEY.")

        # Step 1: Hybrid Retrieval
        docs = await self.hybrid_similarity_search(question, k=k)

        if not docs:
            return {
                "answer": "I could not find any relevant documents to answer your question.",
                "sources": [],
                "retrieved_chunks": []
            }

        # Step 2: Format context — heavily labeled for citation
        context_parts = []
        for i, d in enumerate(docs, 1):
            source = d.metadata.get('source', '?')
            page = d.metadata.get('page', '?')
            context_parts.append(
                f"--- [START CHUNK {i}] ---\nSOURCE: {source}\nPAGE: {page}\nCONTENT:\n{d.page_content.strip()}\n--- [END CHUNK {i}] ---"
            )
        context = "\n\n".join(context_parts)

        # Reinforce formatting in the human turn
        formatted_question = (
            f"{question}\n\n"
            "Using the context above, provide a detailed and well-structured answer. "
            "If the answer involves steps, use a numbered list and explain each step clearly. "
            "Do not give a one-line answer — elaborate on each point with a short explanation."
        )

        # Step 3: Build prompt and invoke LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("human", "{input}")
        ])

        chain = prompt | self.llm | StrOutputParser()
        answer = await asyncio.to_thread(
            chain.invoke,
            {"context": context, "input": formatted_question}
        )

        # Step 4: Build sources list
        sources = self._extract_sources(docs)

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": [d.page_content for d in docs]
        }

    def _minmax_normalize(self, scores: List[float]) -> List[float]:
        if not scores: return []
        if len(scores) == 1: return [1.0]
        s_arr = np.array(scores)
        min_s, max_s = s_arr.min(), s_arr.max()
        if max_s == min_s: return [1.0] * len(scores)
        return ((s_arr - min_s) / (max_s - min_s)).tolist()

    def _fuse_with_minmax(self, dense_ids, dense_scores, bm25_ids, bm25_scores, 
                          dense_weight=0.5, bm25_weight=0.5):
        """Weighted Min-Max Fusion."""
        dense_norm = self._minmax_normalize(dense_scores)
        bm25_norm = self._minmax_normalize(bm25_scores)
        
        score_dict = {}
        for d_id, score in zip(dense_ids, dense_norm):
            score_dict[d_id] = score_dict.get(d_id, 0.0) + (score * dense_weight)
        
        for b_id, score in zip(bm25_ids, bm25_norm):
            score_dict[b_id] = score_dict.get(b_id, 0.0) + (score * bm25_weight)
        
        return sorted(score_dict.items(), key=lambda x: x[1], reverse=True)

    def _setup_rag_chain(self, query: Optional[str] = None):
        """Set up the RAG chain using LCEL."""
        
        # 1. Contextualize Question (History Aware)
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question about JAC Chandigarh, "
            "formulate a standalone question which can be understood without the chat history. "
            "Do NOT answer the question, just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        # Chain to generate standalone question
        history_aware_chain = contextualize_q_prompt | self.llm | StrOutputParser()
        
        # 2. QA Chain
        qa_system_prompt = self._get_system_prompt()
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
        ])
        
        # Define chain: 
        # Logic: 
        #   IF chat_history exists: generate standalone question -> retrieve -> answer
        #   ELSE: input -> retrieve -> answer
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Retrieval chain (Input: string -> Output: List[Docs])
        # We define this HERE to capture 'search_kwargs' from the outer scope
        # Note: we ignore filter for now as hybrid search needs to adapt it
        retriever = RunnableLambda(lambda q: self.hybrid_similarity_search(q, k=10))

        # Chain that preserves context for the final output
        # 1. Start with input
        # 2. Add standalone_question
        # 3. Add context (List[Documents])
        # 4. Add answer (String)
        async def retrieve_docs_async(x):
            return await self.hybrid_similarity_search(x["standalone_question"], k=10)

        # Chain that preserves context for the final output
        full_chain = (
            RunnablePassthrough.assign(
                standalone_question=history_aware_chain
            )
            | RunnablePassthrough.assign(
                context=RunnableLambda(retrieve_docs_async)
            )
            | RunnablePassthrough.assign(
                answer=(
                    RunnablePassthrough.assign(context=lambda x: format_docs(x["context"]))
                    | qa_prompt
                    | self.llm
                    | StrOutputParser()
                )
            )
        )
        
        return full_chain


    def _get_system_prompt(self) -> str:
        """Get the system prompt that produces detailed, well-structured RAG answers."""
        return """
You are a professional assistant expert in synthesizing complex information from retrieved documents.
Your goal is to provide precise, well-structured answers based ONLY on the provided context.

=== CORE COMMANDMENTS ===
1. STRICT CONTEXT ADHERENCE: Answer using only the provided CONTEXT. Do not use outside knowledge.
2. CITATIONS: You MUST cite the source chunk for every significant fact or claim. Use the format "[Chunk X]" (e.g., "According to the guidelines [Chunk 1]...").
3. UNCERTAINTY: If the answer is not in the context, say: "I'm sorry, but I don't have enough information in the provided documents to answer that."

=== STRUCTURE & STYLE ===
1. SUMMARY: Start with a 1-sentence direct answer.
2. FORMATTING:
   - Use **bold titles** for distinct sections.
   - Use bullet points or numbered lists for readability.
   - Use bold text to highlight key terms or dates.
3. DEPTH: Elaborate on points found in the context. Do not give one-word answers.
4. TONE: Professional and objective.

=== CONTEXT SECTIONS ===
{context}
========================
"""

    def get_chain(self, query: Optional[str]):
        """Get or initialize the RAG chain."""
        if self.rag_chain is None or query:
            self.rag_chain = self._setup_rag_chain(query)
        return self.rag_chain

    def _find_similar_cached_query(self, query: str):
        """Find similar query in cache."""
        if not self.semantic_cache:
            return None, None
            
        # Access the embedding function from the vectorstore's _embedding_function attribute
        # or use the embedding function directly if available
        try:
            # Try to access the embedding function from the vectorstore
            if hasattr(self.vectorstore, '_embedding_function'):
                query_embedding = self.vectorstore._embedding_function.embed_query(query)
            elif hasattr(self.vectorstore, 'embedding_function'):
                query_embedding = self.vectorstore.embedding_function.embed_query(query)
            else:
                # If we can't find the embedding function, log a warning and return no match
                logger.warning("Could not find embedding function in vectorstore")
                return None, None
                
            max_similarity = 0
            most_similar_query = None
            
            for cached_query, cache_data in self.semantic_cache.items():
                cached_embedding = cache_data.get("embedding")
                if cached_embedding:
                    similarity = self._calculate_similarity(query_embedding, cached_embedding)
                    if similarity > max_similarity:
                        max_similarity = similarity
                        most_similar_query = cached_query
            
            if max_similarity >= self.cache_threshold and most_similar_query:
                return most_similar_query, self.semantic_cache[most_similar_query]
            return None, None
        except Exception as e:
            logger.warning(f"Error finding similar cached query: {str(e)}")
            return None, None

    def _calculate_similarity(self, vec1, vec2):
        """Calculate similarity using both vector similarity and keyword matching.
        
        This combines cosine similarity with keyword-based relevance scoring similar to the Generator class.
        """
        # Calculate cosine similarity between embeddings
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        cosine_sim = dot_product / norm_product if norm_product != 0 else 0
        
        # We return cosine similarity as the primary method since we don't have access to the
        # original query text and document content in this method, which would be needed for
        # keyword-based scoring. The keyword-based scoring is handled in _rerank_documents.
        return cosine_sim

    async def process_question(self, data: Dict[str, Any]):
        """Process a question with markdown-only context without using LLM.
        
        This implementation matches the Generator class approach but without LLM usage.
        """
        session_id = data.get("session_id")
        question = data.get("question")

        if not session_id or not question:
            raise HTTPException(status_code=400, detail="Session ID and question are required.")
            
        logger.info(f"Processing question for session {session_id}: {question[:50]}...")
        
        try:
            # Check cache first
            similar_query, cache_data = self._find_similar_cached_query(question)
            
            if similar_query and cache_data:
                logger.info(f"Cache hit for: {similar_query}")
                return JSONResponse(content={
                    "session_id": session_id,
                    "question": question,
                    "response": cache_data["answer"],
                    "sources": cache_data["sources"],
                    "cached": True
                })
            
            # Direct retrieval without using LLM chain
            search_kwargs = {"k": 10}
            
            # Apply filters if needed
            filter_conditions = []
            institutes = {
                "uiet": "University Institute of Engineering and Technology",
                "ccet": "Chandigarh College of Engineering and Technology",
                "uicet": "University Institute of Chemical Engineering and Technology",
                "pussgrc": "Panjab University SSG Regional Centre",
                "cca": "Chandigarh College of Architecture"
            }
            query_lower = question.lower()
            for abbr, full_name in institutes.items():
                if abbr.lower() in query_lower or full_name.lower() in query_lower:
                    filter_conditions.append({"doc_type": "markdown"})
                    break

            if filter_conditions:
                search_kwargs["filter"] = (
                    {"$and": filter_conditions} if len(filter_conditions) > 1 
                    else filter_conditions[0]
                )
            
            # Get retriever and retrieve documents directly
            retriever = (
                self.vectorstore.get_retriever(search_kwargs=search_kwargs)
                if hasattr(self.vectorstore, 'get_retriever')
                else self.vectorstore.as_retriever(search_kwargs=search_kwargs)
            )
            
            # Retrieve documents (async-safe with Qdrant)
            retrieved_docs = await retriever.invoke(question)
            
            # Log retrieved documents for debugging (same as Generator class)
            for i, doc in enumerate(retrieved_docs):
                logger.debug(f"Retrieved doc {i}: page={doc.metadata.get('page')}, source={doc.metadata.get('source')}, content={doc.page_content[:50]}...")
            
            # Validate and score retrieved documents (same as Generator._validate_retrieved_docs)
            validated_docs = self._validate_retrieved_docs(retrieved_docs, question)
            
            # Extract source information from validated documents (using existing method)
            sources = self._extract_sources(validated_docs)
            
            # Format document content with deduplication
            document_chunks = [doc.page_content for doc in validated_docs]
            
            # Deduplicate document chunks using hash-based approach
            unique_chunks = []
            seen_chunks = set()
            for chunk in document_chunks:
                chunk_hash = hash(chunk)
                if chunk_hash not in seen_chunks:
                    seen_chunks.add(chunk_hash)
                    unique_chunks.append(chunk)
            
            # Join unique chunks with separator for better readability
            chunks_content = "\n\n---\n\n".join(unique_chunks) if unique_chunks else "No relevant documents found."
            
            # Cache the results
            try:
                # Try to access the embedding function from the vectorstore
                if hasattr(self.vectorstore, '_embedding_function'):
                    query_embedding = self.vectorstore._embedding_function.embed_query(question)
                elif hasattr(self.vectorstore, 'embedding_function'):
                    query_embedding = self.vectorstore.embedding_function.embed_query(question)
                else:
                    logger.warning("Could not find embedding function in vectorstore, skipping cache")
                    query_embedding = None
                
                # Only cache if we have an embedding
                if query_embedding is not None:
                    self.semantic_cache[question] = {
                        "answer": chunks_content,
                        "sources": sources,
                        "embedding": query_embedding
                    }
            except Exception as e:
                logger.warning(f"Error caching query: {str(e)}")
                # Continue without caching
            
            logger.info(f"Successfully processed question for session {session_id}")
            
            # Return raw document chunks without updating session history
            return JSONResponse(content={
                "session_id": session_id,
                "question": question,
                "response": chunks_content,
                "sources": sources
            })
            
        except Exception as e:
            logger.error(f"Error processing question for session {session_id}: {str(e)}")
            return JSONResponse(content={"error": f"Error processing question: {str(e)}"})

    def _validate_retrieved_docs(self, documents: List[Document], query: str) -> List[Document]:
        """Validate and score retrieved markdown documents based on query relevance.
        
        This method matches the Generator class implementation for consistency.
        """
        query_keywords = set(query.lower().split())
        validated_docs = []
        
        for doc in documents:
            content = doc.page_content.lower()
            relevance_score = sum(1 for kw in query_keywords if kw in content) / max(1, len(query_keywords))
            doc.metadata["relevance_score"] = relevance_score
            
            # Log page number issues
            page = doc.metadata.get("page")
            if page is None or not isinstance(page, int) or page < 1:
                logger.debug(f"Invalid or missing page number in doc from {doc.metadata.get('source', 'unknown')}: {page}")
            
            if relevance_score > 0.1:
                validated_docs.append(doc)
        
        validated_docs.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
        return validated_docs
        
    def _rerank_documents(self, query: str, documents: List[Document]) -> List[Document]:
        """Rerank documents using cross-encoder and keyword matching.
        
        This combines neural reranking with keyword-based relevance scoring similar to the Generator class.
        """
        if not documents:
            return documents
            
        # First, calculate keyword-based relevance scores (same as Generator class)
        query_keywords = set(query.lower().split())
        for doc in documents:
            content = doc.page_content.lower()
            keyword_score = sum(1 for kw in query_keywords if kw in content) / max(1, len(query_keywords))
            doc.metadata["keyword_score"] = float(keyword_score)
        
        # Then use cross-encoder for neural reranking
        query_doc_pairs = [(query, doc.page_content) for doc in documents]
        neural_scores = self.cross_encoder.predict(query_doc_pairs)
        
        # Combine documents with both scores
        for doc, neural_score in zip(documents, neural_scores):
            # Combine both scores (equal weighting)
            keyword_score = doc.metadata.get("keyword_score", 0.0)
            combined_score = (neural_score + keyword_score) / 2.0
            doc.metadata["relevance_score"] = float(combined_score)
        
        # Sort by combined relevance score
        documents.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
        
        # Filter out documents with very low relevance (similar to Generator)
        return [doc for doc in documents if doc.metadata.get("relevance_score", 0) > 0.1]

    def _format_document(self, doc: Document) -> Dict[str, Any]:
        """Format document for response (text-only)."""
        return {
            "type": "text",
            "content": doc.page_content,
            "metadata": doc.metadata
        }

    def _extract_sources(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Extract source information from retrieved markdown documents.
        
        This method is aligned with the Generator class implementation to ensure consistency.
        """
        sources = []
        for doc in documents:
            if not hasattr(doc, 'metadata'):
                continue
                
            metadata = doc.metadata
            # Prioritize original_source over source
            source_path = metadata.get("original_source", metadata.get("source", "Unknown source"))
            source_name = os.path.basename(source_path) if source_path else "Unknown source"
            
            # Validate page number
            page = metadata.get("page")
            if page is None:
                logger.warning(f"Page number missing for document from {source_name}. Defaulting to 1.")
                page = 1
            elif not isinstance(page, int) or page < 1:
                logger.warning(f"Invalid page number {page} for {source_name}. Defaulting to 1.")
                page = 1

            # Check for table-specific metadata
            table_number = metadata.get("table_number")
            content_type = "table" if table_number is not None else metadata.get("type", "text")

            source_info = {
                "source": source_name,
                "type": content_type,
                "relevance": metadata.get("relevance_score", 1.0),  # Using relevance_score from metadata
                "content_preview": doc.page_content[:200],
                "page": page,
                "section": metadata.get("section", ""),
            }
            
            if table_number is not None:
                source_info["table_number"] = table_number

            sources.append(source_info)
        
        return sorted(sources, key=lambda x: x["relevance"], reverse=True)