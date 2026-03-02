import logging
import os
import re
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .chunking_strategies import get_chunker

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, embedding_function=None):
        """Initialize document processor with splitting tools for markdown."""
        self.embedding_function = embedding_function
        
        self.chunk_size = 1500
        self.chunk_overlap = 200
        
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n---\n", "\n", ".", ";", ":", " ", ""],
            keep_separator=True
        )
        
        self.chunker = get_chunker(
            'hierarchical',
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            parent_size=1500,
            parent_overlap=200,
        )

    def preprocess_text(self, text):
        """Remove unwanted noise from text while preserving table structure."""
        lines = text.splitlines()
        cleaned = []
        in_table = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped and not in_table:
                continue
            elif stripped.startswith("|") and not stripped.startswith("|-"):
                in_table = True
            elif stripped.startswith("|---"):
                in_table = True
            elif in_table and not stripped.startswith("|"):
                in_table = False
            cleaned.append(line)
        
        return "\n".join(cleaned).strip()

    def split_text_context_aware(self, text, metadata):
        """Split text using the hierarchical chunker, preserving table integrity."""
        temp_doc = Document(page_content=text, metadata=metadata)
        documents = self.chunker.split_documents([temp_doc])
        
        if not documents:
            logger.warning(f"No chunks created for document (type={metadata.get('type', 'text')}), using recursive splitting as fallback")
            recursive_chunks = self.recursive_splitter.split_text(text)
            documents = [Document(page_content=chunk.strip(), metadata=metadata) 
                        for chunk in recursive_chunks if chunk.strip()]
        
        # Ensure metadata is preserved
        for doc in documents:
            doc.metadata.update(metadata)  # Explicitly update to avoid metadata loss
            logger.debug(f"Chunk created: page={doc.metadata.get('page')}, content={doc.page_content[:50]}...")
        
        return documents

    def process_markdown_file(self, markdown_path):
        """Process a markdown file with multiple page headers and split into chunks."""
        try:
            if not os.path.exists(markdown_path) or os.path.getsize(markdown_path) == 0:
                logger.error(f"Markdown file not found or empty: {markdown_path}")
                return []

            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()

            cleaned_content = self.preprocess_text(content)
            chunks = []
            
            # First, look for all headers in the document to understand the structure
            all_headers = re.findall(r'##\s+(.+)', cleaned_content)
            logger.info(f"Found headers: {all_headers[:3]}...")
            
            # Split the document by headers - this pattern is more robust for finding headers
            sections = re.split(r'(?=##\s+)', cleaned_content)
            if sections and not sections[0].strip():
                sections.pop(0)
            
            default_source = os.path.basename(markdown_path).split('.')[0]
            last_page_number = None
            last_pdf_source = None
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                    
                # Print the first line for debugging
                # first_line = section.split('\n')[0] if '\n' in section else section
                # logger.debug(f"Processing section starting with: {first_line}")
                
                # Try to match the specific header pattern with URL
                # This pattern looks for: ## [URL] - Page [NUM] - [TITLE]
                header_match = re.search(r'##\s+(https?://[^\s-]+)\s+-\s+Page\s+(\d+)\s+-\s+(.+)', section)
                
                if header_match:
                    pdf_source = header_match.group(1).strip()  # URL
                    page_number = int(header_match.group(2))    # Page number
                    section_title = header_match.group(3).strip()  # Title
                    
                    last_pdf_source = pdf_source
                    last_page_number = page_number
                    
                    # logger.info(f"Matched URL header: {pdf_source} | Page {page_number} | {section_title}")
                elif '##' in section:
                    # Try a more general pattern for any header
                    general_match = re.search(r'##\s+(.+?)\s+-\s+Page\s+(\d+)\s+-\s+(.+)', section)
                    
                    if general_match:
                        pdf_source = general_match.group(1).strip()
                        page_number = int(general_match.group(2))
                        section_title = general_match.group(3).strip()
                        
                        last_pdf_source = pdf_source
                        last_page_number = page_number
                        
                        # logger.info(f"Matched general header: {pdf_source} | Page {page_number} | {section_title}")
                    else:
                        # Use fallbacks
                        pdf_source = last_pdf_source if last_pdf_source else default_source
                        page_number = last_page_number if last_page_number else 1
                        section_title = section.split('\n')[0].replace('##', '').strip()
                        
                        # logger.warning(f"No header match found, using fallback: {pdf_source}")
                else:
                    # Use fallbacks for content without headers
                    pdf_source = last_pdf_source if last_pdf_source else default_source
                    page_number = last_page_number if last_page_number else 1
                    section_title = ""
                    
                    # logger.warning(f"No header structure, using fallback: {pdf_source}")

                metadata = {
                    "source": pdf_source,
                    "original_source": pdf_source,
                    "type": "text",
                    "doc_type": "markdown",
                    "page": page_number,
                    "section": section_title
                }
                
                # Debug the metadata before chunk creation
                # logger.debug(f"Created metadata with source: {pdf_source}")
                
                section_chunks = self.split_text_context_aware(section, metadata)
                
                # Verify source in chunks
                if section_chunks:
                    logger.debug(f"First chunk source: {section_chunks[0].metadata.get('source')}")
                    
                chunks.extend(section_chunks)

            logger.info(f"Extracted {len(chunks)} chunks from {markdown_path}")
            return chunks

        except Exception as e:
            logger.error(f"Error processing markdown file {markdown_path}: {str(e)}", exc_info=True)
            return []

    def process_markdown_directory(self, directory_path):
        """Process all markdown files in a directory and its subdirectories."""
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return []

        all_chunks = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith('.md'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory_path)
                    logger.info(f"Processing markdown file: {relative_path}")
                    
                    chunks = self.process_markdown_file(file_path)
                    for chunk in chunks:
                        chunk.metadata.update({
                            "relative_path": relative_path,
                            "parent_directory": os.path.dirname(relative_path)
                        })
                        logger.debug(f"Final chunk: page={chunk.metadata.get('page')}, content={chunk.page_content[:50]}...")
                    all_chunks.extend(chunks)

        logger.info(f"Processed {len(all_chunks)} total chunks from directory: {directory_path}")
        return all_chunks

# Global instance
document_processor = DocumentProcessor()