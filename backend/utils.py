import uuid
import hashlib
from datetime import datetime
import random
import string

def generate_taid(prefix: str) -> str:
    """
    Generate Telauthorium Identifier (TAID)
    Format: PREFIX-XXXXX where XXXXX is a 5-character alphanumeric code
    
    Args:
        prefix: TAID prefix (e.g., 'TID-TT-TOUR', 'TAID-TT-SRC', 'TAID-TT-TRUTH')
    
    Returns:
        Full TAID string
    """
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{prefix}-{code}"

def generate_uuid() -> str:
    """Generate UUID string"""
    return str(uuid.uuid4())

def generate_session_id() -> str:
    """Generate unique session ID"""
    return f"sess-{uuid.uuid4().hex[:16]}"

def hash_phone_number(phone: str) -> str:
    """
    Hash phone number for privacy (SHA256)
    Never store raw phone numbers in logs
    
    Args:
        phone: Raw phone number
    
    Returns:
        SHA256 hash of phone number
    """
    return hashlib.sha256(phone.encode()).hexdigest()

def hash_file(file_content: bytes) -> str:
    """
    Generate SHA256 hash of file content for deduplication
    
    Args:
        file_content: File bytes
    
    Returns:
        SHA256 hash string
    """
    return hashlib.sha256(file_content).hexdigest()

def generate_tour_code(tour_name: str) -> str:
    """
    Generate tour code from tour name
    Example: "Kings of Leon 2026" -> "KOL26"
    
    Args:
        tour_name: Full tour name
    
    Returns:
        Tour code (uppercase, max 6 chars)
    """
    # Extract first letters of words
    words = tour_name.split()
    code = ''.join([word[0] for word in words if word])[:4].upper()
    
    # Add year if present
    for word in words:
        if word.isdigit() and len(word) == 4:
            code += word[-2:]
            break
    
    return code or 'TOUR'
