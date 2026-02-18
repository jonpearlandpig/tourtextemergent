# TourText™ v4.1 — Integration Setup Guide

**Status:** ✅ Core Infrastructure Complete — Ready for API Key Integration

---

## Current Status

### ✅ Completed
- Backend API (FastAPI + MongoDB)
- Frontend Admin App (React + Shadcn/UI)
- Public marketing site
- TAID provenance system
- Query processing pipeline
- Truth record system
- Escalation management
- File upload infrastructure
- Invocation logging (append-only)
- Phone number hashing (privacy)

### 🔧 Pending Integration (Requires API Keys)
- Twilio SMS
- OpenAI GPT-5.2
- Supabase Storage

---

## Step-by-Step Integration

### 1. Twilio SMS Integration

**Purpose:** Crew texts queries to TourText, receives instant answers

**Steps:**

1. **Create Twilio Account:**
   - Go to: https://www.twilio.com/try-twilio
   - Sign up (free trial available with $15 credit)

2. **Get Phone Number:**
   - In Twilio Console, go to Phone Numbers → Buy a Number
   - Select a US number (or your country)
   - Purchase number

3. **Get Credentials:**
   - In Twilio Console, go to Account → Dashboard
   - Copy:
     - Account SID: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
     - Auth Token: `your_auth_token_here`
     - Phone Number: `+1234567890` (from step 2)

4. **Add to Backend `.env`:**
   ```bash
   TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   TWILIO_AUTH_TOKEN="your_auth_token_here"
   TWILIO_PHONE_NUMBER="+1234567890"
   ```

5. **Configure Webhook:**
   - In Twilio Console, go to Phone Numbers → Active Numbers
   - Click your number
   - Under "Messaging", set:
     - Webhook URL: `https://your-app.com/api/sms/webhook`
     - Method: HTTP POST

6. **Test:**
   ```bash
   # Send test SMS from your phone to Twilio number
   # TourText should respond
   ```

**Estimated Cost:**
- $1/month for phone number
- $0.0075 per SMS sent (outbound)
- First $15 free with trial

---

### 2. OpenAI GPT Integration

**Purpose:** Intent parsing and natural language response formatting

**Steps:**

1. **Get API Key:**
   - Go to: https://platform.openai.com/api-keys
   - Create account or sign in
   - Click "Create new secret key"
   - Copy key: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

2. **Add to Backend `.env`:**
   ```bash
   OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

   **OR** Use Emergent LLM Key:
   ```bash
   EMERGENT_LLM_KEY="your_emergent_key"
   ```

3. **Restart Backend:**
   ```bash
   sudo supervisorctl restart backend
   ```

4. **Verify Integration:**
   ```bash
   curl http://localhost:8001/api/ | jq '.integrations.openai'
   # Should return: true
   ```

**Estimated Cost:**
- GPT-3.5 Turbo: $0.50 / 1M input tokens, $1.50 / 1M output tokens
- GPT-4: $30 / 1M input tokens, $60 / 1M output tokens
- Average query: ~$0.001 - $0.01 per query

---

### 3. Supabase Integration (Database + Storage)

**Purpose:** PostgreSQL database + S3-compatible file storage

**Option A: Use Supabase (Recommended)**

1. **Create Supabase Project:**
   - Go to: https://supabase.com
   - Create account
   - Create new project
   - Wait for setup (2-3 minutes)

2. **Get Database URL:**
   - In Supabase Dashboard, go to Settings → Database
   - Copy Connection String (URI format):
     ```
     postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
     ```

3. **Get Storage Credentials:**
   - In Supabase Dashboard, go to Settings → API
   - Copy:
     - Project URL: `https://[PROJECT_REF].supabase.co`
     - Service Role Key (secret): `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

4. **Create Storage Bucket:**
   - Go to Storage → Create Bucket
   - Name: `tourtext-files`
   - Public or Private (recommend private)

5. **Update Backend `.env`:**
   ```bash
   # Replace MongoDB with Postgres
   POSTGRES_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres"
   
   # Add Supabase Storage
   SUPABASE_URL="https://[PROJECT_REF].supabase.co"
   SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   SUPABASE_BUCKET="tourtext-files"
   ```

6. **Migrate to Postgres:**
   - Uncomment Postgres code in `server.py`
   - Comment out MongoDB code
   - Restart backend
   - Tables will auto-create

**Option B: Keep MongoDB (Current Setup)**

Continue using MongoDB for now. You can migrate to Postgres/Supabase later.

**Estimated Cost:**
- Supabase Free Tier: Up to 500MB database, 1GB storage
- Pro: $25/month (8GB database, 100GB storage)

---

## Quick Start After Integration

### 1. Restart Services

```bash
sudo supervisorctl restart backend
sudo supervisorctl restart frontend
```

### 2. Verify Integrations

```bash
curl http://localhost:8001/api/ | jq .
```

Expected output:
```json
{
  "message": "TourText API v4.1",
  "status": "operational",
  "integrations": {
    "twilio": true,
    "openai": true,
    "supabase": true
  }
}
```

### 3. Test Full Flow

1. **Open Frontend:**
   - Go to: `http://localhost:3000` (or your preview URL)

