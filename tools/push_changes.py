"""
push_changes.py
Writes tailored LaTeX content to disk, commits, and pushes to GitHub.
GitHub Actions picks it up and compiles the PDF automatically.
"""

import subprocess
import os
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
    """Run a git command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_git_repo(resume_dir: Path) -> bool:
    """Check if the resume directory is inside a git repo."""
    code, _, _ = run_git(["rev-parse", "--is-inside-work-tree"], resume_dir)
    return code == 0


def write_section(section: str, content: str, resume_dir: Path) -> Path:
    """Write content to the correct section file."""
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
) -> dict:
    """
    Write all edits to disk, git add, commit, push.
    Each edit is {"section": str, "content": str}.
    """
    if not edits:
        return {"success": False, "error": "No edits provided."}

    repo_root = resume_dir.parent if (resume_dir.parent / ".git").exists() else resume_dir

    if not check_git_repo(repo_root):
        return {
            "success": False,
            "error": (
                f"No git repo found at {repo_root}. "
                "Run 'git init && git remote add origin <your-github-url>' first."
            ),
        }

    written_files = []
    errors = []

    for edit in edits:
        section = edit.get("section")
        content = edit.get("content")
        if not section or content is None:
            errors.append(f"Invalid edit entry: {edit}")
            continue
        try:
            path = write_section(section, content, resume_dir)
            written_files.append(str(path.relative_to(repo_root)))
        except Exception as e:
            errors.append(f"Failed to write {section}: {e}")

    if errors:
        return {"success": False, "errors": errors}

    code, _, err = run_git(["add"] + written_files, repo_root)
    if code != 0:
        return {"success": False, "error": f"git add failed: {err}"}

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = f"{commit_message} [{timestamp}]"

    code, stdout, err = run_git(["commit", "-m", full_message], repo_root)
    if code != 0:
        if "nothing to commit" in err or "nothing to commit" in stdout:
            return {"success": True, "message": "Nothing to commit — files unchanged.", "pushed": False}
        return {"success": False, "error": f"git commit failed: {err}"}

    code, stdout, err = run_git(["push"], repo_root)
    if code != 0:
        return {
            "success": False,
            "error": (
                f"git push failed: {err}\n"
                "Make sure you've set the remote: git remote add origin <url>"
            ),
            "committed": True,
            "pushed": False,
        }

    code, commit_hash, _ = run_git(["rev-parse", "--short", "HEAD"], repo_root)

    return {
        "success": True,
        "pushed": True,
        "commit": commit_hash,
        "message": full_message,
        "files_changed": written_files,
        "next_step": (
            "GitHub Actions is now compiling your PDF. "
            "Check the Actions tab in your GitHub repo. "
            "The PDF will appear under Releases or Artifacts in ~1 minute."
        ),
    }
