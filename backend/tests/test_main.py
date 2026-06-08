import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app

client = TestClient(app)

def test_read_root():
    """
    Test root health check route.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "running" in response.json()["message"]

def test_upload_resume_invalid_format():
    """
    Test resume endpoint rejects non-PDF files.
    """
    response = client.post(
        "/api/upload-resume",
        files={"file": ("resume.txt", b"my resume content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are accepted" in response.json()["detail"]

def test_upload_resume_success():
    """
    Test successful resume upload and text extraction.
    """
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Skill: Python"
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    
    with patch("pypdf.PdfReader", return_value=mock_reader):
        response = client.post(
            "/api/upload-resume",
            files={"file": ("resume.pdf", b"pdf content", "application/pdf")}
        )
        assert response.status_code == 200
        assert response.json()["filename"] == "resume.pdf"
        assert response.json()["text"] == "Skill: Python"
        assert "extracted successfully" in response.json()["message"]

def test_upload_jd_text_success():
    """
    Test successful job description uploading via text form.
    """
    response = client.post(
        "/api/upload-jd",
        data={"description_text": "We are looking for a Python developer."}
    )
    assert response.status_code == 200
    assert response.json()["text"] == "We are looking for a Python developer."
    assert response.json()["filename"] is None

def test_upload_jd_pdf_success():
    """
    Test successful job description uploading via PDF file.
    """
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Role: React Developer"
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]
    
    with patch("pypdf.PdfReader", return_value=mock_reader):
        response = client.post(
            "/api/upload-jd",
            files={"file": ("jd.pdf", b"pdf content", "application/pdf")}
        )
        assert response.status_code == 200
        assert response.json()["filename"] == "jd.pdf"
        assert response.json()["text"] == "Role: React Developer"
