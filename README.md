# TourText™ v4.1 — Infrastructure-Grade Tour Information System

**TID:** TID-TT-V4-001  
**Version:** v4.1  
**Status:** Production-Ready Infrastructure (Pending API Keys)

---

## Overview

TourText is an SMS-first tour information system that makes tour data instantly usable under pressure. It activates existing systems (Master Tour, Eventbrite) without replacing them.

**Core Philosophy:**
- **Not a chatbot** — Retrieves verified information, not guesses
- **Not a replacement** — Activates your existing Master Tour system
- **Zero behavior change** — If it feels like an extra step, it has failed

---

## Architecture Stack

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (Supabase recommended)
- **Storage:** S3-compatible (Supabase Storage)
- **SMS:** Twilio
- **LLM:** OpenAI GPT-5.2 (intent parsing & formatting only)

### Frontend
- **Framework:** React 19
- **UI Library:** Shadcn/UI (Radix UI + Tailwind CSS)
- **Routing:** React Router v7
- **State:** React hooks

### Telauthorium Provenance
All critical artifacts generate TAID identifiers for audit traceability:
- `TID-TT-TOUR-XXXXX` — Tour creation
- `TAID-TT-SRC-XXXXX` — Source file import
- `TAID-TT-TRUTH-XXXXX` — Truth record
- `TAID-TT-INV-XXXXX` — Query invocation
- `TAID-TT-TKT-XXXXX` — Escalation ticket

---

## 60-Second Activation Path

1. **Export** Master Tour data (zero behavior change)
2. **Upload** to TourText (drag & drop)
3. **Live** — Text to test, instant answers

If activation takes >90 seconds, something is broken.

---

## Installation & Setup

### Prerequisites
- Node.js 18+ and Yarn
- Python 3.11+
- PostgreSQL database (or Supabase account)
- Twilio account (for SMS)
- OpenAI API key (or Emergent LLM key)

### 1. Clone & Install

```bash
# Backend
cd /app/backend
pip install -r requirements.txt

# Frontend
cd /app/frontend
yarn install
```

### 2. Configure Environment Variables

#### Backend (`/app/backend/.env`)

```bash
# Database
POSTGRES_URL="postgresql://user:password@host:port/database"
# OR use Supabase:
# POSTGRES_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres"

CORS_ORIGINS="*"

# Twilio SMS (Required for production)
# Get from: https://console.twilio.com
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="your_auth_token"
TWILIO_PHONE_NUMBER="+1234567890"

# OpenAI (Required for query processing)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# OR use Emergent LLM key:
# EMERGENT_LLM_KEY="your_emergent_key"

# Supabase Storage (Required for file uploads)
# Get from: https://supabase.com/dashboard/project/_/settings/api
SUPABASE_URL="https://[PROJECT_REF].supabase.co"
SUPABASE_KEY="your_service_role_key"
SUPABASE_BUCKET="tourtext-files"
```

#### Frontend (`/app/frontend/.env`)

```bash
REACT_APP_BACKEND_URL=https://your-app.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

### 3. Database Setup

The backend will automatically create tables on first run. Alternatively, use Alembic for migrations:

```bash
cd /app/backend
alembic init alembic  # First time only
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### 4. Start Services

#### Development (Supervisor)

```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

#### Manual Start (Development Only)

```bash
# Backend
cd /app/backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd /app/frontend
yarn start
```

---

## API Integration Guide

### Required API Keys

#### 1. Twilio SMS

**Purpose:** Crew texts queries, TourText responds via SMS  
**Get Keys:** https://console.twilio.com

1. Create Twilio account
2. Get a phone number
3. Copy Account SID, Auth Token, Phone Number
4. Add to `/app/backend/.env`

**Webhook Setup:**
- Set incoming SMS webhook to: `https://your-app.com/api/sms/webhook`
- Method: POST

#### 2. OpenAI API

**Purpose:** Intent parsing and response formatting (NOT decision-making)  
**Get Key:** https://platform.openai.com/api-keys

1. Create OpenAI account
2. Generate API key
3. Add to `/app/backend/.env` as `OPENAI_API_KEY`

**Alternative:** Use `EMERGENT_LLM_KEY` (contact Emergent support)

