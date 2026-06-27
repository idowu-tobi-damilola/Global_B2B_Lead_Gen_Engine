# direct_upload_to_sheets.py
# This script ONLY uploads leads to Google Sheets.
# It does NOT check Redis, preventing any conflicts.

import os
import json
import csv
import glob
import time
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

class DirectSheetUploader:
    def __init__(self):
        self.sheet_id = os.getenv("GOOGLE_SHEET_ID")
        if not self.sheet_id:
            raise ValueError("❌ GOOGLE_SHEET_ID not found in .env!")
        
        print(f"🔑 Connecting to Google Sheets: {self.sheet_id[:10]}...")
        self.service = self._authenticate()
        self.sheet = self.service.spreadsheets()
        print("✅ Google Sheets connected!")
        self.uploaded_count = 0
        self.duplicate_count = 0

    def _authenticate(self):
        """Authenticate using the service account credentials."""
        creds_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
        if not os.path.exists(creds_file):
            raise FileNotFoundError(f"❌ Credentials file not found: {creds_file}")

        creds = service_account.Credentials.from_service_account_file(
            creds_file, scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        return build('sheets', 'v4', credentials=creds)

    def _get_existing_emails(self):
        """Get all existing emails from the sheet to avoid duplicates."""
        try:
            result = self.sheet.values().get(
                spreadsheetId=self.sheet_id,
                range='A:A'  # Get all emails from column A
            ).execute()
            values = result.get('values', [])
            # Return a set of emails (skip the header row)
            return set(row[0] for row in values[1:] if row)
        except Exception as e:
            print(f"⚠️ Could not read existing emails: {e}")
            return set()

    def _upload_batch(self, leads_batch):
        """Upload a batch of leads to Google Sheets."""
        if not leads_batch:
            return
        
        # Prepare data for the sheet
        values = []
        for lead in leads_batch:
            values.append([
                lead.get('email', ''),
                lead.get('company', ''),
                lead.get('source_url', ''),
                lead.get('description', ''),
                lead.get('scraped_date', datetime.now().isoformat()),
                'valid'  # Status
            ])

        try:
            self.sheet.values().append(
                spreadsheetId=self.sheet_id,
                range='A:F',
                valueInputOption='USER_ENTERED',
                body={'values': values}
            ).execute()
            self.uploaded_count += len(leads_batch)
            print(f"  ✅ Uploaded batch of {len(leads_batch)} leads.")
        except Exception as e:
            print(f"  ❌ Error uploading batch: {e}")

    def upload_all_leads(self, batch_size=50):
        """Load all leads from files and upload them in batches."""
        lead_files = glob.glob("leads_*.json") + glob.glob("leads_*.csv")
        
        if not lead_files:
            print("❌ No lead files found!")
            return

        print(f"\n📁 Found {len(lead_files)} lead files.")
        
        # First, get existing emails to avoid duplicates
        print("🔍 Checking for existing emails in the sheet...")
        existing_emails = self._get_existing_emails()
        print(f"📊 Found {len(existing_emails)} existing emails in the sheet.")

        all_leads = []
        
        # Load leads from all files
        for filepath in sorted(lead_files, reverse=True):
            print(f"\n📄 Processing: {filepath}")
            leads = []
            try:
                if filepath.endswith('.json'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        leads = json.load(f)
                elif filepath.endswith('.csv'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        leads = [row for row in reader]
            except Exception as e:
                print(f"  ❌ Error reading {filepath}: {e}")
                continue

            for lead in leads:
                email = lead.get('email', '').strip()
                if not email:
                    continue
                if email in existing_emails:
                    self.duplicate_count += 1
                    continue
                
                # Prepare lead for upload
                all_leads.append({
                    'email': email,
                    'company': lead.get('company', ''),
                    'source_url': lead.get('source_url', ''),
                    'description': lead.get('description', ''),
                    'scraped_date': lead.get('scraped_date', datetime.now().isoformat())
                })
                existing_emails.add(email)  # Track in this session

        print(f"\n📊 Found {len(all_leads)} new leads to upload.")
        
        if not all_leads:
            print("✅ No new leads to upload.")
            return

        # Upload leads in batches
        print(f"\n🚀 Uploading {len(all_leads)} leads in batches of {batch_size}...")
        for i in range(0, len(all_leads), batch_size):
            batch = all_leads[i:i+batch_size]
            self._upload_batch(batch)
            time.sleep(0.5)  # Small delay between batches

        print("\n" + "="*60)
        print(f"✅ UPLOAD COMPLETE!")
        print(f"  📧 Successfully uploaded: {self.uploaded_count}")
        print(f"  ⏭️ Duplicates skipped: {self.duplicate_count}")
        print("="*60)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📤 DIRECT UPLOAD TO GOOGLE SHEETS")
    print("✅ No Redis check - No conflicts")
    print("="*60)
    
    uploader = DirectSheetUploader()
    uploader.upload_all_leads()