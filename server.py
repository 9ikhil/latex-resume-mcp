"""
resume-maker-mcp
A local MCP server that analyzes job descriptions and tailors
your LaTeX resume, then auto-pushes to GitHub for PDF compilation.
Compatible with mcp 2.x (MCPServer API).
"""

import asyncio
import json
import os
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from tools.analyze_jd import analyze_jd
from tools.tailor_resume import tailor_resume
from tools.push_changes import push_changes
from tools.read_resume import read_resume
from tools.list_sections import list_sections

RESUME_DIR = Path(os.environ.get("RESUME_DIR", Path(__file__).parent / "resume"))

app = MCPServer("resume-maker-mcp")


@app.tool()
def tool_analyze_jd(job_description: str) -> str:
    """
    Analyze a job description and extract key requirements.
    Returns structured data: required skills, tech stack, keywords,
    seniority level, and a fit score against your resume.
    """
    try:
        result = analyze_jd(job_description)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@app.tool()
def tool_tailor_resume(section: str, job_description: str) -> str:
    """
    Rewrite a specific resume section to better match a job description.
    Section must be one of: experience, skills, projects, summary.
    Does NOT write to disk — call push_changes after reviewing.
    """
    try:
        result = tailor_resume(
            section=section,
            job_description=job_description,
            resume_dir=RESUME_DIR,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@app.tool()
def tool_push_changes(edits: str, commit_message: str = "chore: tailor resume via MCP") -> str:
    """
    Write edited LaTeX content to disk, commit, and push to GitHub.
    Pass edits as a JSON string: [{"section": "skills", "content": "...latex..."}]
    GitHub Actions will automatically compile the PDF after push.
    """
    try:
        edits_list = json.loads(edits) if isinstance(edits, str) else edits
        result = push_changes(
            edits=edits_list,
            resume_dir=RESUME_DIR,
            commit_message=commit_message,
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@app.tool()
def tool_read_resume(section: str = "full") -> str:
    """
    Read the current content of any resume section or the full resume.tex.
    Section options: experience, skills, projects, summary, full.
    """
    try:
        result = read_resume(section=section, resume_dir=RESUME_DIR)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@app.tool()
def tool_list_sections() -> str:
    """
    List all available resume sections and their file paths and status.
    """
    try:
        result = list_sections(resume_dir=RESUME_DIR)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


if __name__ == "__main__":
    asyncio.run(app.run_stdio_async())