#### 3. Supabase (Database + Storage)

**Purpose:** PostgreSQL database + S3-compatible file storage  
**Get Keys:** https://supabase.com

1. Create Supabase project
2. Go to Settings > API
3. Copy `SUPABASE_URL` and service role key
4. Create storage bucket named `tourtext-files` (public or private)
5. Add credentials to `/app/backend/.env`

**Alternative:** Use any PostgreSQL database + S3-compatible storage

---

## Frontend Structure (3-Screen Admin App)

### Screen 1: Tour Select (`/admin`)
- Create new tour or select existing
- Fields: Tour Name, Tour Code, Start Date, Multi-Tour Access
- Generates `TID-TT-TOUR-XXXXX`

### Screen 2: Upload (`/admin/upload`)
- Drag-and-drop file upload
- Supported: Master Tour (CSV/Excel), Eventbrite, PDFs
- Auto-detects categories: Shows, Venues, VIP, Finance, etc.
- Generates `TAID-TT-SRC-XXXXX` per file
- "Approve & Activate" → Go Live

### Screen 3: Live Status (`/admin/live`)
- Test query interface (simulates SMS)
- Recent queries with confidence scores
- Escalations (missing info, low confidence, financial guardrails)
- Invocation log (audit trail)

---

## Query Processing Pipeline

**Deterministic Flow:**

```
SMS/Web Query
  ↓
Parse Intent (OpenAI)
  ↓
Retrieve Truth Records (Database)
  ↓
Guardrail Check (Finance, Confidence)
  ↓
Format Response (OpenAI)
  ↓
Send Response (Twilio SMS)
  ↓
Log Invocation (Append-Only, TAID-TT-INV)
```

**Answer Policy Hierarchy:**
1. **Truth Record** — Verified canonical data (preferred)
2. **Normalized** — Extracted structured data
3. **Raw** — Source file reference
4. **Refusal** — No information found
5. **Escalate** — Low confidence or missing data

**Critical Rules:**
- LLM **NEVER** decides truth or finance
- All financial queries require guardrail confirmation
- Confidence < threshold → escalate
- Append-only invocation logs (no updates/deletes)

---

## Truth Record System

### Many-to-Many Source Mapping

One Master Tour export can generate multiple truth records:
- Show records (one per date)
- Venue records
- VIP records
- Contact directory

Each truth record links to source file(s) via `truth_record_sources` junction table.

### Required Truth Record Fields

```json
{
  "id": "uuid",
  "taid": "TAID-TT-TRUTH-XXXXX",
  "tour_id": "tour_uuid",
  "record_type": "show|venue|vip|safety|finance|people",
  "schema_version": "1.0",
  "record_status": "draft|verified|conflict|superseded",
  "data": { /* canonical truth data */ },
  "confidence": 0.95,
  "threshold_applied": 0.8,
  "source_taids": ["TAID-TT-SRC-XXXXX"],
  "supersedes_record_id": null,
  "created_at": "2026-02-18T10:00:00Z"
}
```

### Financial Guardrails

Settlement records **MUST** include:

```json
{
  "financial_guardrail": {
    "requires_confirmation": true,
    "confirmation_status": "pending|confirmed|locked",
    "conflict_flag": false
  }
}
```

No settlement answer may be returned without confirmed guardrail status.

---

## Escalation System

### Escalation Types

1. **missing_info** — Query has no matching truth records
2. **conflict** — Multiple conflicting sources
3. **low_confidence** — Confidence below threshold
4. **financial_guardrail** — Finance query requires confirmation

### Escalation Flow

1. System detects issue
2. Generates `TAID-TT-TKT-XXXXX`
3. Creates decision object `TAI-D-TT-XXXXX` (for finance)
4. Assigns to role (PM/TM/Finance/Vendor)
5. Sets SLA deadline
6. Crew receives refusal message
7. Responsible party resolves
8. Truth record updated with supersession chain

---

## Testing

### Backend API Tests

```bash
# Health check
curl http://localhost:8001/api/health

# Create tour
curl -X POST http://localhost:8001/api/tours \
  -H "Content-Type: application/json" \
  -d '{
    "tour_name": "Test Tour 2026",
    "start_date": "2026-03-01T00:00:00Z"
  }'

# Test query
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "tour_code": "TEST26",
    "query": "What time is load-in tomorrow?",
    "phone_number": "+1234567890"
  }'
```

