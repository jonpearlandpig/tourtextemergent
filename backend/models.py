from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, JSON, Text, ForeignKey, Table, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

# Junction table for many-to-many relationship between truth records and sources
truth_record_sources = Table(
    'truth_record_sources',
    Base.metadata,
    Column('truth_record_id', String, ForeignKey('truth_records.id'), primary_key=True),
    Column('source_file_id', String, ForeignKey('source_files.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

class RecordStatus(str, enum.Enum):
    DRAFT = "draft"
    VERIFIED = "verified"
    CONFLICT = "conflict"
    SUPERSEDED = "superseded"

class AnswerPolicy(str, enum.Enum):
    TRUTH_RECORD = "truth_record"
    NORMALIZED = "normalized"
    RAW = "raw"
    REFUSAL = "refusal"
    ESCALATE = "escalate"

class EscalationStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Tour(Base):
    __tablename__ = "tours"
    
    id = Column(String, primary_key=True)  # UUID
    tid = Column(String, unique=True, nullable=False, index=True)  # TID-TT-TOUR-XXXXX
    tour_name = Column(String, nullable=False)
    tour_code = Column(String, nullable=False, index=True)  # e.g., KOH26
    start_date = Column(DateTime(timezone=True))
    multi_tour_access = Column(Boolean, default=False)
    status = Column(String, default="active")  # active, archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    source_files = relationship("SourceFile", back_populates="tour", cascade="all, delete-orphan")
    truth_records = relationship("TruthRecord", back_populates="tour", cascade="all, delete-orphan")
    invocations = relationship("Invocation", back_populates="tour", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="tour", cascade="all, delete-orphan")

class SourceFile(Base):
    __tablename__ = "source_files"
    
    id = Column(String, primary_key=True)  # UUID
    taid = Column(String, unique=True, nullable=False, index=True)  # TAID-TT-SRC-XXXXX
    tour_id = Column(String, ForeignKey('tours.id'), nullable=False)
    
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # mastertour, eventbrite, onesheet, routing, settlement, etc.
    file_path = Column(String, nullable=False)  # Storage path/URL
    file_hash = Column(String)  # SHA256 for deduplication
    file_size = Column(Integer)
    mime_type = Column(String)
    
    # Metadata
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    # Extracted metadata
    extracted_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tour = relationship("Tour", back_populates="source_files")
    truth_records = relationship("TruthRecord", secondary=truth_record_sources, back_populates="source_files")

class TruthRecord(Base):
    __tablename__ = "truth_records"
    
    id = Column(String, primary_key=True)  # UUID
    taid = Column(String, unique=True, nullable=False, index=True)  # TAID-TT-TRUTH-XXXXX
    tour_id = Column(String, ForeignKey('tours.id'), nullable=False)
    
    record_type = Column(String, nullable=False)  # show, venue, vip, safety, finance, people
    schema_version = Column(String, default="1.0")
    record_status = Column(SQLEnum(RecordStatus), default=RecordStatus.DRAFT)
    
    # Core data
    data = Column(JSON, nullable=False)  # Canonical truth data
    
    # Confidence & Guardrails
    confidence = Column(Float, default=1.0)
    threshold_applied = Column(Float, default=0.8)
    
    # Financial guardrails (for settlement records)
    financial_guardrail = Column(JSON, nullable=True)  # {requires_confirmation, confirmation_status, conflict_flag}
    
    # Supersession chain
    supersedes_record_id = Column(String, ForeignKey('truth_records.id'), nullable=True)
    
    # Searchable fields
    search_keywords = Column(JSON, nullable=True)  # Array of keywords for fast lookup
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tour = relationship("Tour", back_populates="truth_records")
    source_files = relationship("SourceFile", secondary=truth_record_sources, back_populates="truth_records")

class Invocation(Base):
    __tablename__ = "invocations"
    
    id = Column(String, primary_key=True)  # UUID
    taid = Column(String, unique=True, nullable=False, index=True)  # TAID-TT-INV-XXXXX
    session_id = Column(String, nullable=False, index=True)
    tour_id = Column(String, ForeignKey('tours.id'), nullable=False)
    tour_code_at_time = Column(String, nullable=False)
    
    # User identification (hashed for privacy)
    phone_hash = Column(String, nullable=False, index=True)  # Never store raw phone
    
    # Query details
    query_text = Column(Text, nullable=False)
    query_intent = Column(String, nullable=True)  # Parsed intent
    
    # Answer chain
    answer_policy = Column(SQLEnum(AnswerPolicy), nullable=False)
    confidence = Column(Float, nullable=False)
    threshold_applied = Column(Float, default=0.8)
    
    # Response
    response_text = Column(Text, nullable=True)
    response_preview = Column(String(280), nullable=True)  # First 280 chars
    
    # TAID references
    truth_record_taids = Column(JSON, nullable=True)  # Array of TAIDs used
    source_taids = Column(JSON, nullable=True)  # Array of source TAIDs
    
    # Status
    status = Column(String, default="completed")  # completed, escalated, error
    
    # Performance
    latency_ms = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tour = relationship("Tour", back_populates="invocations")

class Escalation(Base):
    __tablename__ = "escalations"
    
    id = Column(String, primary_key=True)  # UUID
    taid = Column(String, unique=True, nullable=False, index=True)  # TAID-TT-TKT-XXXXX
    decision_taid = Column(String, nullable=True)  # TAI-D-TT-XXXXX (decision object)
    tour_id = Column(String, ForeignKey('tours.id'), nullable=False)
    
    # Escalation details
    escalation_type = Column(String, nullable=False)  # missing_info, conflict, low_confidence, financial_guardrail
    severity = Column(String, default="medium")  # low, medium, high, critical
    status = Column(SQLEnum(EscalationStatus), default=EscalationStatus.OPEN)
    
    # Context
    description = Column(Text, nullable=False)
    query_context = Column(JSON, nullable=True)  # Related invocation data
    
    # Assignment
    assigned_role = Column(String, nullable=True)  # PM, TM, Finance, Vendor
    assigned_to = Column(String, nullable=True)
    
    # SLA
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tour = relationship("Tour", back_populates="escalations")
