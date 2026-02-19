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
                # Collect all text
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                
                full_text = "\n".join(all_text)
                
                # Extract show schedule using simple line-by-line parsing
                lines = full_text.split('\n')
                shows = []
                
                for line in lines:
                    # Match lines starting with STOP and containing month abbreviations
                    if line.startswith('STOP') and any(month in line for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                        parts = line.split()
                        if len(parts) >= 5:
                            stop_num = parts[0]
                            month = parts[1]
                            day = parts[2]
                            
                            # Find city and state
                            rest = ' '.join(parts[3:])
                            if ',' in rest:
                                city_part, venue_part = rest.split(',', 1)
                                city = city_part.strip()
                                
                                # Extract state (2 letters) and venue
                                state_match = re.match(r'\s*([A-Z]{2})\s+(.+)', venue_part)
                                if state_match:
                                    state = state_match.group(1)
                                    venue = state_match.group(2).strip()
                                    # Clean venue (remove URLs)
                                    venue = venue.split('http')[0].strip()
                                    
                                    if venue and len(venue) > 3:
                                        shows.append({
                                            'date': f'{month} {day}',
                                            'city': city,
                                            'state': state,
                                            'venue': venue
                                        })
                
                if shows:
                    logger.info(f"Extracted {len(shows)} shows from schedule")
                    
                    # State abbreviation to full name mapping
                    state_names = {
                        'AL': 'alabama', 'AK': 'alaska', 'AZ': 'arizona', 'AR': 'arkansas', 'CA': 'california',
                        'CO': 'colorado', 'CT': 'connecticut', 'DE': 'delaware', 'FL': 'florida', 'GA': 'georgia',
                        'HI': 'hawaii', 'ID': 'idaho', 'IL': 'illinois', 'IN': 'indiana', 'IA': 'iowa',
                        'KS': 'kansas', 'KY': 'kentucky', 'LA': 'louisiana', 'ME': 'maine', 'MD': 'maryland',
                        'MA': 'massachusetts', 'MI': 'michigan', 'MN': 'minnesota', 'MS': 'mississippi', 'MO': 'missouri',
                        'MT': 'montana', 'NE': 'nebraska', 'NV': 'nevada', 'NH': 'new hampshire', 'NJ': 'new jersey',
                        'NM': 'new mexico', 'NY': 'new york', 'NC': 'north carolina', 'ND': 'north dakota', 'OH': 'ohio',
                        'OK': 'oklahoma', 'OR': 'oregon', 'PA': 'pennsylvania', 'RI': 'rhode island', 'SC': 'south carolina',
                        'SD': 'south dakota', 'TN': 'tennessee', 'TX': 'texas', 'UT': 'utah', 'VT': 'vermont',
                        'VA': 'virginia', 'WA': 'washington', 'WV': 'west virginia', 'WI': 'wisconsin', 'WY': 'wyoming'
                    }
                    
                    # Create keywords for searching
                    keywords = set()
                    for show in shows:
                        keywords.add(show['city'].lower())
                        keywords.add(show['venue'].lower())
                        keywords.add(show['state'].lower())
                        keywords.add(f"{show['city'].lower()} {show['state'].lower()}")
                        # Add full state name
                        if show['state'] in state_names:
                            keywords.add(state_names[show['state']])
                        # Add city parts for partial matching
                        for part in show['city'].lower().split():
                            if len(part) > 2:
                                keywords.add(part)
                        # Add venue parts
                        for part in show['venue'].lower().split():
                            if len(part) > 3:
                                keywords.add(part)
                    
                    truth_records.append({
                        'record_type': 'show_schedule',
                        'data': {
                            'shows': shows,
                            'context': full_text[:500]
                        },
                        'search_keywords': list(keywords),
                        'confidence': 1.0
                    })
                
                # If no show schedule, try page-by-page extraction
                if not truth_records:
                    for page_num, page_text in enumerate(all_text):
                        records = self.extract_records_from_text(page_text, page_num + 1)
                        truth_records.extend(records)
                
                # If still no records, create general record
                if not truth_records and all_text:
                    full_text = "\n\n".join(all_text)
                    keywords = self.extract_keywords(full_text)
                    
                    truth_records.append({
                        'record_type': 'general',
                        'data': {
                            'source': file_name,
                            'content': full_text[:5000],
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
                    'text_length': sum(len(t) for t in all_text),
                    'shows_found': len(shows) if shows else 0
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
        
        # Look for show schedule patterns like "STOP001 Mar 5 Fort Wayne, IN Allen County War Memorial Coliseum"
        show_pattern = r'STOP\d+\s+([A-Z][a-z]{2}\s+\d{1,2})\s+([^,]+),\s*([A-Z]{2}\.?)\s+(.+?)(?=\nSTOP|\n\n|$)'
        shows = re.findall(show_pattern, text, re.MULTILINE)
        
        if shows:
            # Found show schedule data
            show_records = []
            for date_str, city, state, venue in shows:
                # Clean up venue (stop at next line or URL)
                venue_clean = venue.split('\n')[0].split('http')[0].strip()
                if venue_clean and len(venue_clean) > 3:  # Valid venue name
                    show_records.append({
                        'date': date_str.strip(),
                        'city': city.strip(),
                        'state': state.strip().rstrip('.'),
                        'venue': venue_clean
                    })
            
            if show_records:
                # Create searchable keywords
                keywords = []
                for show in show_records:
                    keywords.append(show['city'].lower())
                    keywords.append(show['venue'].lower())
                    keywords.append(f"{show['city']} {show['state']}".lower())
                    keywords.append(show['state'].lower())
                    # Add abbreviated city names
                    city_parts = show['city'].lower().split()
                    keywords.extend(city_parts)
                
                records.append({
                    'record_type': 'show_schedule',
                    'data': {
                        'page': page_num,
                        'shows': show_records,
                        'context': text[:500]
                    },
                    'search_keywords': list(set(keywords)),
                    'confidence': 1.0
                })
                
                return records
        
        # Fallback to original pattern matching
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
