"""
AI endpoints — all Groq-powered intelligence functions.
API keys never leave the backend.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User, UserProfile
from app.models.resume import Resume
from app.models.job import Job
from app.services.ai import groq_client as ai

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI"])


def _get_primary_resume(db: Session, user_id: str) -> Optional[Resume]:
    return (
        db.query(Resume)
        .filter(Resume.user_id == user_id, Resume.is_primary == True)
        .first()
    )


def _get_candidate_profile(db: Session, user: User) -> dict:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    resume = _get_primary_resume(db, user.id)
    base = {
        "name": user.full_name,
        "email": user.email,
    }
    if profile:
        base.update({
            "current_title": profile.current_title,
            "total_experience_years": profile.total_experience_years,
            "technical_skills": profile.technical_skills or [],
            "soft_skills": profile.soft_skills or [],
            "industries": profile.industries or [],
            "professional_summary": profile.professional_summary,
        })
    if resume and resume.extracted_data:
        base.update(resume.extracted_data)
    return base


# ── Schemas ──────────────────────────────────────────────────

class AnalyzeResumeRequest(BaseModel):
    resume_id: str


class JobMatchRequest(BaseModel):
    job_id: str
    resume_id: Optional[str] = None


class CoverLetterRequest(BaseModel):
    job_id: str
    resume_id: Optional[str] = None
    style: str = "professional"


class GenerateEmailRequest(BaseModel):
    email_type: str
    company_name: str
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    contact_name: Optional[str] = None
    contact_designation: Optional[str] = None
    contact_email: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    resume_id: Optional[str] = None
    tone: str = "professional"
    additional_instructions: str = ""


class LinkedInMessageRequest(BaseModel):
    message_type: str = "connection_request"
    recipient_name: Optional[str] = None
    recipient_title: Optional[str] = None
    company_name: Optional[str] = None
    resume_id: Optional[str] = None


class ResearchCompanyRequest(BaseModel):
    company_name: str
    website: Optional[str] = None
    additional_context: str = ""


class InterviewPrepRequest(BaseModel):
    job_id: str
    resume_id: Optional[str] = None


class CustomizeResumeRequest(BaseModel):
    job_id: str
    resume_id: Optional[str] = None


class ApplicationAnswersRequest(BaseModel):
    job_id: str
    questions: List[str]
    resume_id: Optional[str] = None


class AnalyzeAnswerRequest(BaseModel):
    question: str
    answer: str
    job_context: str = ""


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/analyze-resume")
def analyze_resume(
    payload: AnalyzeResumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    resume = db.query(Resume).filter(
        Resume.id == payload.resume_id,
        Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if not resume.parsed_text:
        raise HTTPException(status_code=422, detail="Resume has not been parsed yet")

    try:
        result = ai.analyze_resume(resume.parsed_text)
        resume.extracted_data = result
        resume.quality_score = result.get("quality_score", 0)
        resume.is_analyzed = True
        db.commit()
        return {"result": result, "quality_score": resume.quality_score}
    except Exception as e:
        logger.error(f"Resume analysis failed: {e}")
        raise HTTPException(status_code=503, detail=f"AI analysis failed: {str(e)}")


@router.post("/generate-cover-letter")
def generate_cover_letter(
    payload: CoverLetterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate = _get_candidate_profile(db, current_user)
    if not candidate.get("technical_skills") and not candidate.get("experience"):
        raise HTTPException(
            status_code=422,
            detail="Please complete your profile or upload a resume before generating a cover letter."
        )

    try:
        result = ai.generate_cover_letter(
            candidate_profile=candidate,
            job_data={
                "title": job.title,
                "company": job.company,
                "description": job.description,
                "location": job.location,
            },
            company_info={"name": job.company, "industry": job.industry},
            style=payload.style,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI generation failed: {str(e)}")


@router.post("/generate-email")
def generate_email(
    payload: GenerateEmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = _get_candidate_profile(db, current_user)

    company_info = {
        "name": payload.company_name,
        "website": payload.company_website,
        "industry": payload.company_industry,
    }
    recipient = {
        "name": payload.contact_name,
        "designation": payload.contact_designation,
        "department": payload.department,
    }
    job_info = None
    if payload.job_title or payload.job_description:
        job_info = {
            "title": payload.job_title,
            "description": payload.job_description,
        }

    try:
        result = ai.generate_application_email(
            email_type=payload.email_type,
            candidate_profile=candidate,
            company_info=company_info,
            recipient=recipient,
            job_info=job_info,
            tone=payload.tone,
            additional_instructions=payload.additional_instructions,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Email generation failed: {str(e)}")


@router.post("/generate-linkedin-message")
def generate_linkedin_message(
    payload: LinkedInMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    candidate = _get_candidate_profile(db, current_user)
    recipient = {
        "name": payload.recipient_name,
        "title": payload.recipient_title,
        "company": payload.company_name,
    }
    company_info = {"name": payload.company_name} if payload.company_name else {}

    try:
        result = ai.generate_linkedin_message(
            message_type=payload.message_type,
            candidate_profile=candidate,
            recipient=recipient,
            company_info=company_info,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LinkedIn message generation failed: {str(e)}")


@router.post("/research-company")
def research_company(
    payload: ResearchCompanyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = ai.research_company(
            company_name=payload.company_name,
            website=payload.website or "",
            additional_context=payload.additional_context,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Company research failed: {str(e)}")


@router.post("/interview-preparation")
def interview_preparation(
    payload: InterviewPrepRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate = _get_candidate_profile(db, current_user)

    try:
        result = ai.generate_interview_questions(
            job_data={"title": job.title, "company": job.company, "description": job.description},
            candidate_profile=candidate,
            company_info={"name": job.company},
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Interview prep generation failed: {str(e)}")


@router.post("/customize-resume")
def customize_resume(
    payload: CustomizeResumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    resume = (
        db.query(Resume).filter(
            Resume.id == payload.resume_id if payload.resume_id else True,
            Resume.user_id == current_user.id,
        ).first()
        if payload.resume_id
        else _get_primary_resume(db, current_user.id)
    )

    if not resume or not resume.extracted_data:
        raise HTTPException(status_code=422, detail="Resume not found or not analyzed")

    try:
        job_analysis = ai.analyze_job_description(job.description, job.title, job.company)
        result = ai.generate_resume_customization(
            resume_data=resume.extracted_data,
            job_data={"title": job.title, "company": job.company},
            job_analysis=job_analysis,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Resume customization failed: {str(e)}")


@router.post("/generate-application-answers")
def generate_application_answers(
    payload: ApplicationAnswersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    candidate = _get_candidate_profile(db, current_user)

    try:
        result = ai.generate_application_answers(
            questions=payload.questions,
            candidate_profile=candidate,
            job_data={"title": job.title, "company": job.company},
        )
        return {"answers": result}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Answer generation failed: {str(e)}")


@router.post("/analyze-interview-answer")
def analyze_interview_answer(
    payload: AnalyzeAnswerRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        result = ai.analyze_interview_answer(
            question=payload.question,
            answer=payload.answer,
            job_context=payload.job_context,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Answer analysis failed: {str(e)}")
