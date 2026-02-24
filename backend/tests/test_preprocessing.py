"""
Unit tests for the preprocessing module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
from pathlib import Path
from langchain_core.documents import Document

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")

from src.preprocessing.preprocessing import (
    get_pdf_paths,
    format_table,
    load_pdf_with_pdfplumber,
    load_pdf_with_ocr,
    get_filename_from_headers,
    download_from_drive,
    extract_file,
    move_pdf,
    download_pdf,
    DocumentProcessor
)

@pytest.fixture
def document_processor():
    """Create a document processor instance."""
    return DocumentProcessor()

@pytest.fixture
def sample_pdf_dir():
    """Create a temporary directory with sample PDF files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some dummy PDF files
        Path(tmpdir, "test1.pdf").touch()
        Path(tmpdir, "test2.pdf").touch()
        Path(tmpdir, "not_a_pdf.txt").touch()
        yield tmpdir

@pytest.fixture
def mock_requests():
    """Create mock requests."""
    with patch('requests.head') as mock:
        response = MagicMock()
        response.headers = {
            'Content-Disposition': 'attachment; filename="test.pdf"'
        }
        mock.return_value = response
        yield mock

def test_get_pdf_paths_success(document_processor, sample_pdf_dir):
    """Test getting PDF paths successfully."""
    pdf_paths = document_processor.get_pdf_paths(sample_pdf_dir)
    assert len(pdf_paths) == 2
    assert all(path.endswith('.pdf') for path in pdf_paths)

def test_get_pdf_paths_no_directory(document_processor):
    """Test getting PDF paths with non-existent directory."""
    with pytest.raises(FileNotFoundError):
        document_processor.get_pdf_paths("nonexistent_directory")

def test_get_pdf_paths_empty_directory(document_processor):
    """Test getting PDF paths from empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            document_processor.get_pdf_paths(tmpdir)

def test_format_table(document_processor):
    """Test table formatting."""
    table = [
        ["Header1", "Header2"],
        ["Value1", "Value2"]
    ]
    formatted = document_processor.format_table(table)
    assert "Header1" in formatted
    assert "Header2" in formatted
    assert "Value1" in formatted
    assert "Value2" in formatted
    assert "-+-" in formatted  # Check for separator

@pytest.fixture
def mock_pdfplumber():
    """Create a mock pdfplumber."""
    with patch('pdfplumber.open') as mock:
        page = MagicMock()
        page.extract_text.return_value = "Sample text\n\nMore text"
        page.extract_tables.return_value = [
            [["Header1", "Header2"], ["Value1", "Value2"]]
        ]
        pdf = MagicMock()
        pdf.pages = [page]
        mock.return_value.__enter__.return_value = pdf
        yield mock

def test_load_pdf_with_pdfplumber(document_processor, mock_pdfplumber):
    """Test loading PDF with pdfplumber."""
    docs = document_processor.load_pdf_with_pdfplumber("dummy.pdf")
    assert len(docs) == 3  # 2 text chunks + 1 table
    assert all(isinstance(doc, Document) for doc in docs)
    assert any(doc.metadata["type"] == "table" for doc in docs)
    assert any(doc.metadata["type"] == "text" for doc in docs)

@pytest.fixture
def mock_ocr():
    """Create mock OCR components."""
    with patch('pdf2image.convert_from_path') as mock_convert, \
         patch('pytesseract.image_to_string') as mock_tesseract:
        mock_convert.return_value = [MagicMock()]
        mock_tesseract.return_value = "OCR extracted text"
        yield mock_convert, mock_tesseract

def test_load_pdf_with_ocr(document_processor, mock_ocr):
    """Test loading PDF with OCR."""
    docs = document_processor.load_pdf_with_ocr("dummy.pdf")
    assert len(docs) == 1
    assert isinstance(docs[0], Document)
    assert docs[0].metadata["type"] == "text (OCR)"
    assert "OCR extracted text" in docs[0].page_content

def test_load_pdf_with_ocr_failure(document_processor, mock_ocr):
    """Test OCR failure handling."""
    mock_convert, _ = mock_ocr
    mock_convert.side_effect = Exception("PDF conversion failed")
    docs = document_processor.load_pdf_with_ocr("dummy.pdf")
    assert len(docs) == 0

def test_get_filename_from_headers(document_processor, mock_requests):
    """Test getting filename from headers."""
    filename = document_processor.get_filename_from_headers("https://drive.google.com/file/d/123/view")
    assert filename == "test.pdf"

@pytest.fixture
def mock_gdown_and_mimetypes():
    """Create mock gdown and mimetypes."""
    with patch('gdown.download') as mock_download, \
         patch('mimetypes.guess_type') as mock_guess_type, \
         patch('os.rename') as mock_rename:
        mock_download.return_value = None
        mock_guess_type.return_value = ("application/pdf", None)
        yield mock_download, mock_guess_type, mock_rename

def test_download_from_drive(document_processor, mock_gdown_and_mimetypes, mock_requests):
    """Test downloading from Google Drive."""
    result = document_processor.download_from_drive("https://drive.google.com/file/d/123/view")
    assert result.endswith("test.pdf")

def test_extract_file_zip(document_processor, tmp_path):
    """Test extracting ZIP file."""
    test_zip = tmp_path / "test.zip"
    with patch('zipfile.ZipFile') as mock_zip:
        document_processor.extract_file(str(test_zip))
        mock_zip.assert_called_once()

def test_extract_file_tar(document_processor, tmp_path):
    """Test extracting TAR file."""
    test_tar = tmp_path / "test.tar.gz"
    with patch('tarfile.open') as mock_tar:
        document_processor.extract_file(str(test_tar))
        mock_tar.assert_called_once()

def test_move_pdf(document_processor, tmp_path):
    """Test moving PDF file."""
    source = tmp_path / "test.pdf"
    source.touch()
    with patch('shutil.move') as mock_move:
        document_processor.move_pdf(str(source))
        mock_move.assert_called_once()

def test_download_pdf_with_pdf(document_processor):
    """Test downloading PDF file."""
    with patch.object(document_processor, 'download_from_drive') as mock_download, \
         patch.object(document_processor, 'move_pdf') as mock_move:
        mock_download.return_value = "test.pdf"
        document_processor.download_pdf("https://drive.google.com/file/d/123/view")
        mock_move.assert_called_once_with("test.pdf")

def test_download_pdf_with_zip(document_processor):
    """Test downloading ZIP file."""
    with patch.object(document_processor, 'download_from_drive') as mock_download, \
         patch.object(document_processor, 'extract_file') as mock_extract:
        mock_download.return_value = "test.zip"
        document_processor.download_pdf("https://drive.google.com/file/d/123/view")
        mock_extract.assert_called_once_with("test.zip")

# Integration test (commented out as it requires actual PDF files)
"""
def test_integration_pdf_processing(tmp_path):
    # Create a test PDF file
    pdf_path = tmp_path / "test.pdf"
    # ... create actual PDF content ...
    
    # Test the full processing pipeline
    docs = load_pdf_with_pdfplumber(str(pdf_path))
    assert len(docs) > 0
    
    # Test OCR fallback
    docs_ocr = load_pdf_with_ocr(str(pdf_path))
    assert len(docs_ocr) > 0
"""
