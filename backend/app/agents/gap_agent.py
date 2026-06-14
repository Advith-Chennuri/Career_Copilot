import logging
from app.utils.gemini_client import get_gemini_client
from app.agents.schemas import GapAnalysisSchema

logger = logging.getLogger(__name__)

def get_mock_gap_analysis(resume_data: dict, jd_data: dict) -> GapAnalysisSchema:
    """
    Performs a programmatic set-comparison between candidate skills and JD requirements.
    Provides a fallback if no Gemini API Key is configured.
    """
    resume_skills = [s.lower().strip() for s in resume_data.get("skills", [])]
    jd_req = jd_data.get("required_skills", [])
    jd_pref = jd_data.get("preferred_skills", [])
    
    missing_skills = []
    matched_count = 0
    
    # Check required skills
    for skill in jd_req:
        if skill.lower().strip() not in resume_skills:
            missing_skills.append(skill)
        else:
            matched_count += 1
            
    # Check preferred skills
    for skill in jd_pref:
        if skill.lower().strip() not in resume_skills:
            missing_skills.append(skill)
            
    # Compute score mathematically
    total_req = len(jd_req)
    if total_req > 0:
        match_score = int((matched_count / total_req) * 80) + 20  # offset 20 to 100
    else:
        match_score = 100
        
    recommendations = ""
    if missing_skills:
        recs = [
            f"- Detail your hands-on experience or project achievements utilizing '{skill}' directly under work descriptions.",
            f"- Consider building a brief side project or proof-of-concept incorporating '{skill}' to close this gap."
        ]
        recommendations = "Short-term Actionable Tweaks:\n" + "\n".join(recs)
    else:
        recommendations = "Outstanding match profile! Your resume highlights demonstrate key expertise in all required and preferred dimensions."

    return GapAnalysisSchema(
        match_score=min(100, max(0, match_score)),
        missing_skills=missing_skills,
        recommendations=recommendations
    )

def analyze_skills_gap(resume_data: dict, jd_data: dict) -> GapAnalysisSchema:
    """
    Compares candidate profile details against job requirements using Gemini.
    Falls back to mathematical parsing if the AI client is unavailable.
    """
    try:
        client = get_gemini_client()
        
        prompt = f"""
        You are a hiring manager and system design recruiter.
        Analyze the match between the candidate's parsed resume profile and the job description requirements.
        
        Structured Candidate Resume Profile:
        {resume_data}
        
        Structured Job Description Requirements:
        {jd_data}
        
        Assess the match score (0-100) based on role alignment. Identify missing skills that are not clearly demonstrated 
        in the candidate's skills, experience, or projects. Provide specific, constructive resume update recommendations.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": GapAnalysisSchema,
                "temperature": 0.2
            }
        )
        
        return GapAnalysisSchema.model_validate_json(response.text)
        
    except ValueError as ve:
        logger.warning(f"Using mock gap analysis fallback: {ve}")
        return get_mock_gap_analysis(resume_data, jd_data)
    except Exception as e:
        logger.exception("Error in Gap Agent execution")
        return get_mock_gap_analysis(resume_data, jd_data)
