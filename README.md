# resume-maker-mcp

A local MCP (Model Context Protocol) server that analyzes job descriptions and automatically tailors your LaTeX resume — then pushes it to GitHub where Actions compiles a fresh PDF. Works entirely with Claude Desktop. **Zero cost.**

---

## Architecture

```
Claude Desktop
      ↓  MCP protocol
resume-maker-mcp  (this server)
      ↓  file I/O + git
Local .tex files in /resume
      ↓  git push
GitHub repo
      ↓  GitHub Actions
resume.pdf  (auto-compiled, downloadable)
```

---

## Tools Exposed

| Tool | What it does |
|------|-------------|
| `analyze_jd` | Parses a job description → extracts skills, stack, keywords, seniority, fit score |
| `tailor_resume` | Rewrites a resume section to target the JD (does NOT write to disk) |
| `push_changes` | Writes edits to disk, git commits, pushes → triggers PDF compilation |
| `read_resume` | Reads any section or the full resume.tex |
| `list_sections` | Shows all section files and their status |

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/resume-maker-mcp.git
cd resume-maker-mcp

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Set up GitHub repo

```bash
cd resume-maker-mcp
git init
git remote add origin https://github.com/YOUR_USERNAME/resume-maker-mcp.git
git add .
git commit -m "feat: initial resume-maker-mcp setup"
git push -u origin main
```

### 3. Fill in your resume

Edit these files with your actual information:

- `resume/resume.tex` — header (name, email, LinkedIn, GitHub)
- `resume/sections/education.tex` — education history
- `resume/sections/experience.tex` — your work history
- `resume/sections/skills.tex` — your tech skills
- `resume/sections/projects.tex` — your projects
- `resume/sections/achievements.tex` — awards, certifications, and achievements

The template renders sections in this order: Education, Technical Skills,
Experience, Projects, and Achievements. Each project includes editable `Live`
and `Code` links. Replace the example URLs with your deployment and repository
URLs.

### 4. Configure Claude Desktop

Open your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Add this block (replace paths with your actual absolute paths):

```json
{
  "mcpServers": {
    "resume-maker": {
      "command": "/absolute/path/to/resume-maker-mcp/.venv/bin/python",
      "args": ["-m", "server"],
      "cwd": "/absolute/path/to/resume-maker-mcp",
      "env": {
        "RESUME_DIR": "/absolute/path/to/resume-maker-mcp/resume"
      }
    }
  }
}
```

See `claude_desktop_config.example.json` for platform-specific examples.

**Restart Claude Desktop** after saving the config.

### 5. Verify it works

In Claude Desktop, type:
```
list all resume sections
```
You should see all 5 editable sections listed with their file paths.

---

## Usage — full workflow

### Analyze a job description
```
Analyze this job description and tell me the fit score:

[paste the full JD here]
```

### Tailor a specific section
```
Tailor my skills section for this job description:

[paste JD]
```

### Tailor and push in one shot
```
Analyze this JD, tailor my skills and projects sections, then push the changes to GitHub:

[paste JD]
```

### Check what changed
```
Read my current projects section
```

---

## How the PDF gets compiled

Once you push changes, GitHub Actions automatically:
1. Installs LaTeX (`texlive`) on an Ubuntu runner
2. Runs `pdflatex resume.tex` twice (for proper cross-references)
3. Uploads `resume.pdf` as a downloadable artifact
4. Commits `resume.pdf` back to the repo

**Download your PDF:** Go to your GitHub repo → Actions tab → latest workflow run → Artifacts → `resume-pdf`.

Or directly from the repo root after Actions commits it back.

---

## Customize fit scoring

The default fit score is a placeholder. To make it accurate, open `tools/analyze_jd.py` and update the `score_fit()` function with your own skills list:

```python
MY_SKILLS = {
    "python", "fastapi", "react", "postgresql", "docker", "aws"
    # add your actual skills here
}

def score_fit(tech_stack: dict, seniority: str) -> dict:
    found = {kw for kws in tech_stack.values() for kw in kws}
    matched = found & MY_SKILLS
    score = int(len(matched) / max(len(found), 1) * 100)
    return {"score": score, "matched": list(matched), "missing": list(found - MY_SKILLS)}
```

---

## Project structure

```
resume-maker-mcp/
├── server.py                        ← MCP server entry point
├── tools/
│   ├── analyze_jd.py                ← JD parser & keyword extractor
│   ├── tailor_resume.py             ← section rewriter
│   ├── push_changes.py              ← git commit & push
│   ├── read_resume.py               ← file reader
│   └── list_sections.py             ← section lister
├── resume/
│   ├── resume.tex                   ← main LaTeX document
│   └── sections/
│       ├── education.tex
│       ├── experience.tex
│       ├── skills.tex
│       ├── projects.tex
│       └── achievements.tex
├── .github/
│   └── workflows/
│       └── compile.yml              ← GitHub Actions PDF builder
├── pyproject.toml
├── claude_desktop_config.example.json
└── README.md
```

---

## Tech stack

| Layer | Technology | Cost |
|-------|-----------|------|
| MCP server | Python 3.10+, `mcp` SDK | Free |
| Resume format | LaTeX | Free |
| Version control | Git + GitHub | Free |
| PDF compilation | GitHub Actions | Free (2000 min/mo) |
| AI integration | Claude Desktop | Free tier |

---

## License

MIT
