"""
tailor_resume.py
Reads a LaTeX resume section and rewrites it to target a specific job description.
Uses keyword injection and section-aware rewriting strategies.
"""

from pathlib import Path
from tools.analyze_jd import analyze_jd


SECTION_FILES = {
    "education": "sections/education.tex",
    "experience": "sections/experience.tex",
    "skills": "sections/skills.tex",
    "projects": "sections/projects.tex",
    "achievements": "sections/achievements.tex",
}


def read_section(section: str, resume_dir: Path) -> str:
    """Read a LaTeX section file."""
    filename = SECTION_FILES.get(section)
    if not filename:
        raise ValueError(f"Unknown section '{section}'. Choose from: {list(SECTION_FILES.keys())}")
    path = resume_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Section file not found: {path}")
    return path.read_text(encoding="utf-8")


def inject_keywords_into_skills(content: str, tech_stack: dict) -> str:
    """
    Add missing tech keywords to the skills section.
    Finds the last \\item line and appends new skills after it.
    """
    all_found = [kw for kws in tech_stack.values() for kw in kws]
    if not all_found:
        return content

    content_lower = content.lower()
    new_skills = [kw for kw in all_found if kw.lower() not in content_lower]

    if not new_skills:
        return content

    new_items = "\n".join(f"  \\item {skill.title()}" for skill in new_skills[:6])
    insert_comment = f"\n  % Auto-added by resume-maker-mcp\n{new_items}"

    last_item = content.rfind("\\item")
    if last_item == -1:
        return content + insert_comment

    end_of_line = content.find("\n", last_item)
    return content[:end_of_line] + insert_comment + content[end_of_line:]


def tailor_experience(content: str, jd_analysis: dict) -> str:
    """
    Adds keyword-rich bullet points to the most recent job entry.
    Inserts after the last existing \\resumeItem or \\item.
    """
    keywords = jd_analysis.get("top_keywords", [])[:4]
    responsibilities = jd_analysis.get("responsibilities", [])
    tech = jd_analysis.get("tech_stack", {})
    tech_flat = [kw for kws in tech.values() for kw in kws][:4]

    if not tech_flat and not keywords:
        return content

    new_bullet = (
        f"Delivered key features leveraging {', '.join(tech_flat[:3])} "
        f"to address {', '.join(keywords[:2])} requirements, "
        f"improving system reliability and team velocity."
    )

    last_item = content.rfind("\\resumeItem")
    if last_item == -1:
        last_item = content.rfind("\\item")
    if last_item == -1:
        return content + f"\n\\resumeItem{{{new_bullet}}}\n"

    end_of_line = content.find("\n", last_item)
    insert = f"\n        \\resumeItem{{{new_bullet}}}"
    return content[:end_of_line] + insert + content[end_of_line:]


def tailor_projects(content: str, jd_analysis: dict) -> str:
    """
    Updates project descriptions to include JD-relevant tech keywords.
    """
    tech = jd_analysis.get("tech_stack", {})
    tech_flat = [kw for kws in tech.values() for kw in kws][:5]

    if not tech_flat:
        return content

    tech_str = ", ".join(t.title() for t in tech_flat)
    comment = f"\n% Tech stack from JD: {tech_str}\n"

    if "% Tech stack from JD" in content:
        return re.sub(r'% Tech stack from JD:.*\n', comment.lstrip(), content)

    return comment + content


def tailor_resume(
    section: str,
    job_description: str,
    resume_dir: Path,
    jd_analysis: dict | None = None,
) -> dict:
    """
    Main entry point. Reads a section, tailors it, returns the new content.
    Does NOT write to disk — call push_changes() after reviewing.
    """
    if jd_analysis is None:
        jd_analysis = analyze_jd(job_description)

    original_content = read_section(section, resume_dir)

    if section == "skills":
        new_content = inject_keywords_into_skills(
            original_content, jd_analysis.get("tech_stack", {})
        )
    elif section == "experience":
        new_content = tailor_experience(original_content, jd_analysis)
    elif section == "projects":
        new_content = tailor_projects(original_content, jd_analysis)
    else:
        new_content = original_content

    changed = new_content != original_content

    return {
        "section": section,
        "changed": changed,
        "original_length": len(original_content),
        "new_length": len(new_content),
        "new_content": new_content,
        "jd_analysis_used": jd_analysis.get("summary", ""),
        "message": (
            f"Section '{section}' tailored successfully. "
            "Call push_changes() to write and commit."
            if changed
            else f"No changes needed for section '{section}'."
        ),
    }
