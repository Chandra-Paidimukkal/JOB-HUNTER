"""
Groq AI Client — central AI service layer for JobHunter AI.
All AI calls are routed through this module.
"""
import json
import time
import logging
from typing import Any, Dict, List, Optional
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[Groq] = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not configured. Set it in your .env file.")
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _call_groq(
    messages: List[Dict],
    model: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    response_format: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Low-level Groq call with retry logic."""
    client = get_groq_client()
    start = time.time()

    kwargs: Dict[str, Any] = {
        "model": model or settings.GROQ_MODEL,
        "messages": messages,
        "max_tokens": max_tokens or settings.GROQ_MAX_TOKENS,
        "temperature": temperature if temperature is not None else settings.GROQ_TEMPERATURE,
    }
    if response_format:
        kwargs["response_format"] = response_format

    response = client.chat.completions.create(**kwargs)
    latency_ms = int((time.time() - start) * 1000)

    return {
        "content": response.choices[0].message.content,
        "model": response.model,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
        "latency_ms": latency_ms,
    }


def _parse_json_response(raw: str) -> Dict:
    """Extract JSON from Groq response, handling markdown code blocks."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Could not parse JSON from response: {raw[:200]}")


# ── Core AI Functions ──────────────────────────────────────────────────────────

def analyze_resume(resume_text: str) -> Dict:
    """Extract structured candidate profile from resume text."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert resume parser. Extract structured information from the resume text. "
                "Return ONLY valid JSON matching the schema exactly. "
                "Do NOT invent or assume any information not present in the resume text."
            ),
        },
        {
            "role": "user",
            "content": f"""Parse this resume and return a JSON object with this exact structure:
{{
  "personal_info": {{
    "name": "string or null",
    "email": "string or null",
    "phone": "string or null",
    "location": "string or null",
    "linkedin": "string or null",
    "portfolio": "string or null"
  }},
  "professional_summary": "string or null",
  "experience": [
    {{
      "company": "string",
      "title": "string",
      "start_date": "string",
      "end_date": "string or null",
      "is_current": boolean,
      "location": "string or null",
      "description": "string or null",
      "achievements": ["string"]
    }}
  ],
  "education": [
    {{
      "institution": "string",
      "degree": "string",
      "field": "string or null",
      "start_year": number or null,
      "end_year": number or null,
      "gpa": "string or null"
    }}
  ],
  "skills": {{
    "technical": ["string"],
    "soft": ["string"]
  }},
  "certifications": [
    {{
      "name": "string",
      "issuer": "string or null",
      "issue_date": "string or null"
    }}
  ],
  "projects": [
    {{
      "name": "string",
      "description": "string or null",
      "technologies": ["string"],
      "url": "string or null"
    }}
  ],
  "achievements": ["string"],
  "keywords": ["string"],
  "total_experience_years": number or null,
  "quality_score": number between 0 and 100
}}

RESUME TEXT:
{resume_text[:8000]}""",
        },
    ]

    result = _call_groq(messages, temperature=0.1)
    return _parse_json_response(result["content"])


def extract_candidate_profile(resume_data: Dict, user_profile: Dict) -> Dict:
    """Merge resume data with user profile to create a comprehensive candidate profile."""
    messages = [
        {
            "role": "system",
            "content": "You are a career expert. Create a unified candidate profile from resume and profile data.",
        },
        {
            "role": "user",
            "content": f"""Create a comprehensive candidate profile summary for job matching.

Resume Data: {json.dumps(resume_data, indent=2)[:3000]}
User Profile: {json.dumps(user_profile, indent=2)[:2000]}

