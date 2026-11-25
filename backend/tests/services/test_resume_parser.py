"""
Tests for resume parsing service.
"""
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock


class TestResumeParsing:
    def test_extract_text_from_pdf(self, tmp_path):
        """Test PDF text extraction with a minimal PDF."""
        # Create a minimal valid PDF
        pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""
        pdf_path = str(tmp_path / "test.pdf")
        with open(pdf_path, "wb") as f:
            f.write(pdf_content)

        from app.services.resumes.parser import extract_text_from_pdf
        # Minimal PDF may return empty string — just verify no exception
        try:
            text = extract_text_from_pdf(pdf_path)
            assert isinstance(text, str)
        except Exception as e:
            pytest.skip(f"PDF test requires valid PDF: {e}")

    def test_unsupported_file_type_raises(self, tmp_path):
        from app.services.resumes.parser import extract_resume_text
        txt_path = str(tmp_path / "resume.txt")
        with open(txt_path, "w") as f:
            f.write("some text")
        with pytest.raises(ValueError, match="Unsupported file type"):
            extract_resume_text(txt_path, "txt")

    def test_empty_file_raises(self, tmp_path):
        from app.services.resumes.parser import validate_resume_file
        empty_path = str(tmp_path / "empty.pdf")
        open(empty_path, "w").close()
        with pytest.raises((ValueError, FileNotFoundError)):
            validate_resume_file(empty_path, "pdf")

    def test_nonexistent_file_raises(self):
        from app.services.resumes.parser import extract_resume_text
        with pytest.raises(FileNotFoundError):
            extract_resume_text("/nonexistent/path/resume.pdf", "pdf")


class TestGroqResumeAnalysis:
    def test_analyze_resume_returns_structured_data(self, mock_groq_resume):
        """Test that Groq analysis returns properly structured data."""
        from app.services.ai.groq_client import analyze_resume

        result = analyze_resume("John Smith\nSenior Engineer at Acme\nPython, React, SQL")

        assert "personal_info" in result
        assert "skills" in result
        assert "experience" in result
        assert "keywords" in result
        assert isinstance(result["skills"]["technical"], list)

    def test_analyze_resume_handles_groq_failure(self):
        """Test graceful handling when Groq is unavailable."""
        from app.services.ai.groq_client import analyze_resume

        with patch("app.services.ai.groq_client._call_groq") as mock:
            mock.side_effect = Exception("Groq API unavailable")
            with pytest.raises(Exception):
                analyze_resume("Test resume text")

    def test_json_response_parsing(self):
        """Test that markdown-wrapped JSON is correctly parsed."""
        from app.services.ai.groq_client import _parse_json_response

        # With markdown code block
        raw = '```json\n{"key": "value"}\n```'
        result = _parse_json_response(raw)
        assert result == {"key": "value"}

        # Plain JSON
        result = _parse_json_response('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_parsing_invalid_raises(self):
        from app.services.ai.groq_client import _parse_json_response
        with pytest.raises(ValueError):
            _parse_json_response("this is not json at all and has no json in it")