2. **Create Tour:**
   - Click "Start a Tour"
   - Fill in: Tour Name, Start Date
   - Click "Create Tour"

3. **Upload Files:**
   - Drag and drop Master Tour CSV or sample file
   - Click "Approve & Activate"

4. **Test Query:**
   - In Live Status screen, enter test query:
     - "What time is load-in tomorrow?"
   - Click "Send Test Query"
   - Should receive response

5. **Test SMS (if Twilio configured):**
   - Text your Twilio number: "What time is load-in?"
   - Should receive SMS response within 3 seconds

---

## Environment Variables Checklist

### Backend (`/app/backend/.env`)

```bash
# Database (choose one)
✅ MONGO_URL="mongodb://localhost:27017"  # Currently active
⬜ POSTGRES_URL="postgresql://..."        # For Supabase

# Core Config
✅ DB_NAME="tourtext"
✅ CORS_ORIGINS="*"

# Twilio SMS (Required for production)
⬜ TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxx"
⬜ TWILIO_AUTH_TOKEN="your_auth_token"
⬜ TWILIO_PHONE_NUMBER="+1234567890"

# OpenAI (Required for query processing)
⬜ OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxx"
# OR
⬜ EMERGENT_LLM_KEY="your_emergent_key"

# Supabase Storage (Optional, for file uploads)
⬜ SUPABASE_URL="https://[PROJECT_REF].supabase.co"
⬜ SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
⬜ SUPABASE_BUCKET="tourtext-files"
```

### Frontend (`/app/frontend/.env`)

```bash
✅ REACT_APP_BACKEND_URL=https://your-app.preview.emergentagent.com
✅ WDS_SOCKET_PORT=443
✅ ENABLE_HEALTH_CHECK=false
```

---

## Testing Integration

### Test Twilio

```bash
# Check backend logs after sending SMS
tail -f /var/log/supervisor/backend.*.log | grep SMS
```

### Test OpenAI

```bash
# Test query endpoint
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "tour_code": "TEST26",
    "query": "What is the venue address for tomorrow?",
    "phone_number": "+1234567890"
  }' | jq .
```

### Test File Upload

```bash
# Create test file
echo "show_date,venue,load_in_time
2026-03-15,Madison Square Garden,10:00 AM" > test_tour.csv

# Upload via API
curl -X POST "http://localhost:8001/api/tours/{TOUR_ID}/upload" \
  -F "file=@test_tour.csv" \
  -F "file_type=mastertour"
```

---

## Common Issues & Fixes

### Issue: Twilio SMS not working

**Solution:**
1. Check webhook URL is publicly accessible
2. Verify webhook method is POST
3. Check Twilio console for error logs
4. Ensure phone number is not on DND list

### Issue: OpenAI rate limit errors

**Solution:**
1. Check API key has credits
2. Implement rate limiting in code
3. Upgrade to paid tier if needed

### Issue: File uploads failing

**Solution:**
1. Check Supabase bucket permissions
2. Verify service role key (not anon key)
3. Check file size limits
4. Fallback to local storage if needed

---

## Cost Estimation (Monthly)

### Minimal Setup (Testing)
- Twilio: $1 (phone number) + ~$5 (SMS)
- OpenAI: ~$10 (testing queries)
- Database: Free (MongoDB local or Supabase free tier)
- **Total: ~$16/month**

### Production Setup (Small Tour)
- Twilio: $1 + $50 (1000 SMS/day)
- OpenAI: $100 (10,000 queries)
- Supabase: $25 (Pro tier)
- **Total: ~$176/month**

### Production Setup (Large Tour)
- Twilio: $1 + $150 (3000 SMS/day)
- OpenAI: $500 (50,000 queries)
- Supabase: $25
- **Total: ~$676/month**

---

## Next Steps

1. **Add API Keys** (follow guides above)
2. **Test Integrations** (use test scripts)
3. **Create Sample Tour** (use admin interface)
4. **Upload Test Data** (Master Tour CSV)
5. **Test Query Flow** (SMS or web interface)
6. **Monitor Logs** (check for errors)
7. **Adjust Thresholds** (confidence, escalation rules)

---

## Support

**File Locations:**
- Backend code: `/app/backend/server.py`
- Frontend code: `/app/frontend/src/`
- Environment: `/app/backend/.env`, `/app/frontend/.env`
- Logs: `/var/log/supervisor/backend.*.log`

**Useful Commands:**
```bash
# Restart services
sudo supervisorctl restart all

# Check status
sudo supervisorctl status

# View backend logs
tail -f /var/log/supervisor/backend.*.log

# Test API
curl http://localhost:8001/api/health
```

---

**TourText™ v4.1 — Ready for Production with API Keys**
