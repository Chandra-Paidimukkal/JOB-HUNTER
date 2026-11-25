import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class OutreachCampaign(Base):
    __tablename__ = "outreach_campaigns"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    contacts = relationship("OutreachContact", back_populates="campaign")


class OutreachContact(Base):
    __tablename__ = "outreach_contacts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(UUID(as_uuid=False), ForeignKey("outreach_campaigns.id", ondelete="SET NULL"), nullable=True)
    company_name = Column(String(255), nullable=False)
    company_website = Column(Text, nullable=True)
    company_industry = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    contact_designation = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_linkedin = Column(Text, nullable=True)
    department = Column(String(255), nullable=True)
    status = Column(String(100), default="new_prospect", nullable=False, index=True)
    email_type = Column(String(100), nullable=True)
    email_subject = Column(Text, nullable=True)
    generated_email = Column(Text, nullable=True)
    sent_date = Column(DateTime, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    response_received = Column(Boolean, default=False)
    response_notes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="outreach_contacts")
    campaign = relationship("OutreachCampaign", back_populates="contacts")
    generated_emails = relationship("GeneratedEmail", back_populates="outreach_contact", cascade="all, delete-orphan")


class GeneratedEmail(Base):
    __tablename__ = "generated_emails"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    outreach_contact_id = Column(UUID(as_uuid=False), ForeignKey("outreach_contacts.id", ondelete="CASCADE"), nullable=True)
    email_type = Column(String(100), nullable=False)
    subject_lines = Column(JSON, default=list)
    selected_subject = Column(Text, nullable=True)
    short_version = Column(Text, nullable=True)
    medium_version = Column(Text, nullable=True)
    detailed_version = Column(Text, nullable=True)
    selected_version = Column(Text, nullable=True)
    tone = Column(String(100), nullable=True)
    reasoning = Column(Text, nullable=True)
    suggestions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    outreach_contact = relationship("OutreachContact", back_populates="generated_emails")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email_type = Column(String(100), nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    tone = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SentEmail(Base):
    __tablename__ = "sent_emails"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    outreach_contact_id = Column(UUID(as_uuid=False), ForeignKey("outreach_contacts.id", ondelete="SET NULL"), nullable=True)
    to_email = Column(String(255), nullable=False)
    subject = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    gmail_message_id = Column(String(255), nullable=True)
    sent_via = Column(String(50), default="gmail")
    sent_at = Column(DateTime, default=datetime.utcnow)


class LinkedInMessage(Base):
    __tablename__ = "linkedin_messages"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_name = Column(String(255), nullable=True)
    recipient_title = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=True)
    message_type = Column(String(100), nullable=False)
    generated_message = Column(Text, nullable=False)
    character_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
