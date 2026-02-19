"""
File processing module for TourText
Handles parsing of uploaded files and creation of truth records
"""

import logging
import re
from typing import Dict, List, Any, Optional
import pandas as pd

try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("pdfplumber not available - PDF parsing disabled")

logger = logging.getLogger(__name__)

class FileProcessor:
    """Process uploaded files and extract structured data"""
    
    def __init__(self):
        self.pdf_available = PDF_AVAILABLE
    
    async def process_file(self, file_content: bytes, file_name: str, file_type: str, mime_type: str) -> Dict[str, Any]:
        """
        Process file and extract data
        
        Returns:
            {
                'success': bool,
                'truth_records': List[Dict],
                'metadata': Dict,
                'error': Optional[str]
            }
        """
        try:
            if mime_type and 'pdf' in mime_type.lower():
                return await self.process_pdf(file_content, file_name)
            elif mime_type and ('csv' in mime_type.lower() or 'excel' in mime_type.lower() or 'spreadsheet' in mime_type.lower()):
                return await self.process_csv_excel(file_content, file_name, mime_type)
            else:
                # Try to detect by extension
                if file_name.lower().endswith('.pdf'):
                    return await self.process_pdf(file_content, file_name)
                elif file_name.lower().endswith(('.csv', '.xlsx', '.xls')):
                    return await self.process_csv_excel(file_content, file_name, mime_type)
                else:
                    return {
                        'success': False,
                        'truth_records': [],
                        'metadata': {},
                        'error': f'Unsupported file type: {mime_type}'
                    }
        
        except Exception as e:
            logger.error(f"File processing error: {str(e)}")
            return {
                'success': False,
                'truth_records': [],
                'metadata': {},
                'error': str(e)
            }
    
    async def process_pdf(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Extract text from PDF and create truth records"""
        if not self.pdf_available:
            return {
                'success': False,
                'truth_records': [],
                'metadata': {},
                'error': 'PDF processing not available'
            }
        
        try:
            import io
            pdf_file = io.BytesIO(file_content)
            
            truth_records = []
            all_text = []
            
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                        
                        # Extract structured information from text
                        # Look for common patterns
                        records = self.extract_records_from_text(text, page_num + 1)
                        truth_records.extend(records)
            
            # If no structured records found, create one general record with all text
            if not truth_records and all_text:
                full_text = "\n\n".join(all_text)
                
                # Extract keywords for searching
                keywords = self.extract_keywords(full_text)
                
                truth_records.append({
                    'record_type': 'general',
                    'data': {
                        'source': file_name,
                        'content': full_text[:5000],  # Limit content size
                        'full_content': full_text,
                        'page_count': len(all_text)
                    },
                    'search_keywords': keywords,
                    'confidence': 1.0
                })
            
            return {
                'success': True,
                'truth_records': truth_records,
                'metadata': {
                    'page_count': len(all_text),
                    'text_length': sum(len(t) for t in all_text)
                },
                'error': None
            }
        
        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            return {
                'success': False,
                'truth_records': [],
                'metadata': {},
                'error': str(e)
            }
    
    async def process_csv_excel(self, file_content: bytes, file_name: str, mime_type: str) -> Dict[str, Any]:
        """Process CSV or Excel file"""
        try:
            import io
            
            # Try to read as CSV first
            if 'csv' in mime_type.lower() or file_name.lower().endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                df = pd.read_excel(io.BytesIO(file_content))
            
            truth_records = []
            
            # Create a truth record for each row
            for idx, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Extract keywords from all values
                keywords = []
                for col, value in row_dict.items():
                    if pd.notna(value):
                        keywords.extend(str(value).lower().split())
                
                truth_records.append({
                    'record_type': 'show',  # Default to show type
                    'data': row_dict,
                    'search_keywords': list(set(keywords)),  # Unique keywords
                    'confidence': 1.0
                })
            
            return {
                'success': True,
                'truth_records': truth_records,
                'metadata': {
                    'row_count': len(df),
                    'columns': list(df.columns)
                },
                'error': None
            }
        
        except Exception as e:
            logger.error(f"CSV/Excel processing error: {str(e)}")
            return {
                'success': False,
                'truth_records': [],
                'metadata': {},
                'error': str(e)
            }
    
    def extract_records_from_text(self, text: str, page_num: int) -> List[Dict]:
        """Extract structured records from text"""
        records = []
        
        # Look for venue/show information patterns
        # Examples: "Madison Square Garden", "Load-in: 10:00 AM", "March 15, 2026"
        
        # Extract dates
        date_pattern = r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        
        # Extract times
        time_pattern = r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)\b'
        times = re.findall(time_pattern, text, re.IGNORECASE)
        
        # Extract venues (capitalized phrases)
        venue_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4}\b'
        venues = re.findall(venue_pattern, text)
        
        # If we found structured data, create records
        if dates or times or venues:
            keywords = []
            keywords.extend([d.lower() for d in dates])
            keywords.extend([t.lower() for t in times])
            keywords.extend([v.lower() for v in venues])
            
            # Extract cities from common patterns
            cities = self.extract_cities(text)
            keywords.extend([c.lower() for c in cities])
            
            records.append({
                'record_type': 'show',
                'data': {
                    'page': page_num,
                    'dates': dates,
                    'times': times,
                    'venues': venues,
                    'cities': cities,
                    'context': text[:500]
                },
                'search_keywords': list(set(keywords)),
                'confidence': 0.9
            })
        
        return records
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract searchable keywords from text"""
        # Remove special characters and split
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Common stop words to exclude
        stop_words = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'will', 'have', 'has', 'are', 'was', 'were'}
        
        keywords = [w for w in words if w not in stop_words]
        
        # Add common tour-related terms if found
        tour_terms = ['venue', 'show', 'load', 'doors', 'soundcheck', 'settlement', 'dock', 'time', 'date', 'city']
        keywords.extend([term for term in tour_terms if term in text.lower()])
        
        # Extract cities, states, venues
        cities = self.extract_cities(text)
        keywords.extend([c.lower() for c in cities])
        
        return list(set(keywords))[:100]  # Limit to 100 unique keywords
    
    def extract_cities(self, text: str) -> List[str]:
        """Extract common US city names"""
        # Common tour cities
        common_cities = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
            'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
            'Fort Worth', 'Columbus', 'Indianapolis', 'Charlotte', 'San Francisco',
            'Seattle', 'Denver', 'Washington', 'Boston', 'Nashville', 'Portland',
            'Las Vegas', 'Detroit', 'Memphis', 'Louisville', 'Baltimore', 'Milwaukee',
            'Albuquerque', 'Tucson', 'Fresno', 'Sacramento', 'Kansas City', 'Mesa',
            'Atlanta', 'Omaha', 'Colorado Springs', 'Raleigh', 'Miami', 'Cleveland',
            'Tulsa', 'Oakland', 'Minneapolis', 'Wichita', 'Arlington', 'Tampa',
            'Indiana', 'Wayne', 'Evansville', 'South Bend', 'Hammond', 'Muncie',
            'Bloomington', 'Gary', 'Carmel', 'Fishers', 'Terre Haute', 'Lafayette'
        ]
        
        found_cities = []
        for city in common_cities:
            # Match whole word only
            pattern = r'\b' + re.escape(city) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_cities.append(city)
        
        return found_cities

file_processor = FileProcessor()
