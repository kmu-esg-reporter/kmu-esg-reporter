"""Database models for ESG Reporter."""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from .base import Base


class Company(Base):
    """Company model for storing company information."""
    
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    business_number = Column(String(50), unique=True, index=True)
    industry = Column(String(100))
    size = Column(String(50))  # small, medium, large
    address = Column(Text)
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    esg_data = relationship("ESGData", back_populates="company")
    reports = relationship("Report", back_populates="company")


class ESGData(Base):
    """ESG data model for storing environmental, social, and governance metrics."""
    
    __tablename__ = "esg_data"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Data categorization
    category = Column(String(50), nullable=False)  # Environmental, Social, Governance
    subcategory = Column(String(100))
    metric_name = Column(String(255), nullable=False)
    metric_code = Column(String(50))
    
    # Data values
    value = Column(Float)
    unit = Column(String(50))
    text_value = Column(Text)  # For qualitative data
    
    # Data source and quality
    data_source = Column(String(100))  # manual, excel, erp, api
    source_file = Column(String(255))  # Original file name if applicable
    quality_score = Column(Float, default=1.0)  # Data quality indicator
    
    # Temporal information
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    reporting_year = Column(Integer, index=True)
    
    # Metadata
    raw_data = Column(JSON)  # Store original raw data
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="esg_data")


class Report(Base):
    """Generated ESG reports."""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    title = Column(String(255), nullable=False)
    report_type = Column(String(50))  # annual, quarterly, custom
    content = Column(Text)
    summary = Column(Text)
    
    # Report metadata
    generated_by = Column(String(50))  # system, user, chatbot
    format = Column(String(20))  # pdf, html, json
    status = Column(String(20), default="draft")  # draft, published, archived
    
    # File information
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="reports")


class ChatSession(Base):
    """Chat sessions for the ESG chatbot."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    
    # Session metadata
    user_id = Column(String(255))  # For future user management
    title = Column(String(255))
    
    # Chat history
    messages = Column(JSON)  # Store chat history as JSON
    context = Column(JSON)   # Store conversation context
    
    # Session statistics
    message_count = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")


class DataImportLog(Base):
    """Log for data import operations."""
    
    __tablename__ = "data_import_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Import details
    import_type = Column(String(50))  # excel, erp, api, manual
    source_file = Column(String(500))
    status = Column(String(20))  # success, error, partial
    
    # Statistics
    records_processed = Column(Integer, default=0)
    records_imported = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    
    # Error information
    error_log = Column(JSON)
    validation_errors = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company")