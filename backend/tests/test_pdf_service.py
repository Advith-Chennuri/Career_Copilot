import pytest
from unittest.mock import MagicMock, patch
from app.services.pdf_service import extract_text_from_pdf

def test_extract_text_from_pdf_success():
    """
    Test extraction works when the PDF contains extractable text.
    """
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Python Developer\nReact Experience\n"
    
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    
    with patch("pypdf.PdfReader", return_value=mock_reader):
        result = extract_text_from_pdf(b"dummy pdf content")
        assert "Python Developer" in result
        assert "React Experience" in result

def test_extract_text_from_pdf_empty():
    """
    Test extraction raises a ValueError if no text can be extracted.
    """
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    
    with patch("pypdf.PdfReader", return_value=mock_reader):
        with pytest.raises(ValueError) as exc_info:
            extract_text_from_pdf(b"dummy pdf content")
        assert "No text could be extracted" in str(exc_info.value)
