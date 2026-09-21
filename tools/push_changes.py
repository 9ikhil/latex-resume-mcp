"""
push_changes.py
Writes tailored LaTeX content to disk, commits, and pushes to GitHub on dedicated branches.
Automatically handles pulling remote PDF commits to prevent conflicts.
"""

import subprocess
import os
import re
from pathlib import Path
from datetime import datetime

SECTION_FILES = {
    "education": "sections/education.tex",
    "experience": "sections/experience.tex",
    "skills": "sections/skills.tex",
    "projects": "sections/projects.tex",
    "achievements": "sections/achievements.tex",
}

def run_git(args: list[str], cwd: Path) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()

def check_git_repo(resume_dir: Path) -> bool:
    code, _, _ = run_git(["rev-parse", "--is-inside-work-tree"], resume_dir)
    return code == 0

def write_section(section: str, content: str, resume_dir: Path) -> Path:
    filename = SECTION_FILES.get(section)
    if not filename:
        raise ValueError(f"Unknown section: {section}")
    path = resume_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path

def push_changes(
    edits: list[dict],
    resume_dir: Path,
    commit_message: str = "chore: tailor resume via MCP",
    branch_name: str = "main",
) -> dict:
    if not edits:
        return {"success": False, "error": "No edits provided."}

    repo_root = resume_dir.parent if (resume_dir.parent / ".git").exists() else resume_dir

    if not check_git_repo(repo_root):
        return {"success": False, "error": "No git repo found."}

    # 1. Automatic Sync: Stash any lingering changes, checkout main, and pull latest PDF
    run_git(["stash"], repo_root)
    run_git(["checkout", "main"], repo_root)
    code, _, err = run_git(["pull", "--rebase", "origin", "main"], repo_root)
    if code != 0:
        return {"success": False, "error": f"Failed to sync with GitHub: {err}"}

    # 2. Branching Strategy: Create/checkout the job-specific branch
    safe_branch = re.sub(r'[^a-zA-Z0-9-]', '-', branch_name).lower().strip('-')
    if safe_branch and safe_branch != "main":
        code, _, _ = run_git(["checkout", safe_branch], repo_root)
        if code != 0:
            run_git(["checkout", "-b", safe_branch], repo_root)
    
    # 3. Write Edits
    written_files = []
    errors = []
    for edit in edits:
        section = edit.get("section")
        content = edit.get("content")
        if not section or content is None:
            continue
        try:
            path = write_section(section, content, resume_dir)
            written_files.append(str(path.relative_to(repo_root)))
        except Exception as e:
            errors.append(f"Failed to write {section}: {e}")

    if errors:
        return {"success": False, "errors": errors}

    # 4. Commit and Push
    run_git(["add"] + written_files, repo_root)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = f"{commit_message} [{timestamp}]"
    code, stdout, err = run_git(["commit", "-m", full_message], repo_root)
    
    if code != 0 and "nothing to commit" not in err.lower() and "nothing to commit" not in stdout.lower():
        return {"success": False, "error": f"git commit failed: {err}"}

    # Force push with upstream tracking to handle new branches automatically
    code, stdout, err = run_git(["push", "-u", "origin", safe_branch], repo_root)
    if code != 0:
        return {"success": False, "error": f"git push failed: {err}"}

    code, commit_hash, _ = run_git(["rev-parse", "--short", "HEAD"], repo_root)

    # 5. Return to main immediately to keep local directory pristine
    run_git(["checkout", "main"], repo_root)

    return {
        "success": True,
        "branch": safe_branch,
        "commit": commit_hash,
        "message": "Resume tailored and pushed to dedicated branch. Check GitHub Actions for your PDF."
    }