Return JSON:
{{
  "headline": "string — one line professional headline",
  "summary": "string — 2-3 sentence professional summary",
  "top_skills": ["string — top 10 most relevant skills"],
  "experience_level": "junior|mid|senior|principal|executive",
  "total_years": number,
  "key_industries": ["string"],
  "notable_achievements": ["string — top 3"],
  "value_proposition": "string — what makes this candidate unique"
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.3)
    return _parse_json_response(result["content"])


def analyze_job_description(job_description: str, job_title: str, company: str) -> Dict:
    """Extract structured requirements from a job description."""
    messages = [
        {
            "role": "system",
            "content": "You are an expert recruiter who analyzes job descriptions. Extract all requirements accurately.",
        },
        {
            "role": "user",
            "content": f"""Analyze this job description for {job_title} at {company} and extract structured data.

JOB DESCRIPTION:
{job_description[:5000]}

Return JSON:
{{
  "required_skills": ["string"],
  "preferred_skills": ["string"],
  "min_experience_years": number or null,
  "max_experience_years": number or null,
  "education_requirements": ["string"],
  "key_responsibilities": ["string"],
  "industry": "string",
  "seniority_level": "junior|mid|senior|principal|executive",
  "work_mode": "remote|hybrid|onsite|flexible",
  "key_keywords": ["string — important ATS keywords"],
  "company_values": ["string"],
  "benefits": ["string"],
  "salary_range": "string or null",
  "technical_stack": ["string"]
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.1)
    return _parse_json_response(result["content"])


def calculate_job_match(candidate_profile: Dict, job_analysis: Dict, job_data: Dict) -> Dict:
    """Calculate compatibility score between candidate and job."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a recruitment expert who evaluates candidate-job fit. "
                "Be accurate and honest — do not inflate scores. "
                "Base scores only on actual evidence from the candidate profile."
            ),
        },
        {
            "role": "user",
            "content": f"""Evaluate this candidate-job match and provide detailed scoring.

CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)[:3000]}

JOB ANALYSIS:
{json.dumps(job_analysis, indent=2)[:3000]}

JOB DETAILS:
Title: {job_data.get('title')}
Company: {job_data.get('company')}
Location: {job_data.get('location')}
Employment Type: {job_data.get('employment_type')}

Return JSON with scores from 0-100:
{{
  "overall_score": number (weighted average),
  "skills_match": number (weight 30%),
  "experience_match": number (weight 25%),
  "responsibility_match": number (weight 20%),
  "education_match": number (weight 10%),
  "industry_match": number (weight 10%),
  "location_match": number (weight 5%),
  "matching_skills": ["string — skills candidate has that job requires"],
  "missing_skills": ["string — required skills candidate lacks"],
  "experience_alignment": "string — brief explanation",
  "qualification_alignment": "string — brief explanation",
  "concerns": ["string — real concerns about the fit"],
  "reasons_to_apply": ["string — genuine strengths for this role"],
  "ai_recommendation": "string — honest 2-3 sentence recommendation",
  "match_category": "excellent|strong|good|moderate|low"
}}

Match categories: excellent=90-100, strong=80-89, good=70-79, moderate=50-69, low=below 50""",
        },
    ]
    result = _call_groq(messages, temperature=0.2)
    return _parse_json_response(result["content"])


