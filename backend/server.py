from fastapi import FastAPI, APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import time
from datetime import datetime, timezone

# Import utilities
from utils import (
    generate_taid, generate_uuid, generate_session_id,
    hash_phone_number, hash_file, generate_tour_code
)
from integrations import twilio_client, openai_processor, supabase_storage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (easy to migrate to Postgres/Supabase later)
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'tourtext')]

# Create the main app
app = FastAPI(title="TourText API", version="4.1")

# Create API router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TourCreate(BaseModel):
    tour_name: str
    tour_code: Optional[str] = None
    start_date: str
    multi_tour_access: bool = False

class SourceFileUpload(BaseModel):
    file_type: str

class QueryRequest(BaseModel):
    tour_code: str
    query: str
    phone_number: Optional[str] = None

# ============================================================================
# HEALTH CHECK
# ============================================================================

@api_router.get("/")
async def root():
    return {
        "message": "TourText API v4.1",
        "status": "operational",
        "integrations": {
            "twilio": twilio_client.enabled,
            "openai": openai_processor.enabled,
            "supabase": supabase_storage.enabled
        }
    }

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# ============================================================================
# TOUR ENDPOINTS
# ============================================================================

@api_router.post("/tours")
async def create_tour(tour: TourCreate):
    """Create new tour"""
    try:
        # Generate IDs
        tour_id = generate_uuid()
        tid = generate_taid("TID-TT-TOUR")
        
        # Generate tour code if not provided
        if not tour.tour_code:
            tour.tour_code = generate_tour_code(tour.tour_name)
        
        # Create tour document
        tour_doc = {
            "id": tour_id,
            "tid": tid,
            "tour_name": tour.tour_name,
            "tour_code": tour.tour_code,
            "start_date": tour.start_date,
            "multi_tour_access": tour.multi_tour_access,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None
        }
        
        await db.tours.insert_one(tour_doc)
        
        logger.info(f"Created tour: {tid} ({tour.tour_code})")
        
        # Remove MongoDB _id before returning
        tour_doc.pop('_id', None)
        return tour_doc
    
    except Exception as e:
        logger.error(f"Failed to create tour: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tours")
async def list_tours():
    """List all active tours"""
    try:
        tours = await db.tours.find({"status": "active"}, {"_id": 0}).sort("created_at", -1).to_list(100)
        return tours
    except Exception as e:
        logger.error(f"Failed to list tours: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tours/{tour_id}")
async def get_tour(tour_id: str):
    """Get tour by ID"""
    tour = await db.tours.find_one({"id": tour_id}, {"_id": 0})
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return tour

# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

