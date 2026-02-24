"""
Tests for the data fetcher module
"""
import os
import pytest
from unittest.mock import patch, Mock
from src.preprocessing.data_fetch import DataFetcher

@pytest.fixture
def data_fetcher():
    """Create a data fetcher instance."""
    return DataFetcher()

@pytest.fixture
def mock_requests():
    """Create mock requests."""
    with patch('requests.head') as mock:
        response = Mock()
        response.headers = {
            'Content-Disposition': 'attachment; filename="test.pdf"'
        }
        mock.return_value = response
        yield mock

@pytest.fixture
def mock_gdown_and_mimetypes():
    """Create mock gdown and mimetypes."""
    with patch('gdown.download') as mock_download, \
         patch('mimetypes.guess_type') as mock_guess_type, \
         patch('os.rename') as mock_rename:
        mock_download.return_value = None
        mock_guess_type.return_value = ("application/pdf", None)
        yield mock_download, mock_guess_type, mock_rename

def test_get_filename_from_headers_success(data_fetcher, mock_requests):
    """Test getting filename from headers successfully."""
    filename = data_fetcher.get_filename_from_headers("https://drive.google.com/file/d/123/view")
    assert filename == "test.pdf"
    mock_requests.assert_called_once_with(
        "https://drive.google.com/uc?id=123",
        allow_redirects=True
    )

def test_get_filename_from_headers_no_disposition(data_fetcher):
    """Test getting filename when Content-Disposition header is missing."""
    with patch('requests.head') as mock:
        mock.return_value = Mock(headers={})
        filename = data_fetcher.get_filename_from_headers("https://drive.google.com/file/d/123/view")
        assert filename is None

def test_download_from_drive_with_filename(data_fetcher, mock_requests, mock_gdown_and_mimetypes, tmp_path):
    """Test downloading file from Drive with known filename."""
    mock_download, _, _ = mock_gdown_and_mimetypes
    
    result = data_fetcher.download_from_drive(
        "https://drive.google.com/file/d/123/view",
        output_folder=str(tmp_path)
    )
    
    assert result == os.path.join(str(tmp_path), "test.pdf")
    mock_download.assert_called_once_with(
        "https://drive.google.com/uc?id=123",
        os.path.join(str(tmp_path), "test.pdf"),
        quiet=False
    )

def test_download_from_drive_no_filename(data_fetcher, mock_gdown_and_mimetypes, tmp_path):
    """Test downloading file from Drive without known filename."""
    with patch('requests.head') as mock:
        mock.return_value = Mock(headers={})
        mock_download, mock_guess_type, mock_rename = mock_gdown_and_mimetypes
        
        result = data_fetcher.download_from_drive(
            "https://drive.google.com/file/d/123/view",
            output_folder=str(tmp_path)
        )
        
        expected_path = os.path.join(str(tmp_path), "downloaded_file.pdf")
        assert result == expected_path
        mock_rename.assert_called_once_with(
            os.path.join(str(tmp_path), "downloaded_file"),
            expected_path
        ) 