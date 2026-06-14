import logging
from app.utils.gemini_client import get_gemini_client
from app.agents.schemas import RoadmapSchema, RoadmapWeek

logger = logging.getLogger(__name__)

def get_mock_roadmap(missing_skills: list, job_title: str) -> RoadmapSchema:
    """
    Programmatic mock generator for roadmaps. Distributes missing skills
    into weekly milestones (up to 4 weeks) with realistic tasks and resources.
    """
    skills_to_use = missing_skills if missing_skills else ["LangGraph", "ChromaDB"]
    
    weeks = []
    # Maximum 4 weeks
    num_weeks = min(4, len(skills_to_use))
    
    for i in range(num_weeks):
        skill = skills_to_use[i]
        theme = f"Mastering {skill} and Local Integrations"
        focus_skills = [skill]
        
        # Bind any leftovers to the last week
        if i == num_weeks - 1 and len(skills_to_use) > num_weeks:
            focus_skills.extend(skills_to_use[num_weeks:])
            theme = f"Advanced {skill} & Complete Stack Integration"
            
        tasks = [
            f"Read the official getting started documentation for {skill}.",
            f"Build a clean local demonstration project utilizing {skill} primitives.",
            f"Write comprehensive test assertions to validate CRUD operations on {skill} inputs."
        ]
        
        resources = [
            f"Official {skill} Documentation: https://docs.example.com/{skill.lower()}",
            f"Awesome {skill} Learning Pathway: https://github.com/topics/{skill.lower()}",
            f"YouTube: Introduction to {skill} for Engineers"
        ]
        
        weeks.append(
            RoadmapWeek(
                week_number=i + 1,
                theme=theme,
                focus_skills=focus_skills,
                tasks=tasks,
                resources=resources
            )
        )
        
    return RoadmapSchema(weeks=weeks)

def generate_learning_roadmap(missing_skills: list, job_title: str) -> RoadmapSchema:
    """
    Creates a customized weekly syllabus to bridge competency gaps using Gemini 2.5 Flash.
    Falls back to a dynamic mock template if client configurations are missing.
    """
    try:
        client = get_gemini_client()
        
        prompt = f"""
        You are a senior technical curriculum designer and career mentor.
        Design a structured, week-by-week study plan (strictly between 1 and 4 weeks) to help a student 
        acquire the missing skills required for the role: '{job_title}'.
        
        Missing Competencies:
        {missing_skills}
        
        Provide highly concrete coding assignments and high-quality resource recommendations for each week 
        to ensure they build a solid practical understanding.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": RoadmapSchema,
                "temperature": 0.2
            }
        )
        
        return RoadmapSchema.model_validate_json(response.text)
        
    except ValueError as ve:
        logger.warning(f"Using mock roadmap fallback: {ve}")
        return get_mock_roadmap(missing_skills, job_title)
    except Exception as e:
        logger.exception("Error in Roadmap Agent execution")
        return get_mock_roadmap(missing_skills, job_title)
