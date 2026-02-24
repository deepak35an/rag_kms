"""
Document preprocessing module for the RAG4GOV system.

This module handles processing of various document formats (PDF, images, etc.) 
into text suitable for the RAG system. It includes functionality for:
- PDF text extraction
- Image OCR processing
- Document cleaning and normalization
- File handling utilities
"""
import warnings
import pdfplumber
import pymupdf4llm
from pdf2image import convert_from_path
from rapidocr_onnxruntime import RapidOCR
import logging
import os
import shutil
import zipfile
import tarfile
import re
from langchain_core.documents import Document
from dotenv import load_dotenv
from tabulate import tabulate
import fitz  # PyMuPDF
from PIL import Image
import io
from .ocr_cleanup import cleanup_ocr_text

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress pdfplumber warnings
logging.getLogger("pdfplumber").setLevel(logging.ERROR)
logging.getLogger("pdfplumber.pdfpage").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=Warning, module="pdfplumber")

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Main document processor class that handles conversion of documents to text.
    
    Attributes:
        pdf_folder (str): Path to directory containing PDF files to process
    """
    def __init__(self):
        """
        Initialize document processor for PDF to Markdown conversion.
        
        Sets up default PDF folder path and logging configuration.
        """
        self.pdf_folder = "./public/"

    def preprocess_text(self, text):
        """
        Clean and normalize extracted text by removing noise.
        
        Args:
            text (str): Raw extracted text from document
            
        Returns:
            str: Cleaned text with headers, footers and noise removed
        """
        lines = text.splitlines()
        cleaned = [line for line in lines if not re.match(r"^(Page \d+|.*\d+ of \d+)$", line.strip())]
        return "\n".join(cleaned).strip()

    def get_pdf_paths(self, folder_path=None):
        """
        Recursively find all PDF files in specified directory.
        
        Args:
            folder_path (str, optional): Directory to search. Defaults to PDF folder.
            
        Returns:
            list: List of absolute paths to found PDF files
            
        Raises:
            FileNotFoundError: If no PDF files are found in directory
        """
        folder_path = folder_path or self.pdf_folder
        pdf_paths = [os.path.join(root, f) for root, _, files in os.walk(folder_path) 
                    for f in files if f.lower().endswith('.pdf')]
        if not pdf_paths:
            raise FileNotFoundError(f"No PDF files found in {folder_path}")
        logger.info(f"Found {len(pdf_paths)} PDF files in {folder_path}")
        return pdf_paths

    def extract_page_content(self, page, pdf_path, page_num):
        """
        Extract all content from a page including text, tables, and detected headings as Markdown.
        
        Args:
            page: PDF page object from pdfplumber
            pdf_path (str): Path to the PDF file
            page_num (int): Page number
            
        Returns:
            Document: Combined text content including tables and formatted headings
        """
        # Extract base text
        base_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
        base_text = self.preprocess_text(base_text)

        # Detect headings based on font size
        words = page.extract_words()
        for word in words:
            if word.get("size", 0) > 12:  # Threshold for heading detection (adjust as needed)
                base_text = base_text.replace(word["text"], f"### {word['text']}")

        # Extract tables as Markdown
        table_texts = []
        try:
            tables = page.extract_tables(table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 2,
                "snap_tolerance": 3,
                "join_tolerance": 3,
                "edge_min_length": 3,
                "min_words_vertical": 1
            })
            
            for table_num, table in enumerate(tables, start=1):
                if not table or not isinstance(table, list):
                    continue
                # Convert table to Markdown using tabulate
                table_text = tabulate(table, tablefmt="pipe")
                table_texts.append(f"\n### Table {table_num}\n{table_text}")
        except Exception as e:
            logger.debug(f"Error extracting tables from page {page_num}: {str(e)}")
        
        # Combine all content
        combined_text = base_text
        if table_texts:
            combined_text += "\n\n" + "\n\n".join(table_texts)
        
        # Extract original PDF name from path
        original_pdf_name = os.path.basename(pdf_path)
        original_source = original_pdf_name
        
        # Determine section title from first line if available
        lines = combined_text.strip().split('\n')
        section_title = lines[0] if lines and len(lines[0]) < 100 else None
        
        # Create metadata
        pdf_id = os.path.splitext(original_source)[0]
        formatted_page_title = f"## {pdf_id} - Page {page_num} - {section_title if section_title else ''}"
        
        metadata = {
            "source": original_source,
            "pdf_path": pdf_path,
            "page": page_num,
            "type": "content",
            "section": section_title,
            "doc_type": "pdf",
            "original_source": original_source,
            "page_title": formatted_page_title
        }
        
        return Document(page_content=combined_text, metadata=metadata)

    def extract_images_with_ocr(self, pdf_path):
        """
        Extract embedded images from PDF and apply OCR to recognize text within images using RapidOCR.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            dict: Dictionary mapping page numbers to list of OCR text from images on that page
        """
        image_text_by_page = {}
        
        try:
            # Initialize RapidOCR engine with specific English-only models
            # use_dilation=True helps detect space between words by expanding detection boxes
            ocr_engine = RapidOCR(
                det_model_dir='en_PP-OCRv3_det',
                rec_model_dir='en_PP-OCRv3_rec',
                use_dilation=True
            )
            
            pdf_document = fitz.open(pdf_path)
            logger.info(f"Extracting images from {pdf_path} for OCR processing with RapidOCR...")
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                image_list = page.get_images(full=True)
                
                if not image_list:
                    continue
                    
                page_image_texts = []
                
                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = pdf_document.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Convert to PIL Image for RapidOCR
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        
                        # Convert PIL Image to numpy array for RapidOCR
                        import numpy as np
                        image_np = np.array(pil_image)
                        
                        # Apply RapidOCR
                        # RapidOCR returns: (result, elapse_time) where result is a list of [bbox, text, confidence]
                        result, _ = ocr_engine(image_np)
                        
                        if result:
                            # Extract text from all detected regions and combine
                            raw_ocr_text = "\n".join([line[1] for line in result if line[1].strip()])
                            
                            if raw_ocr_text.strip():
                                # Apply intelligent cleanup and formatting
                                cleaned_text = cleanup_ocr_text(raw_ocr_text)
                                
                                if cleaned_text:
                                    page_image_texts.append(cleaned_text)
                                    logger.debug(f"Extracted and cleaned {len(cleaned_text)} chars from image {img_index} on page {page_num + 1}")
                    
                    except Exception as e:
                        logger.warning(f"Failed to OCR image {img_index} on page {page_num + 1}: {str(e)}")
                
                if page_image_texts:
                    image_text_by_page[page_num + 1] = page_image_texts
                    logger.info(f"Page {page_num + 1}: Extracted text from {len(page_image_texts)} image(s)")
            
            pdf_document.close()
            
        except Exception as e:
            logger.error(f"Error extracting images from {pdf_path}: {str(e)}")
        
        return image_text_by_page

    def load_pdf_with_pymupdf4llm(self, pdf_path):
        """
        Extract text and tables from PDF as high-quality Markdown using pymupdf4llm,
        enhanced with OCR for embedded images.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            list: List of Document objects with Markdown content and image OCR text
        """
        documents = []
        pdf_name = os.path.basename(pdf_path)
        original_source = os.path.splitext(pdf_name)[0]
        
        try:
            # Extract text from embedded images using PyMuPDF + pytesseract
            image_text_by_page = self.extract_images_with_ocr(pdf_path)
            
            # pymupdf4llm.to_markdown returns a list of dictionaries, one per page
            # Each dict contains: "page": page_index, "text": markdown_text, "images": ..., "tables": ...
            logger.info(f"Extracting content from {pdf_path} using pymupdf4llm...")
            pages = pymupdf4llm.to_markdown(pdf_path, page_chunks=True)
            
            for i, page_data in enumerate(pages):
                page_num = page_data.get("page", i + 1)
                text = page_data.get("text", "")
                
                # Merge image OCR text if available for this page
                if page_num in image_text_by_page:
                    image_texts = image_text_by_page[page_num]
                    image_section = "\n\n## Image Text (OCR)\n\n" + "\n\n".join(
                        f"**Image {idx + 1}:**\n{img_text}" 
                        for idx, img_text in enumerate(image_texts)
                    )
                    text = text + image_section
                    logger.info(f"Page {page_num}: Merged {len(image_texts)} image OCR result(s)")
                
                if text.strip():
                    # Clean the text but keep markdown structure
                    cleaned_text = text.strip()
                    
                    metadata = {
                        "source": original_source,
                        "pdf_path": pdf_path,
                        "page": page_num,
                        "type": "content (PyMuPDF + Image OCR)",
                        "doc_type": "pdf",
                        "original_source": original_source,
                        "page_title": f"Page {page_num}: {original_source}",
                        "has_image_ocr": page_num in image_text_by_page
                    }
                    
                    documents.append(Document(
                        page_content=cleaned_text,
                        metadata=metadata
                    ))
            
            logger.info(f"Extracted {len(documents)} pages from {pdf_path} using pymupdf4llm with image OCR")
            
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path} with pymupdf4llm: {str(e)}")
            
        return documents

    def load_pdf_with_pdfplumber(self, pdf_path):
        """
        Extract text and tables from PDF as unified content, with OCR fallback for low-content pages.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            list: List of Document objects with unified content
        """
        documents = []
        pdf_name = os.path.basename(pdf_path)
        try:
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"Found {len(pdf.pages)} pages in {pdf_path}")
                for page_num, page in enumerate(pdf.pages, start=1):
                    doc = self.extract_page_content(page, pdf_path, page_num)
                    if len(doc.page_content.strip()) < 50:  # Threshold for OCR fallback
                        logger.info(f"Low content on page {page_num} of {pdf_path}, switching to OCR")
                        ocr_docs = self.load_pdf_with_ocr(pdf_path)
                        documents.extend(ocr_docs)
                        break  # Skip remaining pages if OCR is triggered
                    elif doc.page_content.strip():
                        documents.append(doc)

            logger.info(f"Extracted {len(documents)} documents from {pdf_path}")
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path}: {str(e)}")
        return documents

    def load_pdf_with_ocr(self, pdf_path):
        """
        Extract text from PDF using OCR.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            list: List of Document objects with OCR text
        """
        documents = []
        pdf_name = os.path.basename(pdf_path)
        original_source = os.path.splitext(pdf_name)[0]
        
        try:
            images = convert_from_path(pdf_path, dpi=300)
            for page_num, image in enumerate(images, start=1):
                text = pytesseract.image_to_string(image)
                if text.strip():
                    cleaned_text = self.preprocess_text(text)
                    if cleaned_text:
                        metadata = {
                            "source": original_source,
                            "pdf_path": pdf_path,
                            "page": page_num,
                            "type": "content (OCR)",
                            "doc_type": "pdf",
                            "original_source": original_source
                        }
                        documents.append(Document(
                            page_content=cleaned_text,
                            metadata=metadata
                        ))
            logger.info(f"Extracted {len(documents)} documents from {pdf_path} with OCR")
        except Exception as e:
            logger.error(f"Error loading PDF {pdf_path} with OCR: {str(e)}")
        return documents

    def check_pdf_integrity(self, pdf_path):
        """
        Check if a PDF file is valid.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            bool: True if PDF is valid, False otherwise
        """
        try:
            if not os.path.exists(pdf_path):
                logger.error(f"PDF file not found: {pdf_path}")
                return False
            file_size = os.path.getsize(pdf_path)
            if file_size == 0:
                logger.error(f"PDF file is empty: {pdf_path}")
                return False
            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)
                logger.info(f"PDF is valid. Found {page_count} pages in {pdf_path}")
                return True
        except Exception as e:
            logger.error(f"Error checking PDF {pdf_path}: {str(e)}", exc_info=True)
            return False

    def generate_markdown_output(self, documents, output_folder="./markdowns/"):
        """
        Generate one Markdown file per PDF from processed documents.
        
        Args:
            documents (list): List of Document objects
            output_folder (str): Directory to save Markdown files
            
        Returns:
            str: Path to the output folder
        """
        os.makedirs(output_folder, exist_ok=True)
        pdf_groups = {}
        
        # Group documents by PDF source
        for doc in documents:
            pdf_name = doc.metadata["source"]
            if pdf_name not in pdf_groups:
                pdf_groups[pdf_name] = []
            pdf_groups[pdf_name].append(doc)
        
        # Generate one Markdown file per PDF
        for pdf_name, docs in pdf_groups.items():
            output_file = os.path.join(output_folder, f"{os.path.splitext(pdf_name)[0]}.md")
            with open(output_file, "w", encoding="utf-8") as f:
                for doc in docs:
                    f.write(f"{doc.metadata['page_title']}\n\n{doc.page_content}\n\n")
            logger.info(f"Generated Markdown file: {output_file}")
        
        return output_folder

    def process_pdfs(self, pdf_folder=None):
        """
        Process all PDFs in the folder and generate Markdown output.
        
        Args:
            pdf_folder (str, optional): Directory containing PDFs. Defaults to self.pdf_folder.
            
        Returns:
            str: Path to the output folder containing Markdown files
        """
        pdf_documents = []
        pdf_folder = pdf_folder or self.pdf_folder

        try:
            pdf_paths = self.get_pdf_paths(pdf_folder)
            for pdf_path in pdf_paths:
                if not self.check_pdf_integrity(pdf_path):
                    logger.error(f"Skipping invalid PDF: {pdf_path}")
                    continue
                # Primary extraction using pymupdf4llm
                pdf_docs = self.load_pdf_with_pymupdf4llm(pdf_path)
                
                # Fallback to pdfplumber if pymupdf4llm failed or returned very little content
                if not pdf_docs or sum(len(d.page_content) for d in pdf_docs) < 100:
                    logger.warning(f"No/low content from {pdf_path} with pymupdf4llm. Falling back to pdfplumber.")
                    pdf_docs = self.load_pdf_with_pdfplumber(pdf_path)
                
                # Final fallback to OCR
                if not pdf_docs:
                    logger.warning(f"No content from {pdf_path} with pdfplumber. Attempting OCR.")
                    pdf_docs = self.load_pdf_with_ocr(pdf_path)
                if not pdf_docs:
                    logger.warning(f"No content from {pdf_path} even with OCR. Skipping.")
                    continue
                pdf_documents.extend(pdf_docs)

            logger.info(f"Total documents extracted: {len(pdf_documents)}")
            markdown_folder = self.generate_markdown_output(pdf_documents)
            return markdown_folder

        except Exception as e:
            logger.error(f"Error during PDF processing: {e}")
            raise

    def extract_file(self, file_path, extract_folder="extracted_files"):
        """
        Extract ZIP/TAR files.
        
        Args:
            file_path (str): Path to the archive file
            extract_folder (str): Directory to extract files to
        """
        os.makedirs(extract_folder, exist_ok=True)
        if file_path.endswith(".zip"):
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_folder)
            logger.info(f"Extracted ZIP to {extract_folder}")
        elif file_path.endswith((".tar", ".tar.gz", ".tgz")):
            with tarfile.open(file_path, "r:*") as tar_ref:
                tar_ref.extractall(extract_folder)
            logger.info(f"Extracted TAR to {extract_folder}")
        else:
            logger.warning("Unsupported file type for extraction.")

    def move_pdf(self, file_path, pdf_folder=None):
        """
        Move PDF file to the PDF folder.
        
        Args:
            file_path (str): Path to the PDF file
            pdf_folder (str, optional): Destination folder. Defaults to self.pdf_folder.
        """
        pdf_folder = pdf_folder or self.pdf_folder
        os.makedirs(pdf_folder, exist_ok=True)
        new_path = os.path.join(pdf_folder, os.path.basename(file_path))
        shutil.move(file_path, new_path)
        logger.info(f"Moved PDF to {pdf_folder}")

# Global instance
document_processor = DocumentProcessor()