@api_router.post("/tours/{tour_id}/upload")
async def upload_file(
    tour_id: str,
    file: UploadFile = File(...),
    file_type: str = Form(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload source file (Master Tour, Eventbrite, PDF, etc.)
    """
    try:
        # Verify tour exists
        tour = await db.tours.find_one({"id": tour_id})
        if not tour:
            raise HTTPException(status_code=404, detail="Tour not found")
        
        # Read file content
        file_content = await file.read()
        file_hash_str = hash_file(file_content)
        
        # Check for duplicate
        existing = await db.source_files.find_one({
            "tour_id": tour_id,
            "file_hash": file_hash_str
        })
        
        if existing:
            logger.warning(f"Duplicate file detected: {file.filename}")
            existing.pop('_id', None)
            return existing
        
        # Generate IDs
        file_id = generate_uuid()
        taid = generate_taid("TAID-TT-SRC")
        
        # Upload to storage
        storage_path = f"tours/{tour['tour_code']}/{file_type}/{file.filename}"
        file_url = await supabase_storage.upload_file(storage_path, file_content, file.content_type or "application/octet-stream")
        
        # Create source file record
        file_doc = {
            "id": file_id,
            "taid": taid,
            "tour_id": tour_id,
            "file_name": file.filename,
            "file_type": file_type,
            "file_path": file_url or storage_path,
            "file_hash": file_hash_str,
            "file_size": len(file_content),
            "mime_type": file.content_type,
            "upload_date": datetime.now(timezone.utc).isoformat(),
            "processed": False,
            "processing_error": None,
            "extracted_metadata": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.source_files.insert_one(file_doc)
        
        logger.info(f"Uploaded file: {taid} ({file.filename})")
        
        # Process file in background
        if background_tasks:
            background_tasks.add_task(process_uploaded_file, file_id, file_content)
        
        file_doc.pop('_id', None)
        return file_doc
    
    except Exception as e:
        logger.error(f"Failed to upload file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tours/{tour_id}/files")
async def list_tour_files(tour_id: str):
    """List all files for a tour"""
    files = await db.source_files.find({"tour_id": tour_id}, {"_id": 0}).sort("upload_date", -1).to_list(100)
    return files

# ============================================================================
# TRUTH RECORD ENDPOINTS
# ============================================================================

@api_router.post("/truth-records")
async def create_truth_record(
    tour_id: str = Form(...),
    record_type: str = Form(...),
    data: str = Form(...),  # JSON string
    source_file_ids: str = Form(...),  # JSON array string
    confidence: float = Form(1.0),
    threshold_applied: float = Form(0.8)
):
    """Create truth record"""
    try:
        import json
        
        # Generate IDs
        record_id = generate_uuid()
        taid = generate_taid("TAID-TT-TRUTH")
        
        # Parse JSON strings
        data_obj = json.loads(data)
        source_ids = json.loads(source_file_ids)
        
        # Create truth record
        record_doc = {
            "id": record_id,
            "taid": taid,
            "tour_id": tour_id,
            "record_type": record_type,
            "schema_version": "1.0",
            "record_status": "draft",
            "data": data_obj,
            "confidence": confidence,
            "threshold_applied": threshold_applied,
            "source_file_ids": source_ids,
            "search_keywords": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None
        }
        
        await db.truth_records.insert_one(record_doc)
        
        logger.info(f"Created truth record: {taid} (type: {record_type})")
        
        record_doc.pop('_id', None)
        return record_doc
    
    except Exception as e:
        logger.error(f"Failed to create truth record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tours/{tour_id}/truth-records")
async def list_truth_records(tour_id: str, record_type: Optional[str] = None):
    """List truth records for a tour"""
    query = {"tour_id": tour_id}
    if record_type:
        query["record_type"] = record_type
    
    records = await db.truth_records.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return records

# ============================================================================
# QUERY PROCESSING ENDPOINT
# ============================================================================

@api_router.post("/query")
async def process_query(query_req: QueryRequest):
    """
    Process crew query (SMS or web interface)
    
    Pipeline: Parse Intent → Retrieve Truth → Guardrail Check → Format → Respond → Log
    """
    start_time = time.time()
    
    try:
        # Find tour
        tour = await db.tours.find_one({"tour_code": query_req.tour_code})
        if not tour:
            raise HTTPException(status_code=404, detail=f"Tour not found: {query_req.tour_code}")
        
        # Generate session
        session_id = generate_session_id()
        phone_hash = hash_phone_number(query_req.phone_number) if query_req.phone_number else "web-interface"
        
        # Step 1: Parse intent
        intent_data = await openai_processor.parse_intent(query_req.query)
        keywords = intent_data.get("keywords", [])
        
        # Step 2: Retrieve truth records
        truth_records = await db.truth_records.find({
            "tour_id": tour["id"],
            "record_status": {"$in": ["verified", "draft"]}
        }).to_list(100)
        
        # Simple keyword matching
        matched_records = []
        for record in truth_records:
            record_keywords = record.get("search_keywords", [])
            record_text = str(record.get("data", "")).lower()
            
            # Match keywords in data or search_keywords
            if any(kw.lower() in record_text for kw in keywords):
                matched_records.append(record)
        
        # Step 3: Determine answer policy
        if matched_records:
            best_record = max(matched_records, key=lambda r: r.get("confidence", 0))
            
            confidence = best_record.get("confidence", 1.0)
            threshold = best_record.get("threshold_applied", 0.8)
            
            if confidence >= threshold:
                answer_policy = "truth_record"
                response_text = await openai_processor.format_response(best_record["data"], query_req.query)
                truth_taids = [best_record["taid"]]
            else:
                # Low confidence → escalate
                answer_policy = "escalate"
                response_text = "I found information but I'm not confident. Escalating to team."
                truth_taids = [best_record["taid"]]
                
                # Create escalation
                await db.escalations.insert_one({
                    "id": generate_uuid(),
                    "taid": generate_taid("TAID-TT-TKT"),
                    "tour_id": tour["id"],
                    "escalation_type": "low_confidence",
                    "severity": "medium",
                    "status": "open",
                    "description": f"Low confidence query: {query_req.query}",
                    "query_context": {"query": query_req.query, "confidence": confidence},
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
        else:
            # No match → refusal
            answer_policy = "refusal"
            response_text = "I don't have information about that. Please contact your Tour Manager."
            confidence = 0.0
            truth_taids = []
            
            # Create escalation
            await db.escalations.insert_one({
                "id": generate_uuid(),
                "taid": generate_taid("TAID-TT-TKT"),
                "tour_id": tour["id"],
                "escalation_type": "missing_info",
                "severity": "low",
                "status": "open",
                "description": f"No information found: {query_req.query}",
                "query_context": {"query": query_req.query},
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        # Step 4: Log invocation (append-only)
        latency_ms = int((time.time() - start_time) * 1000)
        
        invocation_doc = {
            "id": generate_uuid(),
            "taid": generate_taid("TAID-TT-INV"),
            "session_id": session_id,
            "tour_id": tour["id"],
            "tour_code_at_time": tour["tour_code"],
            "phone_hash": phone_hash,
            "query_text": query_req.query,
            "query_intent": intent_data.get("intent"),
            "answer_policy": answer_policy,
            "confidence": confidence,
            "threshold_applied": 0.8,
            "response_text": response_text,
            "response_preview": response_text[:280] if response_text else None,
            "truth_record_taids": truth_taids,
            "status": "completed",
            "latency_ms": latency_ms,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.invocations.insert_one(invocation_doc)
        
        logger.info(f"Processed query: {invocation_doc['taid']} (policy: {answer_policy}, latency: {latency_ms}ms)")
        
        return {
            "response": response_text,
            "confidence": confidence,
            "answer_policy": answer_policy,
            "truth_record_taids": truth_taids,
            "session_id": session_id,
            "invocation_taid": invocation_doc["taid"]
        }
    
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# INVOCATION LOG ENDPOINTS
# ============================================================================

@api_router.get("/tours/{tour_id}/invocations")
async def list_invocations(tour_id: str, limit: int = 100):
    """List recent invocations for a tour"""
    invocations = await db.invocations.find(
        {"tour_id": tour_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    return invocations

# ============================================================================
# ESCALATION ENDPOINTS
# ============================================================================

@api_router.get("/tours/{tour_id}/escalations")
async def list_escalations(tour_id: str, status: Optional[str] = None):
    """List escalations for a tour"""
    query = {"tour_id": tour_id}
    if status:
        query["status"] = status
    
    escalations = await db.escalations.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return escalations

# ============================================================================
# SMS WEBHOOK ENDPOINT (Twilio)
# ============================================================================

@api_router.post("/sms/webhook")
async def sms_webhook(From: str = Form(...), Body: str = Form(...), MessageSid: str = Form(...)):
    """Twilio SMS webhook handler"""
    try:
        logger.info(f"SMS received from {From[:4]}***: {Body}")
        
        # For now, use a default tour (in production: implement tour detection)
        # Could be based on phone number mapping or message prefix
        tours = await db.tours.find({"status": "active"}, {"_id": 0}).limit(1).to_list(1)
        
        if not tours:
            await twilio_client.send_sms(From, "No active tours found. Please contact admin.")
            return {"status": "error", "message": "No active tours"}
        
        tour_code = tours[0]["tour_code"]
        
        # Process query
        query_response = await process_query(
            QueryRequest(
                tour_code=tour_code,
                query=Body,
                phone_number=From
            )
        )
        
        # Send SMS response
        await twilio_client.send_sms(From, query_response["response"])
        
        return {"status": "success", "invocation_taid": query_response["invocation_taid"]}
    
    except Exception as e:
        logger.error(f"SMS webhook failed: {str(e)}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================

async def process_uploaded_file(file_id: str, file_content: bytes):
    """Background task: Process uploaded file and create truth records"""
    try:
        file = await db.source_files.find_one({"id": file_id})
        if not file:
            return
        
        logger.info(f"Processing file: {file['taid']}")
        
        # Placeholder: In production, implement actual parsing logic
        # - Use pandas for CSV/Excel
        # - Use pdfplumber for PDFs
        # - Create TruthRecord objects
        
        await db.source_files.update_one(
            {"id": file_id},
            {"$set": {"processed": True}}
        )
        
        logger.info(f"File processed: {file['taid']}")
    
    except Exception as e:
        logger.error(f"File processing failed: {str(e)}")
        await db.source_files.update_one(
            {"id": file_id},
            {"$set": {"processing_error": str(e)}}
        )

# ============================================================================
# INCLUDE ROUTER & MIDDLEWARE
# ============================================================================

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# SHUTDOWN HANDLER
# ============================================================================

@app.on_event("shutdown")
async def shutdown():
    client.close()
    logger.info("TourText API shutting down")
