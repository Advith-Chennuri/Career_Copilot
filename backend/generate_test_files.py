import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_pdf(filename, text_lines):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 72
    c.setFont("Helvetica", 10)
    for line in text_lines:
        c.drawString(72, y, line)
        y -= 18
    c.save()

if __name__ == "__main__":
    os.makedirs("../assets", exist_ok=True)
    
    # Generate mock resume
    generate_pdf(
        "../assets/sample_resume.pdf",
        [
            "Jane Doe - Software Engineer",
            "Email: jane.doe@example.com | GitHub: github.com/janedoe",
            "",
            "Experience:",
            "- Software Engineer at Tech Corp (2023 - Present)",
            "  Built stateful multi-agent systems and real-time data pipelines using Python and React.",
            "- Frontend Developer Intern at Web Studio (2022 - 2023)",
            "  Designed interactive web apps using Vite, React, and CSS variables.",
            "",
            "Skills:",
            "Python, React, Vite, FastAPI, PostgreSQL, Git, Docker"
        ]
    )
    print("Generated assets/sample_resume.pdf")

    # Generate mock job description
    generate_pdf(
        "../assets/sample_jd.pdf",
        [
            "Job Description: AI Software Engineer",
            "Company: Future AI Solutions",
            "",
            "Role Overview:",
            "We are looking for an AI Software Engineer to build agentic pipelines.",
            "",
            "Required Skills:",
            "- Professional experience with Python and FastAPI.",
            "- Experience building single-page applications with React.",
            "- Familiarity with multi-agent orchestration frameworks (e.g., LangGraph).",
            "- Understanding of vector databases and semantic search.",
            "",
            "Preferred Skills:",
            "- Experience with Docker, Vite, and vanilla CSS."
        ]
    )
    print("Generated assets/sample_jd.pdf")
