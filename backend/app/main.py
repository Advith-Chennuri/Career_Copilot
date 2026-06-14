import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.services.pdf_service import extract_text_from_pdf
from app.utils.config import settings
from app.models.database import engine, Base, get_db
from app.models.models import User, Resume, JobDescription, Analysis
from app.agents.resume_agent import extract_resume_details
from app.agents.jd_agent import extract_jd_details
from app.agents.gap_agent import analyze_skills_gap
from app.agents.roadmap_agent import generate_learning_roadmap
from app.rag.ingestion import ingest_document
from app.rag.retrieval import query_knowledge_assistant
from pydantic import BaseModel

# Bind SQLAlchemy metadata and create tables automatically on startup
import app.models.models
Base.metadata.create_all(bind=engine)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend services for AI Career Copilot including database caching and multi-agent extraction.",
    version="0.2.0"
)

# Configure CORS so React (Vite) can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific domains for production security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_or_create_test_user(db: Session) -> User:
    """
    Helper function to ensure a default test student exists in the database
    to support uploads without a full authentication system in Phase 2.
    """
    test_email = "test.student@example.com"
    user = db.query(User).filter_by(email=test_email).first()
    if not user:
        user = User(name="Test Student", email=test_email)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created default test user: {user.email}")
    return user

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "message": "AI Career Copilot API is running and healthy."
    }

@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts a PDF resume, saves it to the database under the default user,
    runs the Resume Agent to extract structured parameters, and returns both raw & structured details.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are accepted for resumes."
        )
    try:
        content = await file.read()
        extracted_text = extract_text_from_pdf(content)
        
        # Ensure default test user exists
        user = get_or_create_test_user(db)
        
        # Save raw extraction to database
        db_resume = Resume(
            user_id=user.id,
            filename=file.filename,
            resume_text=extracted_text
        )
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        # Run Resume Agent to extract structured attributes
        structured_data = extract_resume_details(extracted_text)
        
        return {
            "id": db_resume.id,
            "filename": file.filename,
            "text": extracted_text,
            "structured": structured_data,
            "message": "Resume uploaded, saved to database, and structured details parsed successfully."
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        logger.exception("Error processing resume upload")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while parsing the resume: {str(e)}"
        )

@app.post("/api/upload-jd")
async def upload_jd(
    file: UploadFile = None,
    description_text: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Accepts either a PDF file or direct text form parameter for a job description,
    runs the JD Agent to extract structured requirements, and caches it in the database.
    """
    if not file and not description_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either a job description PDF file or direct text content."
        )
    
    extracted_text = ""
    filename = None
    
    if file:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PDF files are accepted."
            )
        try:
            filename = file.filename
            content = await file.read()
            extracted_text = extract_text_from_pdf(content)
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(ve)
            )
        except Exception as e:
            logger.exception("Error processing JD upload")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred while parsing the JD PDF: {str(e)}"
            )
    else:
        extracted_text = description_text.strip()
        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided description text cannot be empty."
            )
            
    try:
        # Run JD Agent to extract structured requirements
        structured_data = extract_jd_details(extracted_text)
        
        # Ensure default test user exists
        user = get_or_create_test_user(db)
        
        # Save raw extraction to database
        db_jd = JobDescription(
            user_id=user.id,
            title=structured_data.job_title,
            description_text=extracted_text
        )
        db.add(db_jd)
        db.commit()
        db.refresh(db_jd)
        
        return {
            "id": db_jd.id,
            "filename": filename,
            "text": extracted_text,
            "structured": structured_data,
            "message": "Job Description uploaded, saved to database, and structured details parsed successfully."
        }
    except Exception as e:
        logger.exception("Error saving Job Description to database")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while saving the JD: {str(e)}"
        )

class AnalyzeRequest(BaseModel):
    resume_id: int
    jd_id: int

@app.post("/api/analyze")
async def analyze_fit(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Retrieves the raw cached texts, executes resume and JD parsers,
    runs the Gap Agent and the Roadmap Agent, and saves/returns the combined analysis.
    """
    db_resume = db.query(Resume).filter_by(id=request.resume_id).first()
    db_jd = db.query(JobDescription).filter_by(id=request.jd_id).first()
    
    if not db_resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {request.resume_id} not found."
        )
    if not db_jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job Description with ID {request.jd_id} not found."
        )
        
    try:
        # Run specialized agents to parse details
        resume_structured = extract_resume_details(db_resume.resume_text)
        jd_structured = extract_jd_details(db_jd.description_text)
        
        # Run Gap Analysis Agent
        gap_analysis = analyze_skills_gap(
            resume_structured.model_dump(), 
            jd_structured.model_dump()
        )
        
        # Run Roadmap Agent
        roadmap_data = generate_learning_roadmap(
            gap_analysis.missing_skills, 
            jd_structured.job_title
        )
        
        # Cache results in the analysis table
        db_analysis = Analysis(
            user_id=db_resume.user_id,
            resume_id=db_resume.id,
            jd_id=db_jd.id,
            match_score=gap_analysis.match_score,
            missing_skills=gap_analysis.missing_skills,
            recommendations=gap_analysis.recommendations,
            roadmap=roadmap_data.model_dump(),
        )
        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)
        
        return {
            "id": db_analysis.id,
            "match_score": db_analysis.match_score,
            "missing_skills": db_analysis.missing_skills,
            "recommendations": db_analysis.recommendations,
            "roadmap": db_analysis.roadmap,
            "message": "Analysis and learning roadmap generated and cached successfully."
        }
    except Exception as e:
        logger.exception("Error during fit analysis orchestration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during multi-agent analysis: {str(e)}"
        )

class QueryRequest(BaseModel):
    query: str

@app.post("/api/upload-knowledge")
async def upload_knowledge(file: UploadFile = File(...)):
    """
    Accepts a PDF containing student notes/study resources, parses it,
    chunks it, embeds it, and indexes it into ChromaDB.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are supported for notes."
        )
    try:
        content = await file.read()
        extracted_text = extract_text_from_pdf(content)
        
        # Ingest into ChromaDB
        chunks_count = ingest_document(file.filename, extracted_text)
        
        return {
            "filename": file.filename,
            "chunks_ingested": chunks_count,
            "message": f"Successfully parsed '{file.filename}' and ingested {chunks_count} chunks into ChromaDB."
        }
    except Exception as e:
        logger.exception("Error during knowledge ingestion")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to ingest knowledge document: {str(e)}"
        )

@app.post("/api/query-knowledge")
async def query_knowledge(request: QueryRequest):
    """
    Retrieves semantic contexts from ChromaDB and returns a grounded answer from Gemini.
    """
    try:
        result = query_knowledge_assistant(request.query)
        return result
    except Exception as e:
        logger.exception("Error querying knowledge assistant")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error querying knowledge assistant: {str(e)}"
        )

@app.get("/api/knowledge-documents")
def list_knowledge_documents():
    """
    Retrieves the list of unique indexed filenames and their chunk counts from ChromaDB.
    """
    try:
        from app.rag.chroma_client import get_kb_collection
        collection = get_kb_collection()
        
        # Get all metadatas in the collection
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", []) if results else []
        
        # Count chunks per document
        doc_counts = {}
        for meta in metadatas:
            if meta and "source" in meta:
                src = meta["source"]
                doc_counts[src] = doc_counts.get(src, 0) + 1
                
        # Format as list of dicts
        docs_list = [
            {"name": name, "chunks": count}
            for name, count in doc_counts.items()
        ]
        return docs_list
    except Exception as e:
        logger.exception("Error listing knowledge documents")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve indexed documents: {str(e)}"
        )

