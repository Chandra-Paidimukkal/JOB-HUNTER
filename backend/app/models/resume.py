import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, Float, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(10), nullable=False)  # pdf | docx
    file_size = Column(Integer, nullable=False)
    version_name = Column(String(255), nullable=True)
    is_primary = Column(Boolean, default=False)
    parsed_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    quality_score = Column(Float, nullable=True)
    keyword_density = Column(JSON, nullable=True)
    is_analyzed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="resumes")
    versions = relationship("ResumeVersion", back_populates="base_resume", cascade="all, delete-orphan")


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    resume_id = Column(UUID(as_uuid=False), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id", ondelete="SET NULL"), nullable=True)
    version_name = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    changes_made = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    base_resume = relationship("Resume", back_populates="versions")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(255), nullable=False)
    skill_type = Column(String(50), nullable=False)  # technical | soft
    proficiency = Column(String(50), nullable=True)
    years_experience = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateExperience(Base):
    __tablename__ = "candidate_experience"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    achievements = Column(JSON, default=list)
    technologies = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)
    field = Column(String(255), nullable=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    gpa = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateCertification(Base):
    __tablename__ = "candidate_certifications"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    issuer = Column(String(255), nullable=True)
    issue_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=True)
    credential_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
