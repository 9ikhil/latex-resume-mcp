"""
tailor_resume.py
Reads a LaTeX resume section and carefully rewrites it to target a job description.
STRICT RULES:
- Only enhance existing content with relevant keywords from the JD.
- Preserve all original facts, numbers, and structure.
"""

import re
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
    filename = SECTION_FILES.get(section)
    if not filename:
        raise ValueError(f"Unknown section '{section}'. Choose from: {list(SECTION_FILES.keys())}")
    path = resume_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Section file not found: {path}")
    return path.read_text(encoding="utf-8")


def inject_keywords_into_skills(content: str, tech_stack: dict) -> str:
    """
    Safely add missing keywords into existing category lines.
    Never creates new \item lines that break the structure.
    add the keywords which are in the job description , 
    you can make assumption that this skill is used in this experience but dont make more lines out of it because it can break the structure of the resume
    """
    if not tech_stack:
        return content

    # Flatten and normalize JD tech
    jd_keywords = []
    for kws in tech_stack.values():
        jd_keywords.extend(kws)
    jd_keywords = list(dict.fromkeys(jd_keywords))  # preserve order, unique

    content_lower = content.lower()

    # Only keep keywords that are truly missing
    missing = [kw for kw in jd_keywords if kw.lower() not in content_lower]
    if not missing:
        return content

    lines = content.splitlines()
    new_lines = []

    for line in lines:
        # Look for category lines like: \item \textbf{Languages:} Python, ...
        match = re.search(r'(\\item\s*\\textbf\{[^}]+:\})\s*(.*)', line, re.IGNORECASE)
        if match:
            prefix = match.group(1)
            existing = match.group(2).rstrip()

            # Decide which missing keywords belong to this category
            to_add = []
            for kw in missing[:]:
                # Simple heuristic: put language-like keywords in Languages, etc.
                # We just append a few missing ones that make sense
                if any(x in kw.lower() for x in ["python", "java", "c++", "typescript", "javascript", "go", "rust", "sql"]):
                    if "language" in prefix.lower():
                        to_add.append(kw)
                        missing.remove(kw)
                elif any(x in kw.lower() for x in ["react", "next", "django", "fastapi", "express", "node", "vue", "angular"]):
                    if "framework" in prefix.lower() or "web" in prefix.lower():
                        to_add.append(kw)
                        missing.remove(kw)
                elif any(x in kw.lower() for x in ["aws", "docker", "kubernetes", "terraform", "ci/cd", "linux"]):
                    if "cloud" in prefix.lower() or "devops" in prefix.lower():
                        to_add.append(kw)
                        missing.remove(kw)
                elif any(x in kw.lower() for x in ["postgres", "mongo", "redis", "mysql", "sql"]):
                    if "database" in prefix.lower():
                        to_add.append(kw)
                        missing.remove(kw)
                elif any(x in kw.lower() for x in ["langchain", "langgraph", "llm", "rag", "nlp", "pytorch", "tensorflow"]):
                    if "ai" in prefix.lower() or "nlp" in prefix.lower() or "ml" in prefix.lower():
                        to_add.append(kw)
                        missing.remove(kw)

            if to_add:
                # Clean title casing for display
                pretty = [k.title() if k.islower() else k for k in to_add]
                if existing and not existing.endswith(","):
                    existing += ","
                new_line = f"{prefix} {existing} {', '.join(pretty)}".strip()
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def tailor_experience(content: str, jd_analysis: dict) -> str:
    """
    Very conservative: only inject 1-2 highly relevant keywords into
    existing bullets of the MOST RECENT job. Never invent new bullets.
    """
    tech = jd_analysis.get("tech_stack", {})
    tech_flat = [kw for kws in tech.values() for kw in kws]
    keywords = jd_analysis.get("top_keywords", [])

    relevant = list(dict.fromkeys(tech_flat + keywords))[:6]
    if not relevant:
        return content

    # Find the first (most recent) experience block and its bullets
    # We only touch the first 1-2 resumeItem lines
    lines = content.splitlines()
    new_lines = []
    bullets_touched = 0
    max_bullets_to_touch = 2

    for line in lines:
        if bullets_touched >= max_bullets_to_touch:
            new_lines.append(line)
            continue

        # Match a resumeItem line
        m = re.search(r'(\\resumeItem\{)(.+)(\})', line)
        if m and "\\resumeItem" in line:
            prefix, body, suffix = m.group(1), m.group(2), m.group(3)
            body_lower = body.lower()

            # Only add a keyword if it is not already present
            added = False
            for kw in relevant:
                if kw.lower() not in body_lower and len(kw) > 2:
                    # Insert naturally near the end of the sentence
                    if body.rstrip().endswith("."):
                        body = body.rstrip()[:-1] + f" using {kw}" + "."
                    else:
                        body = body.rstrip() + f" using {kw}"
                    added = True
                    bullets_touched += 1
                    break

            if added:
                new_lines.append(f"{prefix}{body}{suffix}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def tailor_projects(content: str, jd_analysis: dict) -> str:
    """
    Lightly enhance project descriptions with 1 relevant tech keyword
    if it is missing. Never invent projects or change structure.
    """
    tech = jd_analysis.get("tech_stack", {})
    tech_flat = [kw for kws in tech.values() for kw in kws][:5]
    if not tech_flat:
        return content

    lines = content.splitlines()
    new_lines = []
    enhanced = 0
    max_enhance = 2

    for line in lines:
        if enhanced >= max_enhance:
            new_lines.append(line)
            continue

        m = re.search(r'(\\resumeItem\{)(.+)(\})', line)
        if m:
            prefix, body, suffix = m.group(1), m.group(2), m.group(3)
            body_lower = body.lower()

            for kw in tech_flat:
                if kw.lower() not in body_lower:
                    if body.rstrip().endswith("."):
                        body = body.rstrip()[:-1] + f" with {kw}" + "."
                    else:
                        body = body.rstrip() + f" with {kw}"
                    enhanced += 1
                    break

            new_lines.append(f"{prefix}{body}{suffix}")
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def tailor_resume(
    section: str,
    job_description: str,
    resume_dir: Path,
    jd_analysis: dict | None = None,
) -> dict:
    """
    Main entry point.
    Returns new content but does NOT write to disk.
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
        # education & achievements are left untouched (too personal / factual)
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
            f"Section '{section}' carefully tailored (no invented content). "
            "Call push_changes() after reviewing."
            if changed
            else f"No changes needed for section '{section}'."
        ),
    }