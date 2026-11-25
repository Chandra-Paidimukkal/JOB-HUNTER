"""
Tests for the Groq AI service layer.
All external Groq API calls are mocked.
"""
import pytest
from unittest.mock import patch, MagicMock


SAMPLE_CANDIDATE = {
    "name": "John Smith",
    "current_title": "Senior Software Engineer",
    "total_experience_years": 5,
    "technical_skills": ["Python", "FastAPI", "PostgreSQL", "React"],
    "soft_skills": ["Leadership", "Communication"],
    "professional_summary": "Experienced engineer...",
    "experience": [{"company": "Acme", "title": "Senior Engineer", "is_current": True}],
}

SAMPLE_JOB = {
    "title": "Staff Software Engineer",
    "company": "TechCo",
    "location": "Remote",
    "description": "Looking for experienced Python engineer...",
    "employment_type": "Full-time",
}


class TestGroqClient:
    def test_groq_client_raises_without_api_key(self):
        from app.services.ai.groq_client import get_groq_client
        from app.core.config import settings

        original = settings.GROQ_API_KEY
        settings.GROQ_API_KEY = ""
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            get_groq_client()
        settings.GROQ_API_KEY = original

    def test_parse_json_with_markdown_wrapper(self):
        from app.services.ai.groq_client import _parse_json_response
        raw = "```json\n{\"score\": 85, \"category\": \"strong\"}\n```"
        result = _parse_json_response(raw)
        assert result["score"] == 85
        assert result["category"] == "strong"

    def test_parse_json_plain(self):
        from app.services.ai.groq_client import _parse_json_response
        result = _parse_json_response('{"key": "value", "num": 42}')
        assert result["num"] == 42

    def test_parse_json_embedded_in_text(self):
        from app.services.ai.groq_client import _parse_json_response
        raw = 'Here is the result: {"score": 90} end of response'
        result = _parse_json_response(raw)
        assert result["score"] == 90

    def test_parse_json_invalid_raises(self):
        from app.services.ai.groq_client import _parse_json_response
        with pytest.raises(ValueError):
            _parse_json_response("completely invalid no json here at all ever")


class TestResumeAnalysis:
    def test_analyze_resume_structure(self, mock_groq_resume):
        from app.services.ai.groq_client import analyze_resume
        result = analyze_resume("John Smith\nSenior Engineer\nPython, React")

        assert "personal_info" in result
        assert "skills" in result
        assert "experience" in result
        assert "education" in result
        assert "keywords" in result
        assert "quality_score" in result
        assert isinstance(result["quality_score"], (int, float))


class TestJobMatching:
    def test_calculate_job_match_structure(self, mock_groq):
        from app.services.ai.groq_client import calculate_job_match

        mock_groq.return_value = {
            "content": """{
                "overall_score": 85.0,
                "skills_match": 90,
                "experience_match": 82,
                "responsibility_match": 85,
                "education_match": 80,
                "industry_match": 88,
                "location_match": 100,
                "matching_skills": ["Python", "FastAPI"],
                "missing_skills": ["Kubernetes"],
                "experience_alignment": "Strong alignment",
                "qualification_alignment": "Good match",
                "concerns": [],
                "reasons_to_apply": ["5+ years Python experience"],
                "ai_recommendation": "Strong fit for this role",
                "match_category": "strong"
            }""",
            "model": "llama-3.1-70b-versatile",
            "prompt_tokens": 400,
            "completion_tokens": 200,
            "total_tokens": 600,
            "latency_ms": 800,
        }

        job_analysis = {
            "required_skills": ["Python", "FastAPI", "Kubernetes"],
            "min_experience_years": 4,
        }

        result = calculate_job_match(SAMPLE_CANDIDATE, job_analysis, SAMPLE_JOB)

        assert "overall_score" in result
        assert 0 <= result["overall_score"] <= 100
        assert result["match_category"] in ["excellent", "strong", "good", "moderate", "low"]
        assert isinstance(result["matching_skills"], list)
        assert isinstance(result["missing_skills"], list)


class TestEmailGeneration:
    def test_generate_email_structure(self, mock_groq):
        from app.services.ai.groq_client import generate_application_email

        mock_groq.return_value = {
            "content": """{
                "subject_lines": ["Subject 1", "Subject 2", "Subject 3"],
                "short_version": "Short email body.",
                "medium_version": "Medium length email body.",
                "detailed_version": "Detailed email body.",
                "reasoning": "This email works because...",
                "suggestions": ["Add more context"]
            }""",
            "model": "llama-3.1-70b-versatile",
            "prompt_tokens": 600,
            "completion_tokens": 400,
            "total_tokens": 1000,
            "latency_ms": 1000,
        }

        result = generate_application_email(
            email_type="hr_outreach",
            candidate_profile=SAMPLE_CANDIDATE,
            company_info={"name": "Google", "industry": "Technology"},
            recipient={"name": "Jane Smith", "designation": "HR Manager"},
            job_info=None,
            tone="professional",
        )

        assert len(result["subject_lines"]) == 3
        assert "short_version" in result
        assert "medium_version" in result
        assert "detailed_version" in result
        assert "reasoning" in result

    def test_generate_cover_letter_structure(self, mock_groq):
        from app.services.ai.groq_client import generate_cover_letter

        mock_groq.return_value = {
            "content": """{
                "subject_line": "Application for Senior Engineer",
                "cover_letter": "Dear Hiring Manager,\\n\\nI am excited...",
                "word_count": 185,
                "key_points_addressed": ["5 years Python", "API experience"]
            }""",
            "model": "llama-3.1-70b-versatile",
            "prompt_tokens": 500,
            "completion_tokens": 300,
            "total_tokens": 800,
            "latency_ms": 900,
        }

        result = generate_cover_letter(
            candidate_profile=SAMPLE_CANDIDATE,
            job_data=SAMPLE_JOB,
            company_info={"name": "TechCo"},
            style="professional",
        )

        assert "subject_line" in result
        assert "cover_letter" in result
        assert "word_count" in result


class TestCompanyResearch:
    def test_research_company_structure(self, mock_groq):
        from app.services.ai.groq_client import research_company

        mock_groq.return_value = {
            "content": """{
                "overview": "Company overview here",
                "industry": "Technology",
                "business_model": "SaaS",
                "products_services": ["Product A", "Product B"],
                "company_size": "1000-5000",
                "headquarters": "San Francisco, CA",
                "tech_focus_areas": ["AI", "Cloud"],
                "notable_aspects": ["Fast growing"],
                "potential_departments_hiring": ["Engineering"],
                "confidence_score": 80,
                "data_sources": ["company website"],
                "disclaimer": "Information may be outdated"
            }""",
            "model": "llama-3.1-70b-versatile",
            "prompt_tokens": 300,
            "completion_tokens": 200,
            "total_tokens": 500,
            "latency_ms": 600,
        }

        result = research_company("Stripe", "https://stripe.com")

        assert "overview" in result
        assert "industry" in result
        assert "confidence_score" in result
        assert isinstance(result["products_services"], list)
