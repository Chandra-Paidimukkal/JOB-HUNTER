import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Text, Integer,
    Float, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # null for OAuth users
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    google_id = Column(String(255), nullable=True, unique=True)
    verification_token = Column(String(255), nullable=True)
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("JobPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    outreach_contacts = relationship("OutreachContact", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship("UserIntegration", back_populates="user", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    current_location = Column(String(255), nullable=True)
    preferred_locations = Column(JSON, default=list)
    linkedin_url = Column(Text, nullable=True)
    portfolio_url = Column(Text, nullable=True)
    website_url = Column(Text, nullable=True)
    current_title = Column(String(255), nullable=True)
    current_company = Column(String(255), nullable=True)
    total_experience_years = Column(Float, nullable=True)
    professional_summary = Column(Text, nullable=True)
    technical_skills = Column(JSON, default=list)
    soft_skills = Column(JSON, default=list)
    industries = Column(JSON, default=list)
    education_summary = Column(Text, nullable=True)
    certifications_summary = Column(Text, nullable=True)
    notice_period = Column(String(100), nullable=True)
    willing_to_relocate = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")


class JobPreferences(Base):
    __tablename__ = "job_preferences"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    preferred_titles = Column(JSON, default=list)
    preferred_industries = Column(JSON, default=list)
    preferred_companies = Column(JSON, default=list)
    preferred_countries = Column(JSON, default=list)
    preferred_cities = Column(JSON, default=list)
    remote_ok = Column(Boolean, default=True)
    hybrid_ok = Column(Boolean, default=True)
    onsite_ok = Column(Boolean, default=True)
    full_time = Column(Boolean, default=True)
    part_time = Column(Boolean, default=False)
    contract = Column(Boolean, default=False)
    internship = Column(Boolean, default=False)
    expected_salary = Column(Float, nullable=True)
    min_salary = Column(Float, nullable=True)
    currency = Column(String(10), default="USD")
    career_objective = Column(Text, nullable=True)
    short_term_goals = Column(Text, nullable=True)
    long_term_goals = Column(Text, nullable=True)
    desired_responsibilities = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")
