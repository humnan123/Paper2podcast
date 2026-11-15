from datetime import datetime
from sqlalchemy import (Column, Integer, String, Text, Boolean, Date, DateTime,
                        ForeignKey, UniqueConstraint)
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="author")  # admin | chairperson | author | reviewer
    is_verified = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Otp(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code_hash = Column(String(255), nullable=False)
    purpose = Column(String(20), nullable=False)  # verify | reset
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, nullable=False, default=0)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conference(Base):
    __tablename__ = "conferences"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    submission_deadline = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="open")  # open | closed
    chairperson_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

class Paper(Base):
    __tablename__ = "papers"
    id = Column(Integer, primary_key=True)
    conference_id = Column(Integer, ForeignKey("conferences.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    abstract = Column(Text, nullable=False)
    keywords = Column(String(255))
    file_path = Column(String(500), nullable=False)
    status = Column(String(30), nullable=False, default="submitted")
    submitted_at = Column(DateTime, default=datetime.utcnow)

class ReviewAssignment(Base):
    __tablename__ = "review_assignments"
    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey("papers.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), nullable=False, default="assigned")  # assigned | accepted | declined
    assigned_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)
    decline_reason = Column(Text)
    __table_args__ = (UniqueConstraint("paper_id", "reviewer_id", name="uq_paper_reviewer"),)