"""
Tests for tailor_resume tool.
Run with: python -m pytest tests/ -v
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.tailor_resume import tailor_resume, inject_keywords_into_skills

RESUME_DIR = Path(__file__).parent.parent / "resume"

SAMPLE_JD = """
Looking for a Python developer with experience in FastAPI, PostgreSQL,
Docker, and AWS. Must have strong skills in REST API design and CI/CD pipelines.
"""


def test_tailor_skills_returns_dict():
    result = tailor_resume("skills", SAMPLE_JD, RESUME_DIR)
    assert isinstance(result, dict)
    assert "section" in result
    assert "new_content" in result
    assert result["section"] == "skills"


def test_tailor_summary_returns_dict():
    result = tailor_resume("summary", SAMPLE_JD, RESUME_DIR)
    assert isinstance(result, dict)
    assert result["section"] == "summary"


def test_tailor_does_not_write_to_disk():
    """tailor_resume should NEVER write files — only push_changes does."""
    skills_path = RESUME_DIR / "sections" / "skills.tex"
    original = skills_path.read_text()
    tailor_resume("skills", SAMPLE_JD, RESUME_DIR)
    assert skills_path.read_text() == original


def test_inject_keywords_adds_missing_skills():
    original = "\\begin{itemize}\n  \\item Python\n\\end{itemize}"
    tech_stack = {"frameworks": ["fastapi", "django"], "cloud": ["aws"]}
    result = inject_keywords_into_skills(original, tech_stack)
    assert len(result) > len(original)


def test_inject_keywords_skips_existing():
    original = "\\begin{itemize}\n  \\item Python\n  \\item FastAPI\n\\end{itemize}"
    tech_stack = {"frameworks": ["fastapi"]}
    result = inject_keywords_into_skills(original, tech_stack)
    assert result.lower().count("fastapi") == 1
