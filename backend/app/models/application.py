import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


APPLICATION_STATUSES = [
    "saved", "recommended", "ready_to_apply", "applied", "under_review",
    "recruiter_contacted", "interview_scheduled", "interview_completed",
    "assessment_pending", "offer_received", "rejected", "withdrawn"
]


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(UUID(as_uuid=False), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="saved", nullable=False, index=True)
    applied_date = Column(DateTime, nullable=True)
    cover_letter = Column(Text, nullable=True)
    custom_resume_content = Column(Text, nullable=True)
    recruiter_name = Column(String(255), nullable=True)
    recruiter_email = Column(String(255), nullable=True)
    recruiter_linkedin = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume")
    documents = relationship("ApplicationDocument", back_populates="application", cascade="all, delete-orphan")
    answers = relationship("ApplicationAnswer", back_populates="application", cascade="all, delete-orphan")


class ApplicationDocument(Base):
    __tablename__ = "application_documents"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    application_id = Column(UUID(as_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String(100), nullable=False)
    file_path = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="documents")


class ApplicationAnswer(Base):
    __tablename__ = "application_answers"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    application_id = Column(UUID(as_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    application = relationship("Application", back_populates="answers")
