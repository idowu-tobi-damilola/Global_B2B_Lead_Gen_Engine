# ============================================================================
# google_sheets_upload.py - REAL-TIME GOOGLE SHEETS INTEGRATION
# ============================================================================
# ✅ SEPARATE FILE - Does NOT modify quick_leads.py
# ✅ Real-time lead upload to Google Sheets
# ✅ Works alongside your existing system
# ✅ Uses Redis to prevent duplicates
# ✅ No conflicts with existing code
# ============================================================================

import os
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Redis for deduplication (same Redis as your scraper)
import redis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class RealTimeGoogleSheets:
    """
    Real-time Google Sheets uploader for B2B leads.
    Works alongside quick_leads.py - no conflicts.
    """
    
    def __init__(self, sheet_id: str, credentials_file: str = "credentials.json"):
        """
        Initialize Google Sheets connection.
        
        Args:
            sheet_id: Google Sheet ID from URL
            credentials_file: Path to service account JSON file
        """
        self.sheet_id = sheet_id
        self.credentials_file = credentials_file
        
        # Redis connection (same Redis as scraper)
        try:
            self.redis = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0,
                decode_responses=True
            )
            self.redis.ping()
            logger.info("✅ Connected to Redis (same as scraper)")
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
            self.redis = None
        
        # Initialize Google Sheets API
        self.sheet = self._init_google_sheets()
        
        if self.sheet:
            # Setup the sheet if needed
            self._setup_sheet()
    
    def _init_google_sheets(self):
        """Initialize Google Sheets API with service account"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            
            if not os.path.exists(self.credentials_file):
                logger.error(f"❌ Credentials file not found: {self.credentials_file}")
                return None
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file, scopes=SCOPES
            )
            
            service = build('sheets', 'v4', credentials=credentials)
            sheet = service.spreadsheets()
            
            logger.info("✅ Google Sheets API initialized")
            return sheet
            
        except Exception as e:
            logger.error(f"❌ Google Sheets init failed: {e}")
            return None
    
    def _setup_sheet(self):
        """Create headers if sheet is empty"""
        try:
            # Check if sheet has data
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='A1:E1'
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                # Add headers
                headers = [
                    ['Email', 'Company', 'Source URL', 'Description', 'Time Found']
                ]
                
                self.sheet.values().update(
                    spreadsheetId=self.sheet_id,
                    range='A1:E1',
                    valueInputOption='RAW',
                    body={'values': headers}
                ).execute()
                
                # Format headers
                self._format_headers()
                
                logger.info("✅ Sheet headers created")
                
        except Exception as e:
            logger.error(f"❌ Sheet setup failed: {e}")
    
    def _format_headers(self):
        """Format header row (bold, frozen)"""
        try:
            requests = [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": 0,
                            "startRowIndex": 0,
                            "endRowIndex": 1
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                                "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)"
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": 0,
                            "gridProperties": {"frozenRowCount": 1}
                        },
                        "fields": "gridProperties.frozenRowCount"
                    }
                }
            ]
            
            self.sheet.batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': requests}
            ).execute()
            
        except Exception as e:
            logger.debug(f"Header formatting skipped: {e}")
    
    def is_lead_scraped(self, email: str) -> bool:
        """Check if email already exists in Redis"""
        if not self.redis:
            return False
        
        try:
            return bool(self.redis.sismember("scraped_emails", email))
        except:
            return False
    
    def mark_lead_scraped(self, email: str):
        """Mark email as scraped in Redis"""
        if not self.redis:
            return
        
        try:
            self.redis.sadd("scraped_emails", email)
        except:
            pass
    
    def add_lead_to_sheet(self, email: str, company: str, source_url: str, 
                          description: str = "", timestamp: str = None):
        """
        Add a single lead to Google Sheets in REAL-TIME.
        
        Args:
            email: Email address
            company: Company name
            source_url: Where the email was found
            description: Optional description
            timestamp: Time found (defaults to now)
        """
        # Skip if already scraped
        if self.is_lead_scraped(email):
            logger.info(f"⏭️ Email already scraped: {email}")
            return False
        
        if not self.sheet:
            logger.warning("⚠️ Google Sheets not available")
            return False
        
        if not timestamp:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            # Append the lead
            values = [[email, company, source_url, description[:200], timestamp]]
            
            self.sheet.values().append(
                spreadsheetId=self.sheet_id,
                range='A:E',
                valueInputOption='RAW',
                body={'values': values}
            ).execute()
            
            # Mark as scraped in Redis
            self.mark_lead_scraped(email)
            
            logger.info(f"✅ Lead added to Google Sheets: {email} ({company})")
            return True
            
        except HttpError as e:
            if '429' in str(e):
                logger.warning("⚠️ Rate limit hit, waiting 1 second...")
                time.sleep(1)
                return self.add_lead_to_sheet(email, company, source_url, description, timestamp)
            else:
                logger.error(f"❌ Google Sheets error: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to add lead: {e}")
            return False
    
    def add_leads_batch(self, leads: List[Dict], delay: float = 0.1):
        """
        Add multiple leads to Google Sheets in real-time.
        
        Args:
            leads: List of lead dictionaries
            delay: Delay between additions (seconds)
        """
        count = 0
        for lead in leads:
            email = lead.get('email', '')
            company = lead.get('company', '')
            source_url = lead.get('source_url', '')
            description = lead.get('description', '')
            timestamp = lead.get('scraped_date')
            
            if email and not self.is_lead_scraped(email):
                if self.add_lead_to_sheet(email, company, source_url, description, timestamp):
                    count += 1
                    time.sleep(delay)  # Prevent rate limiting
        
        logger.info(f"✅ Added {count} new leads to Google Sheets")
        return count
    
    def get_lead_count(self) -> int:
        """Get total leads in Google Sheets"""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='A:A'
            ).execute()
            
            values = result.get('values', [])
            return max(0, len(values) - 1)  # Subtract header
            
        except Exception as e:
            logger.error(f"❌ Failed to get lead count: {e}")
            return 0
    
    def get_all_leads(self, limit: int = 1000) -> List[Dict]:
        """Get all leads from Google Sheets"""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='A:E'
            ).execute()
            
            values = result.get('values', [])
            if not values or len(values) < 2:
                return []
            
            leads = []
            headers = values[0]  # ['Email', 'Company', 'Source URL', 'Description', 'Time Found']
            
            for row in values[1:limit+1]:
                lead = {
                    'email': row[0] if len(row) > 0 else '',
                    'company': row[1] if len(row) > 1 else '',
                    'source_url': row[2] if len(row) > 2 else '',
                    'description': row[3] if len(row) > 3 else '',
                    'time_found': row[4] if len(row) > 4 else ''
                }
                leads.append(lead)
            
            return leads
            
        except Exception as e:
            logger.error(f"❌ Failed to get leads: {e}")
            return []


# ============================================================================
# INTEGRATION WITH YOUR SCRAPER
# ============================================================================

class ScraperToSheets:
    """
    Bridge between your scraper and Google Sheets.
    This is called by your scraper when a new lead is found.
    """
    
    def __init__(self, sheet_id: str, credentials_file: str = "credentials.json"):
        self.sheets = RealTimeGoogleSheets(sheet_id, credentials_file)
    
    def on_lead_found(self, email: str, company: str, source_url: str, description: str = ""):
        """
        Call this function from your scraper when a new lead is found.
        
        Example in your scraper:
            if result['success'] and result['valid_emails']:
                for email in result['valid_emails']:
                    sheets_uploader.on_lead_found(
                        email=email,
                        company=company,
                        source_url=url,
                        description=description
                    )
        """
        if not self.sheets.sheet:
            logger.warning("⚠️ Google Sheets not available, skipping upload")
            return False
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self.sheets.add_lead_to_sheet(email, company, source_url, description, timestamp)
    
    def on_lead_batch(self, leads: List[Dict]):
        """
        Call this function with a batch of leads.
        """
        return self.sheets.add_leads_batch(leads)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Load configuration from .env
from dotenv import load_dotenv
load_dotenv()

# Get Sheet ID from .env
SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")

if not SHEET_ID:
    print("\n⚠️ WARNING: GOOGLE_SHEET_ID not set in .env file!")
    print("Add this to your .env file:")
    print("  GOOGLE_SHEET_ID=your_sheet_id_from_url")
    print("  GOOGLE_CREDENTIALS_FILE=credentials.json\n")


# ============================================================================
# STANDALONE USAGE
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("📋 REAL-TIME GOOGLE SHEETS LEAD UPLOADER")
    print("✅ Works with your existing scraper")
    print("✅ No modifications to quick_leads.py")
    print("=" * 80)
    
    print("\n📌 Example Usage:")
    print("""
    # In your scraper, when a lead is found:
    from google_sheets_upload import ScraperToSheets
    
    # Initialize (once)
    sheets = ScraperToSheets(SHEET_ID)
    
    # When you find a lead:
    sheets.on_lead_found(
        email="sales@company.com",
        company="Company Name",
        source_url="https://company.com/contact",
        description="B2B lead from electronics distributor"
    )
    # This adds the lead to Google Sheets IN REAL-TIME!
    """)
    
    print("\n📊 Google Sheet Format:")
    print("""
    | Email                     | Company              | Source URL          | Description          | Time Found          |
    |---------------------------|----------------------|---------------------|----------------------|---------------------|
    | sales@autozone.com       | AutoZone             | autozone.com/contact| B2B lead            | 2026-06-22 22:01:15 |
    | info@advanceautoparts.com| Advance Auto Parts   | advanceautoparts.com| B2B lead            | 2026-06-22 22:01:18 |
    | ... (keeps updating)     | ...                  | ...                 | ...                  | ...                 |
    """)
    
    if SHEET_ID:
        print(f"\n✅ Sheet ID found: {SHEET_ID}")
        print("\n🚀 To test the connection, run this in Python:")
        print(f"""
from google_sheets_upload import RealTimeGoogleSheets
sheets = RealTimeGoogleSheets("{SHEET_ID}")
sheets.add_lead_to_sheet("test@example.com", "Test Company", "https://test.com", "Test lead")
        """)
    else:
        print("\n❌ Sheet ID not found in .env file!")
        print("Please add: GOOGLE_SHEET_ID=your_sheet_id")