"""
Tests for analyze_jd tool.
Run with: python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.analyze_jd import analyze_jd, extract_tech_stack, extract_seniority


SAMPLE_JD = """
We are looking for a Senior Software Engineer to join our backend team.

Requirements:
- 5+ years of experience with Python and Django
- Strong knowledge of PostgreSQL and Redis
- Experience with AWS (EC2, S3, Lambda)
- Familiarity with Docker and Kubernetes
- Experience with React.js is a plus

Responsibilities:
- Design and build scalable REST APIs
- Collaborate with cross-functional teams
- Mentor junior developers
- Participate in code reviews
"""


def test_analyze_jd_returns_dict():
    result = analyze_jd(SAMPLE_JD)
    assert isinstance(result, dict)


def test_analyze_jd_has_required_keys():
    result = analyze_jd(SAMPLE_JD)
    assert "seniority_level" in result
    assert "tech_stack" in result
    assert "top_keywords" in result
    assert "fit_score" in result
    assert "summary" in result


def test_seniority_detection():
    seniority = extract_seniority(SAMPLE_JD)
    assert seniority == "senior"


def test_tech_stack_extraction():
    tech = extract_tech_stack(SAMPLE_JD)
    assert "languages" in tech
    assert "python" in tech["languages"]
    assert "data" in tech
    assert "postgresql" in tech["data"]


def test_cloud_detection():
    tech = extract_tech_stack(SAMPLE_JD)
    assert "cloud" in tech
    assert "aws" in tech["cloud"]


def test_keywords_are_list():
    result = analyze_jd(SAMPLE_JD)
    assert isinstance(result["top_keywords"], list)
    assert len(result["top_keywords"]) > 0


def test_fit_score_is_number():
    result = analyze_jd(SAMPLE_JD)
    assert isinstance(result["fit_score"]["score"], (int, float))
    assert 0 <= result["fit_score"]["score"] <= 100
