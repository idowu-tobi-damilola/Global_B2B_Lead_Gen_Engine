# ============================================================================
# run_with_sheets.py - Wrapper for quick_leads.py with Google Sheets
# ============================================================================
# ✅ Does NOT modify quick_leads.py
# ✅ Adds real-time Google Sheets upload
# ✅ Uses your existing scraper as-is
# ============================================================================

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Import your existing scraper (NO MODIFICATIONS)
from quick_leads import QuickLeadExtractor

# Import Google Sheets integration
from google_sheets_upload import ScraperToSheets

load_dotenv()

# ============================================================================
# Extended Extractor with Google Sheets
# ============================================================================

class QuickLeadExtractorWithSheets(QuickLeadExtractor):
    """
    Extends your existing QuickLeadExtractor with Google Sheets.
    Your original code is 100% unchanged.
    """
    
    def __init__(self):
        # Call your original __init__ (unchanged)
        super().__init__()
        
        # Initialize Google Sheets
        self.sheets_uploader = None
        self._init_google_sheets()
    
    def _init_google_sheets(self):
        """Initialize Google Sheets uploader (separate from your code)"""
        try:
            sheet_id = os.getenv("GOOGLE_SHEET_ID")
            if sheet_id:
                self.sheets_uploader = ScraperToSheets(sheet_id)
                print(f"✅ Google Sheets ready: {sheet_id[:8]}...")
                return True
            else:
                print("ℹ️ Google Sheets not configured (add GOOGLE_SHEET_ID to .env)")
                return False
        except Exception as e:
            print(f"⚠️ Google Sheets init failed: {e}")
            return False
    
    def extract_emails_from_businesses(self, businesses):
        """
        OVERRIDES the original method to add Google Sheets upload.
        Your original logic is preserved, only adding upload.
        """
        if not businesses:
            print("❌ No businesses to scrape")
            return []
        
        leads = []
        total = len(businesses)
        self.stats["start_time"] = time.time()
        
        print(f"\n{'='*80}")
        print(f"🌐 Starting to scrape {total} businesses")
        print(f"📊 Google Sheets: {'✅ ACTIVE' if self.sheets_uploader else '❌ DISABLED'}")
        print(f"{'='*80}")
        
        for i, biz in enumerate(businesses, 1):
            url = biz['url']
            company = biz['title']
            description = biz.get('description', '')[:200] if biz.get('description') else ''
            
            print(f"\n[{i}/{total}] 🌐 Scraping: {company[:40]}...")
            print(f"   URL: {url[:70]}...")
            
            try:
                # Call your original scraper (unchanged)
                import asyncio
                result = asyncio.run(self.scraper.scrape_single_url(url))
                
                if result.get('success') and result.get('valid_emails'):
                    for email in result['valid_emails']:
                        leads.append({
                            'email': email,
                            'company': company,
                            'source_url': url,
                            'description': description,
                            'scraped_date': datetime.now().isoformat(),
                            'status': 'valid'
                        })
                        self.stats["total_emails_found"] += 1
                        
                        # =========================================================
                        # 🆕 GOOGLE SHEETS REAL-TIME UPLOAD - ADDED ONLY HERE
                        # =========================================================
                        if self.sheets_uploader:
                            try:
                                self.sheets_uploader.on_lead_found(
                                    email=email,
                                    company=company,
                                    source_url=url,
                                    description=description
                                )
                                print(f"   📊 Lead added to Google Sheets: {email}")
                            except Exception as e:
                                print(f"   ⚠️ Google Sheets error: {e}")
                        # =========================================================
                    
                    print(f"   ✅ Found {len(result['valid_emails'])} emails")
                elif result.get('success') and not result.get('valid_emails'):
                    print(f"   ℹ️ No emails found on this site")
                else:
                    error = result.get('error', 'Unknown error')
                    print(f"   ⚠️ Scrape issue: {error[:50]}")
                    
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}")
            
            self.stats["total_scraped"] = i
            
            if i % 10 == 0:
                print(f"\n📊 Progress: {i}/{total} businesses processed")
                print(f"📧 Emails found so far: {len(leads)}")
        
        self.stats["end_time"] = time.time()
        self.leads = leads
        return leads


