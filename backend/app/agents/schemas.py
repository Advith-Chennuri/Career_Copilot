from typing import List, Optional
from pydantic import BaseModel, Field

# --- Resume Agent Schemas ---

class WorkExperience(BaseModel):
    company: str = Field(description="Name of the company or organization")
    role: str = Field(description="Job title or role held")
    duration: str = Field(description="Timeframe of employment (e.g., '2023 - Present' or 'Jan 2022 - Dec 2022')")
    highlights: List[str] = Field(description="Bullet points of key achievements and duties")

class Project(BaseModel):
    title: str = Field(description="Name of the project")
    tech_stack: List[str] = Field(description="Key tools, languages, and frameworks used in the project")
    description: str = Field(description="Brief description of what was built and achieved")

class Education(BaseModel):
    institution: str = Field(description="Name of the university, college, or school")
    degree: str = Field(description="Type of degree earned (e.g., 'Bachelor of Science', 'Master of Science')")
    major: str = Field(description="Field of study or major (e.g., 'Computer Science', 'Data Science')")

class ResumeExtractionSchema(BaseModel):
    skills: List[str] = Field(description="List of technical and soft skills parsed from the resume")
    experience: List[WorkExperience] = Field(description="List of professional work experiences")
    projects: List[Project] = Field(description="List of relevant engineering or software projects")
    education: List[Education] = Field(description="Academic background details")


# --- Job Description Agent Schemas ---

class JDExtractionSchema(BaseModel):
    job_title: str = Field(description="Extracted job title (e.g. 'Software Engineer')")
    company: Optional[str] = Field(description="Name of the hiring company, if listed")
    required_skills: List[str] = Field(description="Skills marked as mandatory, required, or essential")
    preferred_skills: List[str] = Field(description="Skills marked as optional, preferred, nice-to-have, or bonus")
    experience_required: Optional[str] = Field(description="Years or description of experience required (e.g. '3+ years')")


# --- Gap Analysis Agent Schemas ---

class GapAnalysisSchema(BaseModel):
    match_score: int = Field(description="Compatibility score between 0 and 100 representing how well the resume matches the JD criteria.")
    missing_skills: List[str] = Field(description="List of required or preferred skills from the JD that are not explicitly demonstrated or listed in the resume.")
    recommendations: str = Field(description="Actionable bullet points suggesting how the candidate can improve their resume or highlight key projects to better fit the role.")


# --- Roadmap Agent Schemas ---

class RoadmapWeek(BaseModel):
    week_number: int = Field(description="Number of the week (e.g. 1, 2, 3, 4)")
    theme: str = Field(description="The primary topic or goal of this week (e.g., 'Mastering LangGraph State Management')")
    focus_skills: List[str] = Field(description="The specific missing skills targeted in this week")
    tasks: List[str] = Field(description="Specific, actionable hands-on coding tasks or assignments the candidate should perform")
    resources: List[str] = Field(description="Curated high-quality learning resources, documentations, or study articles")

class RoadmapSchema(BaseModel):
    weeks: List[RoadmapWeek] = Field(description="List of weekly structured milestones building up candidate skills")


