import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base
from app.models.models import User, Resume, JobDescription, Analysis

@pytest.fixture(name="db_session")
def fixture_db_session():
    """
    Creates a temporary in-memory database and yields a session
    for clean transactional unit testing.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()

def test_user_creation(db_session):
    # Add User
    user = User(name="Jane Doe", email="jane@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.name == "Jane Doe"
    assert user.email == "jane@example.com"

def test_resume_cascade_delete(db_session):
    # Add User
    user = User(name="Developer One", email="dev@example.com")
    db_session.add(user)
    db_session.commit()
    
    # Add Resume
    resume = Resume(
        user_id=user.id,
        filename="resume.pdf",
        resume_text="Experienced engineer skills: python, FastAPI"
    )
    db_session.add(resume)
    db_session.commit()

    # Query relations
    assert len(user.resumes) == 1
    assert user.resumes[0].filename == "resume.pdf"

    # Delete user and ensure resume is deleted automatically (CASCADE)
    db_session.delete(user)
    db_session.commit()

    resumes_count = db_session.query(Resume).count()
    assert resumes_count == 0