# ============================================================================
# MAIN EXECUTION - SAME AS YOUR ORIGINAL main()
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ZOOMINFO GLOBAL B2B LEAD EXTRACTOR - WITH GOOGLE SHEETS REAL-TIME")
    print(" Your original scraper is 100% UNCHANGED")
    print(" Google Sheets uploads in REAL-TIME")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Your original menu (unchanged)
    industries = {
        '1': {'name': 'Electronics Distributors', 'industry': 'electronics distributor', 'location': 'Taiwan'},
        '2': {'name': 'HVAC Contractors', 'industry': 'HVAC contractor', 'location': 'USA'},
        '3': {'name': 'Real Estate Agents', 'industry': 'real estate agent', 'location': 'USA'},
        '4': {'name': 'Plumbing Contractors', 'industry': 'plumbing contractor', 'location': 'USA'},
        '5': {'name': 'Auto Parts Suppliers', 'industry': 'auto parts', 'location': 'USA'},
        '6': {'name': 'Custom Search - ANY Industry, ANY Location', 'industry': 'custom', 'location': 'custom'}
    }
    
    print("\n📌 Choose industry:")
    for key, value in industries.items():
        if key != '6':
            print(f"  {key}. {value['name']} ({value['location']})")
    print(f"  6. Custom Search")
    
    choice = input("\nEnter choice (1-6): ").strip()
    if choice not in industries:
        print("❌ Invalid choice")
        exit(1)
    
    selected = industries[choice]
    
    if choice == '6':
        print("\n🌍 ENTER ANY INDUSTRY AND LOCATION")
        print("   Examples:")
        print("   - Industry: 'plumber', Location: 'Texas'")
        print("   - Industry: 'auto parts', Location: 'USA'")
        print("   - Industry: 'electronics', Location: 'Taiwan'")
        print("   - Industry: 'contractor', Location: 'California'")
        
        industry = input("\nEnter industry: ").strip()
        location = input("Enter location: ").strip()
        
        if not industry or not location:
            print("❌ Industry and location are required")
            exit(1)
    else:
        industry = selected['industry']
        location = selected['location']
    
    print("\n📊 How many businesses to scrape?")
    print("  5 - Quick test")
    print("  10 - Small batch")
    print("  20 - Medium batch (recommended)")
    print("  50 - Large batch")
    print("  100 - Maximum")
    
    max_input = input("\nEnter number (5-100, default 20): ").strip()
    max_results = int(max_input) if max_input.isdigit() else 20
    max_results = max(1, min(max_results, 100))
    
    print(f"\n✅ Starting extraction with:")
    print(f"  Industry: {industry}")
    print(f"  Location: {location}")
    print(f"  Max Results: {max_results}")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        exit(0)
    
    try:
        # Use the extended extractor (your original code is still used)
        extractor = QuickLeadExtractorWithSheets()
        leads = extractor.run(industry=industry, location=location, max_results=max_results)
        
        print("\n" + "=" * 80)
        print("✅ EXTRACTION COMPLETE!")
        print("=" * 80)
        
        if leads:
            print(f"📁 Files saved:")
            print(f"  • JSON: leads_*.json")
            print(f"  • CSV: leads_*.csv")
            print(f"  • Google Sheets: REAL-TIME updates")
            print("\n📧 Sample leads:")
            for i, lead in enumerate(leads[:5], 1):
                print(f"  {i}. {lead['email']} - {lead['company']}")
            if len(leads) > 5:
                print(f"  ... and {len(leads) - 5} more")
        
        print("\n🕐 Completed at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped by user")
        exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your API token in .env file")
        print("  2. Make sure Redis is running: docker ps")
        print("  3. Check internet connection")
        print("  4. Verify GOOGLE_SHEET_ID in .env")
        exit(1)