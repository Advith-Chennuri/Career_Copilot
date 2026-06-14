import logging
from app.utils.gemini_client import get_gemini_client
from app.agents.schemas import ResumeExtractionSchema, WorkExperience, Project, Education

logger = logging.getLogger(__name__)

def get_mock_resume_extraction(text: str) -> ResumeExtractionSchema:
    """
    Keyword-based mock extractor to serve as a graceful fallback
    if the GEMINI_API_KEY is not set.
    """
    skills = []
    lower_text = text.lower()
    
    # Detect mock skills
    for keyword, skill_name in [
        ("python", "Python"),
        ("react", "React"),
        ("fastapi", "FastAPI"),
        ("docker", "Docker"),
        ("git", "Git"),
        ("aws", "AWS"),
        ("sql", "SQL"),
        ("javascript", "JavaScript"),
        ("typescript", "TypeScript")
    ]:
        if keyword in lower_text:
            skills.append(skill_name)
            
    if not skills:
        skills = ["Python", "FastAPI", "React", "SQL"]

    # Try to parse name from first line
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    candidate_name = lines[0] if lines else "Jane Doe"
    if len(candidate_name) > 30:
        candidate_name = "Jane Doe"
        
    return ResumeExtractionSchema(
        skills=skills,
        experience=[
            WorkExperience(
                company="Tech Corp (Mock Fallback)",
                role="Software Engineer",
                duration="2023 - Present",
                highlights=[
                    "Developed backend API services using Python and FastAPI.",
                    "Collaborated on design system variables and premium UI templates.",
                    "Maintained transactional database states and migration tasks."
                ]
            )
        ],
        projects=[
            Project(
                title="AI Career Mentor App",
                tech_stack=["React", "FastAPI", "SQLite"],
                description="Designed an automated resume analysis and learning roadmap helper."
            )
        ],
        education=[
            Education(
                institution="State University",
                degree="Bachelor of Science",
                major="Computer Science"
            )
        ]
    )

def extract_resume_details(resume_text: str) -> ResumeExtractionSchema:
    """
    Extracts structured attributes from raw resume text using Gemini 2.5 Flash.
    Falls back to a keyword mock parser if no API Key is active.
    """
    try:
        client = get_gemini_client()
        
        prompt = f"""
        You are an expert technical recruiter and resume parser.
        Analyze the raw resume text provided below and extract the structural details.
        Be extremely precise, preserving details as they are written in the resume.
        
        Resume Text:
        {resume_text}
        """
        
        # Call Google GenAI SDK with JSON schema enforcement
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ResumeExtractionSchema,
                "temperature": 0.1
            }
        )
        
        # Validate extracted json against our pydantic schema
        return ResumeExtractionSchema.model_validate_json(response.text)
        
    except ValueError as ve:
        logger.warning(f"Using mock resume parser fallback: {ve}")
        return get_mock_resume_extraction(resume_text)
    except Exception as e:
        logger.exception("Error in Resume Agent execution")
        # Fail over to mock to keep application running
        return get_mock_resume_extraction(resume_text)
