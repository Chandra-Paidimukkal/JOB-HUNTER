import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False, index=True)
    website = Column(Text, nullable=True)
    linkedin_url = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)
    industry = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    headquarters = Column(String(255), nullable=True)
    locations = Column(JSON, default=list)
    size = Column(String(100), nullable=True)
    founded_year = Column(Integer, nullable=True)
    products_services = Column(JSON, default=list)
    recent_news = Column(JSON, default=list)
    careers_url = Column(Text, nullable=True)
    researched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contacts = relationship("CompanyContact", back_populates="company", cascade="all, delete-orphan")
    research = relationship("CompanyResearch", back_populates="company", cascade="all, delete-orphan")


class CompanyContact(Base):
    __tablename__ = "company_contacts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=True)
    designation = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    linkedin_url = Column(Text, nullable=True)
    department = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="contacts")


class CompanyResearch(Base):
    __tablename__ = "company_research"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=False), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    overview = Column(Text, nullable=True)
    key_people = Column(JSON, default=list)
    tech_stack = Column(JSON, default=list)
    candidate_fit_analysis = Column(Text, nullable=True)
    relevant_departments = Column(JSON, default=list)
    confidence_score = Column(Integer, nullable=True)
    sources = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="research")
