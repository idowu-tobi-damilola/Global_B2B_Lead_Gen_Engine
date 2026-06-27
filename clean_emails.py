# clean_emails.py - CLEAN INVALID EMAILS FROM GOOGLE SHEETS
# This is a SEPARATE file - Does NOT modify any existing files
# Filters out: image files, sentry.io, UUIDs, invalid formats

import os
import re
import time
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

class EmailCleaner:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        if not self.sheet_id:
            raise ValueError("❌ GOOGLE_SHEET_ID not found in .env!")
        
        print(f"🔑 Connecting to Google Sheets: {self.sheet_id[:10]}...")
        creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        
        if not os.path.exists(creds_file):
            raise FileNotFoundError(f"❌ Credentials file not found: {creds_file}")
        
        creds = service_account.Credentials.from_service_account_file(
            creds_file, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.service = build('sheets', 'v4', credentials=creds)
        self.sheet = self.service.spreadsheets()
        print("✅ Google Sheets connected!")
        
        # Counters
        self.total_emails = 0
        self.valid_emails = 0
        self.invalid_emails = 0
        self.uploaded_count = 0
    
    def is_valid_email(self, email: str) -> bool:
        """Check if email is valid (not an image, not sentry.io, not UUID, etc.)"""
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip().lower()
        
        # Must contain @
        if '@' not in email:
            return False
        
        # Split into local and domain parts
        try:
            local, domain = email.split('@', 1)
        except ValueError:
            return False
        
        # ============================================================
        # INVALID PATTERNS TO FILTER OUT
        # ============================================================
        
        # 1. Image files (common image extensions)
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico', '.tiff']
        for ext in image_extensions:
            if email.endswith(ext):
                return False
            if local.endswith(ext):
                return False
        
        # 2. Image-related patterns
        image_patterns = [
            r'@2x\.', r'@1x\.', r'@0\.75x\.', r'@3x\.',
            r'@\d+x\.', r'-\d+x\d+\.', r'x\d+\.jpg', r'x\d+\.png',
            r'cropped-', r'thumbnail', r'-300x', r'-270x', r'-180x', r'-192x', r'-32x',
            r'logo@', r'icon@', r'sprite@', r'\.svg', r'\.ico'
        ]
        for pattern in image_patterns:
            if re.search(pattern, email, re.IGNORECASE):
                return False
        
        # 3. Domain-based invalid emails
        invalid_domains = [
            'sentry.io', 'sentry.wixpress.com', 'sentry-next.wixpress.com',
            'bug-reporting', 'example.com', 'yourdomain.com',
            'wixpress.com', 'sentry', 'intercom-mail.com',
            'pissedconsumer.com'
        ]
        for invalid_domain in invalid_domains:
            if invalid_domain in domain:
                return False
        
        # 4. UUID pattern (e.g., fcbf5b3f-b4a4-43a2-9e69-d2c27a429693@...)
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(uuid_pattern, local, re.IGNORECASE):
            return False
        
        # 5. Hexadecimal patterns (e.g., 5d1795a2db124a268f1e1bd88f503500@...)
        hex_pattern = r'^[0-9a-f]{32}$'
        if re.match(hex_pattern, local, re.IGNORECASE):
            return False
        
        # 6. Very short local part (less than 2 characters)
        if len(local) < 2:
            return False
        
        # 7. Local part contains invalid characters (common in images)
        invalid_chars = ['%20', ' ', '+', '%']
        for char in invalid_chars:
            if char in email:
                return False
        
        # 8. Valid email should have a proper domain with a dot
        if '.' not in domain:
            return False
        
        # 9. Domain should have at least 2 parts
        domain_parts = domain.split('.')
        if len(domain_parts) < 2:
            return False
        
        return True
    
    def get_all_emails(self):
        """Read all emails from Google Sheet"""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='A:E'  # Get all columns
            ).execute()
            return result.get('values', [])
        except Exception as e:
            print(f"❌ Error reading sheet: {e}")
            return []
    
    def analyze_sheet(self):
        """Analyze all emails in the sheet and show stats"""
        print("\n📊 ANALYZING YOUR GOOGLE SHEET")
        print("=" * 60)
        
        rows = self.get_all_emails()
        if not rows or len(rows) < 2:
            print("❌ No data found in sheet!")
            return [], [], []
        
        headers = rows[0] if rows else []
        data_rows = rows[1:] if len(rows) > 1 else []
        
        valid_emails_list = []
        invalid_emails_list = []
        
        print(f"📋 Found {len(data_rows)} total rows")
        
        for row in data_rows:
            if not row:
                continue
            
            email = row[0].strip() if len(row) > 0 else ''
            if not email:
                continue
            
            self.total_emails += 1
            
            if self.is_valid_email(email):
                self.valid_emails += 1
                valid_emails_list.append(row)
            else:
                self.invalid_emails += 1
                invalid_emails_list.append({
                    'email': email,
                    'row': row,
                    'reason': self.get_invalid_reason(email)
                })
        
        print("\n📊 ANALYSIS COMPLETE!")
        print("=" * 60)
        print(f"  📧 Total emails: {self.total_emails}")
        print(f"  ✅ Valid emails: {self.valid_emails}")
        print(f"  ❌ Invalid emails: {self.invalid_emails}")
        print("=" * 60)
        
        if invalid_emails_list:
            print("\n❌ SAMPLE INVALID EMAILS:")
            for item in invalid_emails_list[:20]:
                print(f"  • {item['email']} ({item['reason']})")
            if len(invalid_emails_list) > 20:
                print(f"  ... and {len(invalid_emails_list) - 20} more")
        
        return valid_emails_list, invalid_emails_list, headers
    
    def get_invalid_reason(self, email: str) -> str:
        """Get reason why an email is invalid"""
        email_lower = email.lower()
        
        if email.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.ico')):
            return "Image file"
        
        image_patterns = ['@2x.', '@1x.', 'cropped-', 'thumbnail', 'logo@', 'icon@', 'x2x', 'sprite']
        for pattern in image_patterns:
            if pattern in email_lower:
                return "Image reference"
        
        invalid_domains = ['sentry.io', 'sentry.wixpress.com', 'wixpress.com', 'bug-reporting', 'service@matto.com.tw', 'example@mysite.com']
        for domain in invalid_domains:
            if domain in email_lower:
                return f"Invalid domain: {domain}"
        
        if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}@', email_lower):
            return "UUID format"
        
        if re.match(r'^[0-9a-f]{32}@', email_lower):
            return "Hash format"
        
        return "Invalid format"
    
    def create_clean_sheet(self):
        """Create a new sheet with only valid emails"""
        print("\n🚀 CREATING CLEAN SHEET (Valid Emails Only)")
        print("=" * 60)
        
        rows = self.get_all_emails()
        if not rows or len(rows) < 2:
            print("❌ No data found!")
            return
        
        headers = rows[0] if rows else ['Email', 'Company', 'Source URL', 'Description', 'Time Found']
        data_rows = rows[1:] if len(rows) > 1 else []
        
        valid_rows = [headers]  # Start with headers
        invalid_count = 0
        
        for row in data_rows:
            if not row:
                continue
            
            email = row[0].strip() if len(row) > 0 else ''
            if not email:
                continue
            
            if self.is_valid_email(email):
                valid_rows.append(row)
            else:
                invalid_count += 1
        
        print(f"📊 Valid emails: {len(valid_rows) - 1}")
        print(f"❌ Invalid emails removed: {invalid_count}")
        
        if len(valid_rows) <= 1:
            print("❌ No valid emails found!")
            return
        
        # Create a new sheet with valid emails only
        print("\n📤 Creating clean sheet with valid emails...")
        
        # Clear existing sheet and upload clean data
        try:
            # Clear the sheet
            self.sheet.values().clear(
                spreadsheetId=self.sheet_id,
                range='A:F'
            ).execute()
            
            # Upload clean data in batches
            batch_size = 100
            for i in range(0, len(valid_rows), batch_size):
                batch = valid_rows[i:i+batch_size]
                self.sheet.values().append(
                    spreadsheetId=self.sheet_id,
                    range='A:F',
                    valueInputOption='USER_ENTERED',
                    body={'values': batch}
                ).execute()
                self.uploaded_count += len(batch)
                print(f"  ✅ Uploaded batch {i//batch_size + 1}: {len(batch)} rows")
                time.sleep(0.5)
            
            print("\n" + "=" * 60)
            print(f"✅ CLEAN SHEET CREATED!")
            print(f"  📧 Valid emails: {len(valid_rows) - 1}")
            print(f"  ❌ Invalid emails removed: {invalid_count}")
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error creating clean sheet: {e}")

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧹 CLEAN EMAILS - REMOVE INVALID ENTRIES")
    print("✅ Keeps only valid business emails")
    print("=" * 60)
    
    cleaner = EmailCleaner()
    
    print("\n📌 Choose an option:")
    print("  1. Analyze only (show stats, no changes)")
    print("  2. Create clean sheet (remove invalid emails)")
    print("  3. Exit")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        cleaner.analyze_sheet()
    elif choice == '2':
        cleaner.analyze_sheet()
        confirm = input("\n⚠️ This will REMOVE invalid emails from your sheet. Continue? (y/n): ").strip().lower()
        if confirm == 'y':
            cleaner.create_clean_sheet()
        else:
            print("❌ Cancelled")
    else:
        print("❌ Cancelled")