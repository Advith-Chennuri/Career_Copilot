import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, get_db
from app.models.models import User, Resume, JobDescription

# Use a temporary SQLite file to share database context across HTTP client connections
TEST_DB_FILE = "./test_temp.db"
engine = create_engine(f"sqlite:///{TEST_DB_FILE}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply the dependency override to the app instance
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    # Create all tables on the temporary SQLite file
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup tables
    Base.metadata.drop_all(bind=engine)
    # Delete the test database file
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_upload_resume_invalid_format():
    response = client.post(
        "/api/upload-resume",
        files={"file": ("resume.txt", b"my resume content", "text/plain")}
    )
    assert response.status_code == 400
    assert "Only PDF files are accepted" in response.json()["detail"]

def test_upload_resume_success():
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
        assert "parsed successfully" in response.json()["message"]

def test_upload_jd_text_success():
    response = client.post(
        "/api/upload-jd",
        data={"description_text": "We are looking for a Python developer."}
    )
    assert response.status_code == 200
    assert response.json()["text"] == "We are looking for a Python developer."
    assert response.json()["filename"] is None

def test_upload_jd_pdf_success():
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

def test_analyze_fit_success():
    # 1. Populate DB with required resume and JD entries
    db = TestingSessionLocal()
    
    # Create default user
    user = User(name="Test User", email="test.analysis@example.com")
    db.add(user)
    db.commit()
    
    # Create Resume entry
    resume = Resume(user_id=user.id, filename="my_resume.pdf", resume_text="Skills: Python, FastAPI")
    db.add(resume)
    
    # Create JD entry
    jd = JobDescription(user_id=user.id, title="Python Dev", description_text="Requirements: Python, React, LangGraph")
    db.add(jd)
    db.commit()
    
    # 2. Trigger unified analysis API
    payload = {
        "resume_id": resume.id,
        "jd_id": jd.id
    }
    
    response = client.post("/api/analyze", json=payload)
    db.close()
    
    assert response.status_code == 200
    assert "match_score" in response.json()
    assert "missing_skills" in response.json()
    assert "roadmap" in response.json()
    
    # "FastAPI" and "Python" are in resume; "React" and "LangGraph" should be missing
    assert "React" in response.json()["missing_skills"]
    assert "LangGraph" in response.json()["missing_skills"]
    assert len(response.json()["roadmap"]["weeks"]) > 0
