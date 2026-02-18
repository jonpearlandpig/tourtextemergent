import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TWILIO SMS INTEGRATION
# ============================================================================

class TwilioSMS:
    """
    Twilio SMS integration for crew queries
    
    Required environment variables:
    - TWILIO_ACCOUNT_SID
    - TWILIO_AUTH_TOKEN
    - TWILIO_PHONE_NUMBER
    """
    
    def __init__(self):
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.phone_number = os.environ.get('TWILIO_PHONE_NUMBER', '')
        self.enabled = all([self.account_sid, self.auth_token, self.phone_number])
        
        if self.enabled:
            from twilio.rest import Client
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio SMS integration enabled")
        else:
            logger.warning("Twilio SMS integration disabled - missing credentials")
    
    async def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        Send SMS message
        
        Args:
            to_phone: Recipient phone number (E.164 format)
            message: Message text (max 1600 chars)
        
        Returns:
            Response dict with status
        """
        if not self.enabled:
            logger.warning(f"SMS not sent (Twilio disabled): {to_phone[:4]}***")
            return {"status": "disabled", "message": "Twilio credentials not configured"}
        
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_phone
            )
            logger.info(f"SMS sent successfully: {msg.sid}")
            return {"status": "success", "sid": msg.sid}
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return {"status": "error", "message": str(e)}

# ============================================================================
# OPENAI GPT INTEGRATION
# ============================================================================

class OpenAIProcessor:
    """
    OpenAI GPT-5.2 integration for query processing
    
    CRITICAL: LLM ONLY used for:
    - Intent parsing
    - Answer formatting
    - Natural language response generation
    
    LLM NEVER decides:
    - Truth
    - Finance
    - Conflict resolution
    
    Required environment variables:
    - OPENAI_API_KEY (or use EMERGENT_LLM_KEY)
    """
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY', '') or os.environ.get('EMERGENT_LLM_KEY', '')
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            import openai
            openai.api_key = self.api_key
            self.client = openai
            logger.info("OpenAI integration enabled")
        else:
            logger.warning("OpenAI integration disabled - missing API key")
    
    async def parse_intent(self, query: str) -> Dict[str, Any]:
        """
        Parse user query intent
        
        Args:
            query: User query text
        
        Returns:
            Dict with intent, entities, and search keywords
        """
        if not self.enabled:
            logger.warning("OpenAI disabled - returning basic intent")
            return {
                "intent": "general_query",
                "entities": [],
                "keywords": query.lower().split()
            }
        
        try:
            # Use GPT to parse intent (implementation placeholder)
            # In production: call OpenAI API with structured prompt
            return {
                "intent": "parsed_intent",
                "entities": [],
                "keywords": query.lower().split()
            }
        except Exception as e:
            logger.error(f"Failed to parse intent: {str(e)}")
            return {
                "intent": "error",
                "entities": [],
                "keywords": query.lower().split()
            }
    
    async def format_response(self, truth_data: Dict[str, Any], query: str) -> str:
        """
        Format truth data into natural language response
        
        Args:
            truth_data: Retrieved truth record data
            query: Original user query
        
        Returns:
            Natural language response string
        """
        if not self.enabled:
            logger.warning("OpenAI disabled - returning raw data")
            return str(truth_data)
        
        try:
            # Use GPT to format response (implementation placeholder)
            # In production: call OpenAI API with formatting prompt
            return f"Response based on truth records: {truth_data}"
        except Exception as e:
            logger.error(f"Failed to format response: {str(e)}")
            return "Error formatting response. Please contact admin."

# ============================================================================
# SUPABASE STORAGE INTEGRATION
# ============================================================================

class SupabaseStorage:
    """
    Supabase Storage for file uploads
    
    Required environment variables:
    - SUPABASE_URL
    - SUPABASE_KEY (service role key)
    - SUPABASE_BUCKET (storage bucket name)
    """
    
    def __init__(self):
        self.url = os.environ.get('SUPABASE_URL', '')
        self.key = os.environ.get('SUPABASE_KEY', '')
        self.bucket = os.environ.get('SUPABASE_BUCKET', 'tourtext-files')
        self.enabled = all([self.url, self.key])
        
        if self.enabled:
            logger.info("Supabase Storage integration enabled")
        else:
            logger.warning("Supabase Storage disabled - missing credentials")
    
    async def upload_file(self, file_path: str, file_content: bytes, content_type: str) -> Optional[str]:
        """
        Upload file to Supabase Storage
        
        Args:
            file_path: Path within bucket (e.g., 'tours/KOH26/mastertour.csv')
            file_content: File bytes
            content_type: MIME type
        
        Returns:
            Public URL of uploaded file or None
        """
        if not self.enabled:
            logger.warning(f"File upload skipped (Supabase disabled): {file_path}")
            # Fallback: save locally
            local_path = f"/tmp/tourtext_files/{file_path}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, 'wb') as f:
                f.write(file_content)
            return local_path
        
        try:
            # Implementation placeholder
            # In production: use Supabase Storage SDK
            logger.info(f"Would upload file to Supabase: {file_path}")
            return f"{self.url}/storage/v1/object/public/{self.bucket}/{file_path}"
        except Exception as e:
            logger.error(f"Failed to upload file: {str(e)}")
            return None

# ============================================================================
# INTEGRATION INSTANCES
# ============================================================================

twilio_client = TwilioSMS()
openai_processor = OpenAIProcessor()
supabase_storage = SupabaseStorage()
