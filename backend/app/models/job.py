import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(100), unique=True, nullable=False)
    base_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    requires_api_key = Column(Boolean, default=False)
    api_configured = Column(Boolean, default=False)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("Job", back_populates="source_ref")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    company_logo = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    country = Column(String(100), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    is_remote = Column(Boolean, default=False, index=True)
    is_hybrid = Column(Boolean, default=False)
    employment_type = Column(String(50), nullable=True, index=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), default="USD")
    experience_min = Column(Integer, nullable=True)
    experience_max = Column(Integer, nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, default=list)
    skills_required = Column(JSON, default=list)
    skills_preferred = Column(JSON, default=list)
    apply_url = Column(Text, nullable=False)
    source = Column(String(100), nullable=False, index=True)
    source_id = Column(UUID(as_uuid=False), ForeignKey("job_sources.id", ondelete="SET NULL"), nullable=True)
    external_id = Column(String(500), nullable=True)
    posted_at = Column(DateTime, nullable=True, index=True)
    deadline = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    industry = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    source_ref = relationship("JobSource", back_populates="jobs")
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    saved = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False)
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="skills")


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(UUID(as_uuid=False), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    match_score = Column(Float, nullable=False, index=True)
    skills_match = Column(Float, default=0)
    experience_match = Column(Float, default=0)
    responsibility_match = Column(Float, default=0)
    education_match = Column(Float, default=0)
    industry_match = Column(Float, default=0)
    location_match = Column(Float, default=0)
    matching_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    experience_alignment = Column(Text, nullable=True)
    qualification_alignment = Column(Text, nullable=True)
    concerns = Column(JSON, default=list)
    reasons_to_apply = Column(JSON, default=list)
    ai_recommendation = Column(Text, nullable=True)
    match_category = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_job_match"),)

    job = relationship("Job", back_populates="matches")


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="saved")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_user_saved_job"),)

    user = relationship("User", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved")
