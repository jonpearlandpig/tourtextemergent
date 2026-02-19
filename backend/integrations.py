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
            logger.warning("OpenAI disabled - using basic formatting")
            # Basic formatting without LLM
            return self._basic_format(truth_data, query)
        
        try:
            # Use GPT to format response (implementation placeholder)
            # In production: call OpenAI API with formatting prompt
            return f"Response based on truth records: {truth_data}"
        except Exception as e:
            logger.error(f"Failed to format response: {str(e)}")
            return self._basic_format(truth_data, query)
    
    def _basic_format(self, truth_data: Dict[str, Any], query: str) -> str:
        """Basic formatting without LLM"""
        response_parts = []
        
        if isinstance(truth_data, dict):
            query_lower = query.lower().strip('?!.,')
            
            # Check if this is a show_schedule record (new format)
            if 'shows' in truth_data:
                shows = truth_data['shows']
                
                # State name to abbreviation mapping
                state_mapping = {
                    'florida': 'FL', 'california': 'CA', 'texas': 'TX', 'new york': 'NY',
                    'pennsylvania': 'PA', 'illinois': 'IL', 'ohio': 'OH', 'georgia': 'GA',
                    'north carolina': 'NC', 'michigan': 'MI', 'indiana': 'IN', 'tennessee': 'TN',
                    'massachusetts': 'MA', 'arizona': 'AZ', 'minnesota': 'MN', 'colorado': 'CO',
                    'washington': 'WA', 'maryland': 'MD', 'wisconsin': 'WI', 'missouri': 'MO'
                }
                
                # Try to find matching city, state, or venue
                matching_shows = []
                for show in shows:
                    city = show['city'].lower()
                    state = show['state'].upper()
                    venue = show['venue'].lower()
                    
                    # Check if query matches city
                    if city in query_lower or query_lower in city:
                        matching_shows.append(show)
                        continue
                    
                    # Check if query matches state abbreviation
                    if state.lower() in query_lower or query_lower == state.lower():
                        matching_shows.append(show)
                        continue
                    
                    # Check if query matches full state name
                    if query_lower in state_mapping and state_mapping[query_lower] == state:
                        matching_shows.append(show)
                        continue
                    
                    # Check if query matches venue
                    if venue in query_lower or query_lower in venue:
                        matching_shows.append(show)
                
                # If we found exact matches, return them
                if len(matching_shows) == 1:
                    show = matching_shows[0]
                    return f"**{show['city']}, {show['state']}**\nVenue: {show['venue']}\nDate: {show['date']}\n\nFor complete tour details, check the uploaded documents."
                elif len(matching_shows) > 1 and len(matching_shows) <= 5:
                    response_parts = []
                    for show in matching_shows:
                        response_parts.append(f"• {show['date']} - {show['city']}, {show['state']} - {show['venue']}")
                    return "\n".join(response_parts) + "\n\nFor complete details, check the uploaded tour documents."
                elif len(matching_shows) > 5:
                    return f"Found {len(matching_shows)} shows matching your query. Please be more specific about which city or date."
                
                # No matches but we have shows - return all if reasonable
                if len(shows) <= 5:
                    response_parts = []
                    for show in shows:
                        response_parts.append(f"• {show['date']} - {show['city']}, {show['state']} - {show['venue']}")
                    return "\n".join(response_parts) + "\n\nFor complete details, check the uploaded tour documents."
                else:
                    return f"Found {len(shows)} shows in total. Please be more specific about which city, state, or date you're asking about."
            
            # Original format handling
            cities = truth_data.get('cities', [])
            venues = truth_data.get('venues', [])
            dates = truth_data.get('dates', [])
            
            # Try to find matching city
            matching_city = None
            for city in cities:
                if city.lower() in query_lower or query_lower in city.lower():
                    matching_city = city
                    break
            
            if matching_city:
                response_parts.append(f"**{matching_city}**")
                
                # Look for real venue names
                if venues:
                    real_venues = [v for v in venues if len(v) > 10 and (' ' in v or 'center' in v.lower() or 'arena' in v.lower() or 'stadium' in v.lower() or 'hall' in v.lower())]
                    if real_venues:
                        response_parts.append(f"Venue: {real_venues[0]}")
                
                if dates:
                    response_parts.append(f"Date: {dates[0]}")
            
            # If we found specific info, return it
            if len(response_parts) > 1:
                return "\n".join(response_parts) + "\n\nFor complete details, check the uploaded tour documents."
            
            # General information
            if dates and len(dates) > 0:
                response_parts.append(f"Dates: {', '.join(dates[:3])}")
            
            if cities and len(cities) > 0:
                response_parts.append(f"Cities: {', '.join(cities[:5])}")
            
            if venues:
                real_venues = [v for v in venues if len(v) > 10 and (' ' in v or 'center' in v.lower() or 'arena' in v.lower() or 'stadium' in v.lower() or 'hall' in v.lower())]
                if real_venues:
                    response_parts.append(f"Venues: {', '.join(real_venues[:3])}")
            
            if response_parts:
                return "\n".join(response_parts) + "\n\nFor complete details, check the uploaded tour documents."
            
            # Try context
            if 'context' in truth_data and truth_data.get('context'):
                context = truth_data['context'][:300]
                return f"Here's what I found:\n\n{context}...\n\nFor more details, check the uploaded tour documents."
            
            if 'full_content' in truth_data:
                content = truth_data['full_content']
                query_terms = [q.strip('?!.,') for q in query_lower.split()]
                lines = content.split('\n')
                relevant_lines = []
                
                for i, line in enumerate(lines):
                    line_lower = line.lower()
                    if any(term in line_lower for term in query_terms if len(term) > 2):
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        relevant_lines.extend(lines[start:end])
                        if len(relevant_lines) > 10:
                            break
                
                if relevant_lines:
                    return "\n".join(relevant_lines[:10])
            
            return "I found relevant information in the tour documents. Please check the uploaded files for specific details."
        
        return str(truth_data)[:500]

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
