"""
analyze_jd.py
Parses a job description and extracts structured information:
skills, tech stack, keywords, seniority, and fit scoring.
"""

import re
from collections import Counter


TECH_KEYWORDS = {
    "languages": [
        "python", "javascript", "typescript", "java", "go", "golang", "rust",
        "c++", "c#", "ruby", "swift", "kotlin", "php", "scala", "r",
    ],
    "frameworks": [
        "react", "next.js", "nextjs", "vue", "angular", "django", "fastapi",
        "flask", "express", "node.js", "nodejs", "spring", "rails", "laravel",
        "svelte", "nuxt",
    ],
    "cloud": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
        "terraform", "ansible", "ci/cd", "jenkins", "github actions",
    ],
    "data": [
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "kafka", "spark", "hadoop", "airflow", "dbt", "snowflake", "bigquery",
    ],
    "ml_ai": [
        "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
        "llm", "nlp", "computer vision", "mlops", "hugging face",
    ],
    "tools": [
        "git", "linux", "rest api", "graphql", "grpc", "microservices",
        "agile", "scrum", "jira", "figma",
    ],
}

SENIORITY_SIGNALS = {
    "manager": ["manager", "director", "vp ", "head of", "engineering manager"],
    "senior": ["senior", "5+ years", "6+ years", "7+ years", "lead", "principal", "staff"],
    "mid": ["mid level", "mid-level", "2-5 years", "3 years", "4 years"],
    "junior": ["junior", "entry level", "entry-level", "0-2 years", "1 year", "fresh graduate", "new grad"],
}

SOFT_SKILLS = [
    "communication", "collaboration", "teamwork", "problem solving", "leadership",
    "mentoring", "ownership", "initiative", "analytical", "detail-oriented",
    "self-starter", "cross-functional",
]


def extract_tech_stack(text: str) -> dict:
    text_lower = text.lower()
    found = {}
    for category, keywords in TECH_KEYWORDS.items():
        matches = [kw for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
        if matches:
            found[category] = matches
    return found


def extract_seniority(text: str) -> str:
    text_lower = text.lower()
    for level, signals in SENIORITY_SIGNALS.items():
        if any(s in text_lower for s in signals):
            return level
    return "mid"


def extract_keywords(text: str) -> list[str]:
    """Pull high-frequency meaningful words from JD."""
    text_lower = text.lower()
    stop_words = {
        "the", "and", "for", "with", "you", "our", "will", "are", "that",
        "this", "have", "your", "we", "be", "a", "an", "to", "of", "in",
        "is", "on", "at", "by", "or", "as", "us", "it", "its", "not",
        "from", "team", "work", "experience", "role", "join", "about",
        "looking", "help", "build", "strong", "ability", "skills", "years",
    }
    words = re.findall(r'\b[a-z][a-z0-9\+\#\.]{2,}\b', text_lower)
    freq = Counter(w for w in words if w not in stop_words)
    return [word for word, _ in freq.most_common(20)]


def extract_responsibilities(text: str) -> list[str]:
    """Extract bullet-style responsibilities."""
    lines = text.split('\n')
    bullets = []
    for line in lines:
        line = line.strip()
        if line.startswith(('-', '•', '*', '·')) and len(line) > 10:
            clean = re.sub(r'^[-•*·]\s*', '', line).strip()
            if clean:
                bullets.append(clean)
    return bullets[:8]


def extract_requirements(text: str) -> list[str]:
    """Look for 'requirements' or 'qualifications' section."""
    pattern = re.compile(
        r'(?:requirements?|qualifications?|what you.ll need|must have)[:\s]*\n(.*?)(?:\n\n|\Z)',
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text)
    if match:
        block = match.group(1)
        lines = [re.sub(r'^[-•*·]\s*', '', l.strip()) for l in block.split('\n') if l.strip()]
        return [l for l in lines if len(l) > 10][:8]
    return []


def score_fit(tech_stack: dict, seniority: str) -> dict:
    """Placeholder scoring — user fills in their own skills for real scoring."""
    total_found = sum(len(v) for v in tech_stack.values())
    score = min(100, total_found * 8)
    return {
        "score": score,
        "note": (
            "Update tools/analyze_jd.py > score_fit() with your own skills "
            "for accurate fit scoring."
        ),
    }


def analyze_jd(job_description: str) -> dict:
    """
    Main entry point. Takes raw JD text, returns structured analysis.
    """
    tech_stack = extract_tech_stack(job_description)
    seniority = extract_seniority(job_description)
    keywords = extract_keywords(job_description)
    responsibilities = extract_responsibilities(job_description)
    requirements = extract_requirements(job_description)
    fit = score_fit(tech_stack, seniority)

    soft_skills_found = [
        s for s in SOFT_SKILLS
        if s in job_description.lower()
    ]

    return {
        "seniority_level": seniority,
        "tech_stack": tech_stack,
        "top_keywords": keywords,
        "responsibilities": responsibilities,
        "requirements": requirements,
        "soft_skills": soft_skills_found,
        "fit_score": fit,
        "summary": (
            f"Found {sum(len(v) for v in tech_stack.values())} technical keywords "
            f"across {len(tech_stack)} categories. "
            f"Seniority: {seniority}. "
            f"Fit score: {fit['score']}/100."
        ),
    }
