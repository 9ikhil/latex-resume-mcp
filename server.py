"""
resume-maker-mcp
A local MCP server that analyzes job descriptions and tailors
your LaTeX resume, then auto-pushes to GitHub for PDF compilation.
"""

import asyncio
import json
import os
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from tools.analyze_jd import analyze_jd
from tools.tailor_resume import tailor_resume
from tools.push_changes import push_changes
from tools.read_resume import read_resume
from tools.list_sections import list_sections

RESUME_DIR = Path(os.environ.get("RESUME_DIR", Path(__file__).parent / "resume"))

app = Server("resume-maker-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="analyze_jd",
            description=(
                "Analyze a job description and extract key requirements. "
                "Returns structured data: required skills, tech stack, keywords, "
                "seniority level, and a fit score against your resume."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_description": {
                        "type": "string",
                        "description": "The full job description text to analyze.",
                    },
                },
                "required": ["job_description"],
            },
        ),
        Tool(
            name="tailor_resume",
            description=(
                "Rewrite a specific resume section to better match a job description. "
                "Pass the section name and either raw JD text or the output from analyze_jd."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "enum": ["experience", "skills", "projects", "summary"],
                        "description": "Which resume section to rewrite.",
                    },
                    "job_description": {
                        "type": "string",
                        "description": "The job description text to tailor the section for.",
                    },
                    "jd_analysis": {
                        "type": "object",
                        "description": "Optional: structured output from analyze_jd to reuse.",
                    },
                },
                "required": ["section", "job_description"],
            },
        ),
        Tool(
            name="push_changes",
            description=(
                "Write edited LaTeX content to disk, commit, and push to GitHub. "
                "GitHub Actions will automatically compile the PDF."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "edits": {
                        "type": "array",
                        "description": "List of section edits to apply.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "section": {"type": "string"},
                                "content": {"type": "string"},
                            },
                            "required": ["section", "content"],
                        },
                    },
                    "commit_message": {
                        "type": "string",
                        "description": "Git commit message. Defaults to 'chore: tailor resume via MCP'.",
                    },
                },
                "required": ["edits"],
            },
        ),
        Tool(
            name="read_resume",
            description="Read the current content of any resume section or the full resume.tex.",
            inputSchema={
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "description": "Section name (experience/skills/projects/summary) or 'full' for main file.",
                        "default": "full",
                    },
                },
            },
        ),
        Tool(
            name="list_sections",
            description="List all available resume sections and their file paths.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "analyze_jd":
            result = analyze_jd(arguments["job_description"])
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "tailor_resume":
            result = tailor_resume(
                section=arguments["section"],
                job_description=arguments["job_description"],
                resume_dir=RESUME_DIR,
                jd_analysis=arguments.get("jd_analysis"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "push_changes":
            result = push_changes(
                edits=arguments["edits"],
                resume_dir=RESUME_DIR,
                commit_message=arguments.get("commit_message", "chore: tailor resume via MCP"),
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "read_resume":
            result = read_resume(
                section=arguments.get("section", "full"),
                resume_dir=RESUME_DIR,
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "list_sections":
            result = list_sections(resume_dir=RESUME_DIR)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
