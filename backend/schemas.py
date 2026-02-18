from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from models import RecordStatus, AnswerPolicy, EscalationStatus

# ============================================================================
# TOUR SCHEMAS
# ============================================================================

class TourCreate(BaseModel):
    tour_name: str
    tour_code: Optional[str] = None  # Auto-generated if not provided
    start_date: datetime
    multi_tour_access: bool = False

class TourResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    tid: str
    tour_name: str
    tour_code: str
    start_date: datetime
    multi_tour_access: bool
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

# ============================================================================
# SOURCE FILE SCHEMAS
# ============================================================================

class SourceFileCreate(BaseModel):
    tour_id: str
    file_name: str
    file_type: str  # mastertour, eventbrite, onesheet, routing, settlement, etc.
    file_content: bytes = Field(exclude=True)  # Not included in response

class SourceFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    taid: str
    tour_id: str
    file_name: str
    file_type: str
    file_path: str
    file_hash: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    upload_date: datetime
    processed: bool
    processing_error: Optional[str] = None
    extracted_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

# ============================================================================
# TRUTH RECORD SCHEMAS
# ============================================================================

class TruthRecordCreate(BaseModel):
    tour_id: str
    record_type: str  # show, venue, vip, safety, finance, people
    data: Dict[str, Any]
    source_file_ids: List[str]  # Array of source file IDs
    confidence: float = 1.0
    threshold_applied: float = 0.8
    search_keywords: Optional[List[str]] = None

class TruthRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    taid: str
    tour_id: str
    record_type: str
    schema_version: str
    record_status: RecordStatus
    data: Dict[str, Any]
    confidence: float
    threshold_applied: float
    financial_guardrail: Optional[Dict[str, Any]] = None
    supersedes_record_id: Optional[str] = None
    search_keywords: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class TruthRecordUpdate(BaseModel):
    record_status: Optional[RecordStatus] = None
    data: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None

# ============================================================================
# INVOCATION SCHEMAS
# ============================================================================

class InvocationCreate(BaseModel):
    tour_id: str
    phone_number: str  # Will be hashed before storage
    query_text: str

class InvocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    taid: str
    session_id: str
    tour_id: str
    tour_code_at_time: str
    phone_hash: str
    query_text: str
    query_intent: Optional[str] = None
    answer_policy: AnswerPolicy
    confidence: float
    threshold_applied: float
    response_text: Optional[str] = None
    response_preview: Optional[str] = None
    truth_record_taids: Optional[List[str]] = None
    source_taids: Optional[List[str]] = None
    status: str
    latency_ms: Optional[int] = None
    created_at: datetime

# ============================================================================
# ESCALATION SCHEMAS
# ============================================================================

class EscalationCreate(BaseModel):
    tour_id: str
    escalation_type: str  # missing_info, conflict, low_confidence, financial_guardrail
    severity: str = "medium"
    description: str
    query_context: Optional[Dict[str, Any]] = None
    assigned_role: Optional[str] = None

class EscalationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    taid: str
    decision_taid: Optional[str] = None
    tour_id: str
    escalation_type: str
    severity: str
    status: EscalationStatus
    description: str
    query_context: Optional[Dict[str, Any]] = None
    assigned_role: Optional[str] = None
    assigned_to: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class EscalationUpdate(BaseModel):
    status: Optional[EscalationStatus] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None

# ============================================================================
# SMS WEBHOOK SCHEMA
# ============================================================================

class SMSWebhook(BaseModel):
    """Twilio SMS webhook payload"""
    From: str  # Phone number
    Body: str  # Message text
    MessageSid: str
    AccountSid: str

# ============================================================================
# QUERY PROCESSING SCHEMA
# ============================================================================

class QueryRequest(BaseModel):
    tour_code: str
    query: str
    phone_number: Optional[str] = None  # For session tracking

class QueryResponse(BaseModel):
    response: str
    confidence: float
    answer_policy: str
    truth_record_taids: List[str]
    session_id: str
    invocation_taid: str