def generate_cover_letter(
    candidate_profile: Dict,
    job_data: Dict,
    company_info: Optional[Dict],
    style: str = "professional",
) -> Dict:
    """Generate a personalized cover letter."""
    style_instructions = {
        "professional": "formal, structured, achievement-focused",
        "conversational": "warm, authentic, storytelling approach",
        "concise": "direct, punchy, maximum 150 words",
    }
    style_desc = style_instructions.get(style, style_instructions["professional"])

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert career writer. Generate authentic, personalized cover letters. "
                "Only use real information from the candidate profile. Never invent qualifications. "
                "Avoid clichés like 'I am excited to apply' or 'I am a team player'."
            ),
        },
        {
            "role": "user",
            "content": f"""Write a cover letter for:

JOB: {job_data.get('title')} at {job_data.get('company')}
STYLE: {style_desc}

CANDIDATE PROFILE:
{json.dumps(candidate_profile, indent=2)[:2500]}

JOB DESCRIPTION:
{job_data.get('description', '')[:2000]}

COMPANY INFO:
{json.dumps(company_info or {}, indent=2)[:1000]}

Return JSON:
{{
  "subject_line": "string",
  "cover_letter": "string — full cover letter with proper formatting",
  "word_count": number,
  "key_points_addressed": ["string"]
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.6)
    return _parse_json_response(result["content"])


def generate_application_email(
    email_type: str,
    candidate_profile: Dict,
    company_info: Dict,
    recipient: Dict,
    job_info: Optional[Dict],
    tone: str = "professional",
    additional_instructions: str = "",
) -> Dict:
    """Generate professional outreach emails."""
    EMAIL_TYPE_PROMPTS = {
        "job_application": "a formal job application email for a specific advertised opening",
        "hr_outreach": "a professional email to an HR recruiter about suitable opportunities",
        "hiring_manager": "a personalized email to a hiring manager explaining how candidate skills benefit their team",
        "cold_outreach": "a cold outreach email to a company where no specific opening is listed",
        "referral_request": "a professional referral request to an employee at the target company",
        "recruiter_introduction": "an introduction email to a recruiter presenting candidate background",
        "post_application_followup": "a follow-up email after submitting an application",
        "interview_thankyou": "a thank-you email after an interview",
        "linkedin_connection": "a LinkedIn connection request message (300 chars max)",
        "linkedin_followup": "a LinkedIn follow-up message after connection was accepted",
        "networking": "a professional networking outreach message",
    }

    purpose = EMAIL_TYPE_PROMPTS.get(email_type, email_type)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert professional communication writer. "
                "Write genuine, specific emails that stand out. "
                "Never use generic phrases like 'I hope this email finds you well'. "
                "Reference specific company information and candidate achievements. "
                "Never invent information not provided. "
                f"Tone: {tone}."
            ),
        },
        {
            "role": "user",
            "content": f"""Write {purpose}.

CANDIDATE:
{json.dumps(candidate_profile, indent=2)[:2000]}

TARGET COMPANY:
{json.dumps(company_info, indent=2)[:1500]}

RECIPIENT:
Name: {recipient.get('name', 'Hiring Team')}
Title: {recipient.get('designation', '')}
Department: {recipient.get('department', '')}

JOB INFO:
{json.dumps(job_info or {}, indent=2)[:1000]}

ADDITIONAL INSTRUCTIONS: {additional_instructions}

Return JSON:
{{
  "subject_lines": ["string — option 1", "string — option 2", "string — option 3"],
  "short_version": "string — 50-80 words",
  "medium_version": "string — 100-150 words",
  "detailed_version": "string — 150-250 words",
  "reasoning": "string — why this email is relevant and what makes it stand out",
  "suggestions": ["string — 2-3 improvement suggestions"]
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.65, max_tokens=2000)
    return _parse_json_response(result["content"])


def research_company(company_name: str, website: str, additional_context: str = "") -> Dict:
    """Research a company using provided information."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a business analyst. Analyze the company based on the information provided. "
                "Only state what you know with confidence. Mark uncertain information clearly. "
                "Never fabricate specific employee names, internal projects, or financials."
            ),
        },
        {
            "role": "user",
            "content": f"""Provide a structured company analysis for: {company_name}
Website: {website}
Additional context: {additional_context}

Return JSON:
{{
  "overview": "string — 2-3 sentence company overview",
  "industry": "string",
  "business_model": "string",
  "products_services": ["string"],
  "company_size": "string — estimate if unknown",
  "headquarters": "string",
  "tech_focus_areas": ["string"],
  "notable_aspects": ["string"],
  "potential_departments_hiring": ["string"],
  "confidence_score": number 0-100,
  "data_sources": ["string"],
  "disclaimer": "string — what information might be outdated or uncertain"
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.3)
    return _parse_json_response(result["content"])


def generate_linkedin_message(
    message_type: str,
    candidate_profile: Dict,
    recipient: Dict,
    company_info: Optional[Dict],
) -> Dict:
    """Generate LinkedIn connection/follow-up messages."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are a professional networking expert. "
                "Write concise, genuine LinkedIn messages. "
                "Connection requests MUST be under 300 characters. "
                "Follow-ups under 500 characters. "
                "Be specific, not generic."
            ),
        },
        {
            "role": "user",
            "content": f"""Write a LinkedIn {message_type} message.

SENDER (Candidate):
{json.dumps(candidate_profile, indent=2)[:1500]}

RECIPIENT:
{json.dumps(recipient, indent=2)[:800]}

COMPANY:
{json.dumps(company_info or {}, indent=2)[:600]}

Return JSON:
{{
  "message": "string — the actual message",
  "character_count": number,
  "alternative_message": "string — a shorter alternative"
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.6)
    return _parse_json_response(result["content"])


def generate_interview_questions(
    job_data: Dict,
    candidate_profile: Dict,
    company_info: Optional[Dict],
) -> Dict:
    """Generate comprehensive interview preparation questions."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an experienced interviewer. Generate realistic interview questions "
                "based on the actual job requirements and candidate background."
            ),
        },
        {
            "role": "user",
            "content": f"""Generate interview preparation for:

JOB: {job_data.get('title')} at {job_data.get('company')}
JOB DESCRIPTION: {job_data.get('description', '')[:2000]}

CANDIDATE:
{json.dumps(candidate_profile, indent=2)[:2000]}

Return JSON:
{{
  "technical_questions": [
    {{
      "question": "string",
      "difficulty": "easy|medium|hard",
      "suggested_answer": "string",
      "why_asked": "string"
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "string",
      "star_answer": {{
        "situation": "string — example situation from candidate's background",
        "task": "string",
        "action": "string",
        "result": "string"
      }}
    }}
  ],
  "hr_questions": [
    {{
      "question": "string",
      "suggested_answer": "string"
    }}
  ],
  "company_specific_questions": [
    {{
      "question": "string",
      "context": "string"
    }}
  ],
  "questions_to_ask_interviewer": ["string"],
  "preparation_tips": ["string"]
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.5, max_tokens=3000)
    return _parse_json_response(result["content"])


def generate_resume_customization(
    resume_data: Dict,
    job_data: Dict,
    job_analysis: Dict,
) -> Dict:
    """Customize resume content for a specific job. Never invents new experience."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert resume writer. Optimize the resume for the target job "
                "by reordering, emphasizing, and rewording existing content. "
                "CRITICAL: Never add skills, experience, or achievements that are not in the original resume. "
                "Only work with what the candidate actually has."
            ),
        },
        {
            "role": "user",
            "content": f"""Optimize this resume for the target job. Only use existing content — reorder and emphasize relevant parts.

ORIGINAL RESUME DATA:
{json.dumps(resume_data, indent=2)[:3000]}

TARGET JOB:
Title: {job_data.get('title')}
Company: {job_data.get('company')}
Key Requirements: {json.dumps(job_analysis.get('required_skills', []))}
Keywords: {json.dumps(job_analysis.get('key_keywords', []))}

Return JSON:
{{
  "optimized_summary": "string — rewritten professional summary highlighting job-relevant aspects",
  "reordered_skills": ["string — existing skills ordered by relevance to this job"],
  "highlighted_experience": [
    {{
      "company": "string",
      "title": "string",
      "emphasis": "string — what to emphasize for this job",
      "relevant_achievements": ["string — from original resume only"]
    }}
  ],
  "keywords_incorporated": ["string — ATS keywords naturally included"],
  "changes_made": ["string — list of specific changes made"],
  "missing_keywords": ["string — keywords in JD not in resume — candidate may need to gain these skills"]
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.3)
    return _parse_json_response(result["content"])


def analyze_interview_answer(question: str, answer: str, job_context: str) -> Dict:
    """Provide AI feedback on a mock interview answer."""
    messages = [
        {
            "role": "system",
            "content": "You are an expert interview coach providing constructive, actionable feedback.",
        },
        {
            "role": "user",
            "content": f"""Evaluate this interview answer:

QUESTION: {question}
ANSWER: {answer}
JOB CONTEXT: {job_context}

Return JSON:
{{
  "score": number 0-10,
  "strengths": ["string"],
  "improvements": ["string"],
  "better_answer": "string — improved version of the answer",
  "tips": ["string"]
}}""",
        },
    ]
    result = _call_groq(messages, temperature=0.4)
    return _parse_json_response(result["content"])


def generate_application_answers(
    questions: List[str],
    candidate_profile: Dict,
    job_data: Dict,
) -> List[Dict]:
    """Generate answers to application form questions."""
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert job application writer. "
                "Generate honest, specific answers based only on the candidate's actual background. "
                "Never fabricate experience or qualifications."
            ),
        },
        {
            "role": "user",
            "content": f"""Generate answers for these application questions:

QUESTIONS: {json.dumps(questions)}

CANDIDATE:
{json.dumps(candidate_profile, indent=2)[:2000]}

JOB: {job_data.get('title')} at {job_data.get('company')}

Return JSON array:
[
  {{
    "question": "string",
    "answer": "string — specific answer using candidate's real background",
    "word_count": number
  }}
]""",
        },
    ]
    result = _call_groq(messages, temperature=0.4)
    return _parse_json_response(result["content"])
