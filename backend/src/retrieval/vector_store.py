import logging
import time
import os
import shutil
import uuid
import asyncio
from typing import List, Optional, Tuple, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from langchain_core.documents import Document
from ..preprocessing.chunking_strategies import get_chunker, get_chunker_for_document_type

# Configure logging
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, embedding_model, chunk_size=800, chunk_overlap=150):
        """
        Initialize vector store using native Qdrant client.
        
        Args:
            embedding_model: The EmbeddingModel instance (must provide embed_documents and embed_query)
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.embedding_model = embedding_model
        self.persist_directory = "./qdrant_storage"
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.collection_name = "rag4gov_documents"
        self.vector_size = getattr(self.embedding_model, 'dimension', 384)
        
        # Initialize Qdrant client
        logger.info(f"Initializing Qdrant client at {self.persist_directory}")
        try:
            self.client = QdrantClient(path=self.persist_directory)
            
            # Check if collection exists, create if not
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating new Qdrant collection '{self.collection_name}'")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
            else:
                logger.info(f"Qdrant collection '{self.collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise e

    def create_or_load(self):
        """
        Idempotent initialization (client is already created in __init__).
        Kept for API compatibility with existing calls.
        """
        return self

    def add_documents(self, documents: List[Document], batch_size: int = 10, num_workers: int = 4):
        """
        Add documents to vector store using Qdrant upsert.
        """
        if not documents:
            logger.warning("No documents to add.")
            return

        start_time = time.time()
        
        # Split documents
        text_documents = [d for d in documents if d.metadata.get("type") != "table"]
        table_documents = [d for d in documents if d.metadata.get("type") == "table"]
        
        # Use hierarchical chunking for production ingestion
        chunker = get_chunker(
            'hierarchical',
            embedding_function=self.embedding_model,
            parent_size=1500,
            child_size=self.chunk_size,
            parent_overlap=200,
            child_overlap=self.chunk_overlap
        )
        
        splits = chunker.split_documents(text_documents)
        splits.extend(table_documents)
        
        logger.info(f"Prepared {len(splits)} chunks for ingestion.")
        
        # Process in batches
        total_batches = (len(splits) - 1) // batch_size + 1
        
        for i in range(0, len(splits), batch_size):
            batch = splits[i:i + batch_size]
            batch_num = i // batch_size + 1
            
            # Prepare data for Qdrant format
            batch_texts = [doc.page_content for doc in batch]
            
            # Generate embeddings explicitly
            try:
                batch_embeddings = self.embedding_model.embed_documents(batch_texts)
            except Exception as e:
                logger.error(f"Embedding generation failed for batch {batch_num}: {e}")
                continue

            # Create PointStruct objects for Qdrant
            points = []
            for j, doc in enumerate(batch):
                point_id = str(uuid.uuid4())
                
                # Prepare payload: metadata + document text
                payload = dict(doc.metadata)
                payload["text"] = doc.page_content
                
                point = PointStruct(
                    id=point_id,
                    vector=batch_embeddings[j],
                    payload=payload
                )
                points.append(point)
            
            # Upsert to Qdrant
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"Batch {batch_num}/{total_batches} added ({len(batch)} docs).")
            except Exception as e:
                logger.error(f"Failed to add batch {batch_num} to Qdrant: {e}")
                
        logger.info(f"Vector store update completed in {time.time() - start_time:.2f} seconds")
        return self

    async def similarity_search(self, query: str, k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Perform similarity search using Qdrant search.
        Returns List[Document] for compatibility.
        """
        try:
            logger.info(f"Starting similarity_search for query: {query}")

            logger.info("Generating query embedding...")
            # Qdrant client is thread-safe, but we'll still use async for consistency
            query_embedding = await asyncio.to_thread(self.embedding_model.embed_query, query)
            logger.info("Query embedding generated successfully.")

            # Prepare Qdrant filter if provided
            qdrant_filter = None
            if filter:
                # Convert simple dict filter to Qdrant Filter format
                # Example: {"doc_type": "markdown"} -> Filter with FieldCondition
                conditions = []
                for key, value in filter.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)

            logger.info(f"Querying Qdrant collection '{self.collection_name}' with k={k}")

            # Perform search using query_points (correct Qdrant API method)
            search_results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=k,
                query_filter=qdrant_filter
            ).points

            logger.info(f"Qdrant search returned {len(search_results)} results.")

            # Convert Qdrant results to LangChain Documents
            documents = []
            for result in search_results:
                payload = result.payload
                
                # Extract text from payload
                text = payload.pop("text", "")
                
                # Remaining payload is metadata
                metadata = dict(payload)
                metadata["id"] = result.id  # Store Qdrant point ID for fusion matching
                metadata["distance"] = result.score  # Qdrant returns score (higher is better for cosine)
                
                doc = Document(
                    page_content=text,
                    metadata=metadata
                )
                documents.append(doc)

            logger.info(f"Converted {len(documents)} documents.")
            return documents

        except Exception as e:
            logger.error(f"Similarity search failed: {e}", exc_info=True)
            return []

    def scroll_all(self, batch_size: int = 100, kb_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve ALL documents (or filtered by kb_id) from Qdrant using scroll.
        Used for building BM25 index on startup or per-KB index.
        """
        all_docs = []
        next_offset = None

        # Build filter if kb_id is provided
        scroll_filter = None
        if kb_id:
            scroll_filter = Filter(must=[FieldCondition(key="kb_id", match=MatchValue(value=kb_id))])
        
        try:
            while True:
                results, next_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=batch_size,
                    offset=next_offset,
                    with_payload=True,
                    with_vectors=False,
                    scroll_filter=scroll_filter
                )
                
                for res in results:
                    payload = res.payload
                    doc_id = res.id
                    text = payload.get("text", "")
                    all_docs.append({
                        "id": doc_id,
                        "text": text,
                        "metadata": payload
                    })
                
                if next_offset is None:
                    break
                    
            logger.info(f"Scrolled {len(all_docs)} documents from Qdrant.")
            return all_docs
        except Exception as e:
            logger.error(f"Error scrolling documents: {e}")
            return []


    # Compatibility methods for consumers that might call .get_retriever()
    
    def as_retriever(self, **kwargs):
        """Legacy compatibility: Return self as it implements invoke()."""
        return self

    async def invoke(self, query: str):
        """
        Allow VectorStore to act like a LangChain retriever for backwards compatibility.
        """
        q = query if isinstance(query, str) else str(query)
        return await self.similarity_search(q, k=10)

    def get_retriever(self, search_kwargs=None):
        return self