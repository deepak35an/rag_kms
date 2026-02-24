"""Tests for markdown source attribution functionality."""

import pytest
from unittest.mock import Mock
from src.preprocessing.markdown_processor import MarkdownProcessor
from langchain_core.documents import Document

@pytest.fixture
def markdown_processor():
    """Create a markdown processor instance."""
    return MarkdownProcessor()

def test_extract_source_from_header():
    """Test extracting source information from markdown headers."""
    markdown_text = """# Source: test_document.pdf
This is some content.
## Page 5
More content here."""
    
    processor = MarkdownProcessor()
    docs = processor.process_markdown(markdown_text)
    
    assert len(docs) == 1
    assert docs[0].metadata["source"] == "test_document.pdf"
    assert docs[0].metadata["page"] == 5

def test_extract_source_with_multiple_sections():
    """Test source extraction with multiple markdown sections."""
    markdown_text = """
# Source: doc1.pdf
Content from first doc
# Source: doc2.pdf
Content from second doc
"""
    
    processor = MarkdownProcessor()
    docs = processor.process_markdown(markdown_text)
    
    assert len(docs) == 2
    assert docs[0].metadata["source"] == "doc1.pdf"
    assert docs[1].metadata["source"] == "doc2.pdf"

def test_extract_source_with_missing_header():
    """Test handling of markdown without source headers."""
    markdown_text = "Just some content without headers"
    
    processor = MarkdownProcessor()
    docs = processor.process_markdown(markdown_text)
    
    assert len(docs) == 1
    assert "source" not in docs[0].metadata

def test_extract_source_with_invalid_format():
    """Test handling of invalid source header format."""
    markdown_text = "# Not a valid source header\nContent"
    
    processor = MarkdownProcessor()
    docs = processor.process_markdown(markdown_text)
    
    assert len(docs) == 1
    assert "source" not in docs[0].metadata

def test_extract_source_with_page_numbers():
    """Test extraction of page numbers from headers."""
    markdown_text = """
# Source: report.pdf
## Page 1
First page content
## Page 2
Second page content
"""
    
    processor = MarkdownProcessor()
    docs = processor.process_markdown(markdown_text)
    
    assert len(docs) == 2
    assert all(doc.metadata["source"] == "report.pdf" for doc in docs)
    assert docs[0].metadata["page"] == 1
    assert docs[1].metadata["page"] == 2