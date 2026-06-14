import pytest
from app.agents.gap_agent import get_mock_gap_analysis
from app.agents.roadmap_agent import get_mock_roadmap

def test_mock_gap_analysis():
    """
    Validates that set calculations for missing required/preferred skills
    are calculated correctly with accurate matching scores.
    """
    resume_data = {
        "skills": ["Python", "React", "Docker"]
    }
    jd_data = {
        "required_skills": ["Python", "FastAPI", "React"],
        "preferred_skills": ["LangGraph", "Docker"]
    }
    
    result = get_mock_gap_analysis(resume_data, jd_data)
    
    # 2/3 required skills match (Python, React) -> (2/3)*80 + 20 = 73% score
    assert result.match_score == 73
    
    # Missing required: FastAPI; Missing preferred: LangGraph
    assert "FastAPI" in result.missing_skills
    assert "LangGraph" in result.missing_skills
    
    # Matched skills should NOT be in the missing list
    assert "Python" not in result.missing_skills
    assert "Docker" not in result.missing_skills

def test_mock_roadmap():
    """
    Validates that missing skills are correctly partitioned into weeks.
    """
    missing_skills = ["FastAPI", "LangGraph"]
    result = get_mock_roadmap(missing_skills, "AI Software Engineer")
    
    # 2 missing skills should map to 2 weeks
    assert len(result.weeks) == 2
    assert result.weeks[0].week_number == 1
    assert "FastAPI" in result.weeks[0].focus_skills
    assert "LangGraph" in result.weeks[1].focus_skills
    assert len(result.weeks[0].tasks) > 0
