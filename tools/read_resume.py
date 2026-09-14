"""
read_resume.py
Reads the current content of any resume section or the full resume.tex.
"""

from pathlib import Path


SECTION_FILES = {
    "experience": "sections/experience.tex",
    "skills": "sections/skills.tex",
    "projects": "sections/projects.tex",
    "summary": "sections/summary.tex",
    "full": "resume.tex",
}


def read_resume(section: str = "full", resume_dir: Path = None) -> dict:
    filename = SECTION_FILES.get(section)
    if not filename:
        return {
            "error": f"Unknown section '{section}'. Choose from: {list(SECTION_FILES.keys())}"
        }

    path = resume_dir / filename
    if not path.exists():
        return {"error": f"File not found: {path}"}

    content = path.read_text(encoding="utf-8")
    return {
        "section": section,
        "file": str(path),
        "content": content,
        "lines": len(content.splitlines()),
        "chars": len(content),
    }