### Frontend Testing

1. Navigate to `http://localhost:3000`
2. Public site should render
3. Click "Start a Tour" → Admin interface
4. Create test tour
5. Upload sample CSV file
6. Activate and test query

---

## File Processing (Background Tasks)

When files are uploaded:

1. **Immediate:**
   - File stored in Supabase Storage
   - Metadata saved to `source_files` table
   - `TAID-TT-SRC-XXXXX` generated

2. **Background (async):**
   - Parse CSV/Excel with Pandas
   - Extract PDF text with pdfplumber
   - Create truth records
   - Link via `truth_record_sources`
   - Set `processed = True`

### Supported File Types

| Type | Description | Library |
|------|-------------|---------|
| Master Tour | Primary tour data | pandas |
| Eventbrite | VIP/ticketing | pandas |
| One Sheet | PDF overview | pdfplumber |
| Routing | Travel logistics | pdfplumber |
| Settlement | Financial data | pandas/pdfplumber |
| Tech Pack | Venue specs | pdfplumber |

---

## Security & Privacy

### Phone Number Hashing

**CRITICAL:** Never store raw phone numbers in invocation logs.

```python
from utils import hash_phone_number

phone_hash = hash_phone_number("+1234567890")
# Stores SHA256 hash only
```

### Row-Level Security (Supabase)

Enable RLS on all tables to enforce multi-tour isolation:

```sql
ALTER TABLE tours ENABLE ROW LEVEL SECURITY;
ALTER TABLE truth_records ENABLE ROW LEVEL SECURITY;
-- etc.
```

### Append-Only Logs

Invocation table has **NO UPDATE OR DELETE** operations:
- All logs are immutable
- Audit trail preserved
- Compliance-ready

---

## Deployment

### Environment Variables (Production)

Ensure all required keys are set:

```bash
# Check backend
cat /app/backend/.env | grep -E "TWILIO|OPENAI|SUPABASE|POSTGRES"

# Check frontend
cat /app/frontend/.env | grep REACT_APP_BACKEND_URL
```

### Supervisor Configuration

Supervisor manages both services:

```bash
sudo supervisorctl status
# backend                          RUNNING
# frontend                         RUNNING
```

### Health Monitoring

```bash
# Backend health
curl https://your-app.com/api/health

# Integration status
curl https://your-app.com/api/ | jq '.integrations'
```

---

## Troubleshooting

### Issue: SMS not sending

**Check:**
1. Twilio credentials in `.env`
2. Backend logs: `tail -f /var/log/supervisor/backend.*.log`
3. Twilio console for errors
4. Webhook URL configured correctly

### Issue: Query processing fails

**Check:**
1. OpenAI API key valid
2. Database connection working
3. Truth records exist for tour
4. Backend logs for errors

### Issue: File upload fails

**Check:**
1. Supabase credentials configured
2. Storage bucket exists and accessible
3. File size within limits
4. Backend has write permissions

### Issue: Frontend not connecting to backend

**Check:**
1. `REACT_APP_BACKEND_URL` in frontend `.env`
2. Backend running on correct port (8001)
3. CORS configured in backend
4. Network requests in browser console

---

## Roadmap

### Phase 1 (Current)
- ✅ Admin web interface (3 screens)
- ✅ SMS integration (Twilio)
- ✅ Truth record system
- ✅ Query processing pipeline
- ✅ Escalation management
- ✅ Telauthorium provenance (TAID)

### Phase 2 (Future)
- Radio Comms (walkie-talkie integration)
- Offline mode (local AKB snapshots)
- Multi-channel department isolation
- Advanced analytics dashboard
- Mobile app (native)

---

## Support & Contact

**TourText™ v4.1**  
Pearl & Pig — Founder & Architect  
GoGarvis Runtime + Telauthorium Provenance

For integration support or questions:
- Check backend logs: `/var/log/supervisor/backend.*.log`
- Check frontend logs: Browser console
- Review API responses for error details

---

## License

TourText™ is proprietary software.  
All rights reserved.

---

**End of Documentation**
