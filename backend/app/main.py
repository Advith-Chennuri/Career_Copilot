import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.services.pdf_service import extract_text_from_pdf
from app.utils.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend services for AI Career Copilot including multi-agent and RAG capabilities.",
    version="0.1.0"
)

# Configure CORS so React (Vite) can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to specific domains for production security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "message": "AI Career Copilot API is running and healthy."
    }

@app.post("/api/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """
    Accepts a PDF resume file and returns the parsed text.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are accepted for resumes."
        )
    try:
        content = await file.read()
        extracted_text = extract_text_from_pdf(content)
        return {
            "filename": file.filename,
            "text": extracted_text,
            "message": "Resume uploaded and text extracted successfully."
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
    description_text: str = Form(None)
):
    """
    Accepts either a PDF file or direct text form parameter for a job description.
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
            
    return {
        "filename": filename,
        "text": extracted_text,
        "message": "Job Description uploaded and text extracted successfully."
    }
