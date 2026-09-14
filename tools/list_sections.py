"""
list_sections.py
Lists all resume sections and their current file status.
"""

from pathlib import Path


SECTION_FILES = {
    "experience": "sections/experience.tex",
    "skills": "sections/skills.tex",
    "projects": "sections/projects.tex",
    "summary": "sections/summary.tex",
}


def list_sections(resume_dir: Path) -> dict:
    sections = []
    for name, relative_path in SECTION_FILES.items():
        path = resume_dir / relative_path
        sections.append({
            "section": name,
            "file": relative_path,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        })

    return {
        "resume_dir": str(resume_dir),
        "sections": sections,
        "all_present": all(s["exists"] for s in sections),
    }
