import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(UUID(as_uuid=False), ForeignKey("applications.id", ondelete="CASCADE"), nullable=True)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    interview_date = Column(DateTime, nullable=True)
    interview_type = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    interview_id = Column(UUID(as_uuid=False), ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    suggested_answer = Column(Text, nullable=True)
    star_answer = Column(JSON, nullable=True)
    difficulty = Column(String(20), nullable=True)
    user_answer = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="questions")
