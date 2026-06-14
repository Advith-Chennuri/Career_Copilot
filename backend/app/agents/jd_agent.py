import logging
from app.utils.gemini_client import get_gemini_client
from app.agents.schemas import JDExtractionSchema

logger = logging.getLogger(__name__)

def get_mock_jd_extraction(text: str) -> JDExtractionSchema:
    """
    Keyword-based mock extractor to serve as a graceful fallback
    if the GEMINI_API_KEY is not set.
    """
    required = []
    preferred = []
    lower_text = text.lower()
    
    # Detect mock required skills
    for keyword, skill_name in [
        ("python", "Python"),
        ("fastapi", "FastAPI"),
        ("react", "React"),
        ("langgraph", "LangGraph"),
        ("chromadb", "ChromaDB"),
        ("mysql", "MySQL"),
        ("docker", "Docker"),
        ("git", "Git")
    ]:
        if keyword in lower_text:
            required.append(skill_name)
            
    # Add preferred skills
    for keyword, skill_name in [
        ("vanilla css", "Vanilla CSS"),
        ("typescript", "TypeScript"),
        ("aws", "AWS"),
        ("mcp", "MCP")
    ]:
        if keyword in lower_text:
            preferred.append(skill_name)

    if not required:
        required = ["Python", "FastAPI", "React"]
    if not preferred:
        preferred = ["LangGraph", "ChromaDB", "TypeScript"]
        
    # Attempt to extract job title from first line
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    job_title = lines[0] if lines else "AI Software Engineer"
    if "job description" in job_title.lower() and len(lines) > 1:
        job_title = lines[1]
    if len(job_title) > 50:
        job_title = "AI Software Engineer"

    return JDExtractionSchema(
        job_title=job_title,
        company="Future AI Solutions (Mock Fallback)",
        required_skills=required,
        preferred_skills=preferred,
        experience_required="2+ years"
    )

def extract_jd_details(jd_text: str) -> JDExtractionSchema:
    """
    Extracts structured job parameters from raw job descriptions using Gemini 2.5 Flash.
    Falls back to a keyword mock parser if no API Key is active.
    """
    try:
        client = get_gemini_client()
        
        prompt = f"""
        You are a hiring manager and system design interviewer.
        Analyze the raw job description text provided below and extract the structural requirements.
        Be extremely precise, capturing required skills vs preferred skills.
        
        Job Description:
        {jd_text}
        """
        
        # Call Google GenAI SDK with JSON schema enforcement
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": JDExtractionSchema,
                "temperature": 0.1
            }
        )
        
        # Validate extracted json against our pydantic schema
        return JDExtractionSchema.model_validate_json(response.text)
        
    except ValueError as ve:
        logger.warning(f"Using mock JD parser fallback: {ve}")
        return get_mock_jd_extraction(jd_text)
    except Exception as e:
        logger.exception("Error in JD Agent execution")
        # Fail over to mock to keep application running
        return get_mock_jd_extraction(jd_text)
