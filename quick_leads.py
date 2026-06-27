# quick_leads.py - FINAL FIXED VERSION
import os
import asyncio
import json
import csv
import time
import logging
import requests
import re
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from scrapers.basic_scraper import BasicScraper
from config.settings import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)
load_dotenv()

class QuickLeadExtractor:
    def __init__(self):
        self.token = os.getenv("BRIGHTDATA_API_TOKEN")
        if not self.token:
            raise ValueError("❌ BRIGHTDATA_API_TOKEN not found in .env file!")
        
        self.serp_zone = os.getenv("SERP_API_ZONE", "serp_api1")
        self.web_unlocker_zone = os.getenv("WEB_UNLOCKER_ZONE", "web_unlocker1")
        
        print(f"🔑 Initializing Bright Data...")
        print(f"📍 SERP API Zone: {self.serp_zone}")
        print(f"📍 Web Unlocker Zone: {self.web_unlocker_zone}")
        
        self.scraper = BasicScraper()
        self.leads = []
        self.stats = {"total_searched": 0, "total_scraped": 0, "total_emails_found": 0, "start_time": None, "end_time": None}
    
    def api_request(self, zone, url, format_type="raw"):
        api_url = "https://api.brightdata.com/request"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"zone": zone, "url": url, "format": format_type}
        if format_type == "json":
            payload["data_format"] = "parsed"
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        return response
    
    def search_businesses_serp(self, industry, location, max_results=20):
        query = f"{industry} {location}"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={min(max_results, 10)}"
        
        print(f"\n🔍 Searching Google via SERP API: {query}")
        print(f"📊 Max results: {max_results}")
        
        try:
            response = self.api_request(self.serp_zone, search_url, "json")
            
            if not response or response.status_code != 200:
                print(f"  ❌ SERP API Error: {response.status_code if response else 'No response'}")
                return []
            
            # Parse JSON response
            data = response.json()
            print(f"  📌 Response keys: {list(data.keys())}")
            
            # The actual content is in 'body' field
            if 'body' in data:
                print("  📌 Found 'body' field - parsing content...")
                body_content = data['body']
                
                # If body is a string, try to parse it as JSON
                if isinstance(body_content, str):
                    try:
                        body_content = json.loads(body_content)
                    except:
                        pass
                
                # Now extract organic results from the body
                businesses = []
                
                # Try different paths
                if isinstance(body_content, dict):
                    organic_results = body_content.get('organic', []) or body_content.get('results', []) or body_content.get('items', [])
                    
                    for item in organic_results:
                        url = item.get('link', '') or item.get('url', '')
                        if url and url.startswith('http'):
                            businesses.append({
                                'title': item.get('title', 'No Title'),
                                'url': url,
                                'description': item.get('snippet', 'No Description') or item.get('description', '')
                            })
                            if len(businesses) >= max_results:
                                break
                
                # If still no results, try to find any list
                if not businesses and isinstance(body_content, dict):
                    for key, value in body_content.items():
                        if isinstance(value, list) and len(value) > 0:
                            print(f"  📌 Found list in '{key}'")
                            for item in value:
                                if isinstance(item, dict):
                                    url = item.get('link', '') or item.get('url', '')
                                    if url and url.startswith('http'):
                                        businesses.append({
                                            'title': item.get('title', 'No Title'),
                                            'url': url,
                                            'description': item.get('snippet', 'No Description')
                                        })
                                        if len(businesses) >= max_results:
                                            break
                            break
                
                self.stats["total_searched"] = len(businesses)
                print(f"✅ SERP API found {len(businesses)} businesses")
                
                if businesses:
                    print("\n📋 Sample businesses found:")
                    for i, biz in enumerate(businesses[:5], 1):
                        print(f"  {i}. {biz['title'][:50]}...")
                        print(f"     {biz['url'][:60]}...")
                
                return businesses
            else:
                print("  ❌ No 'body' field found in response")
                return []
            
        except Exception as e:
            print(f"  ❌ SERP API failed: {e}")
            import traceback
            print(traceback.format_exc())
            return []
    
    def search_businesses_web_unlocker(self, industry, location, max_results=20):
        query = f"{industry} {location}"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={max_results}"
        
        print(f"\n🔍 Searching via Web Unlocker: {query}")
        
        try:
            response = self.api_request(self.web_unlocker_zone, search_url, "raw")
            
            if not response or response.status_code != 200:
                print(f"  ❌ Web Unlocker Error: {response.status_code if response else 'No response'}")
                return []
            
            html = response.text
            businesses = []
            
            # Parse Google search results
            url_pattern = re.compile(r'<a[^>]+href="(/url\?q=[^&"]+)"[^>]*>([^<]+)</a>', re.IGNORECASE)
            matches = url_pattern.findall(html)
            
            for href, title in matches:
                if href.startswith('/url?q='):
                    actual_url = href.replace('/url?q=', '').split('&')[0]
                    actual_url = urllib.parse.unquote(actual_url)
                    
                    if 'google.com' not in actual_url and actual_url.startswith('http'):
                        businesses.append({
                            'title': title.strip()[:100] if title.strip() else 'No Title',
                            'url': actual_url,
                            'description': 'Found via Google search'
                        })
                        if len(businesses) >= max_results:
                            break
            
            # Remove duplicates
            seen = set()
            unique_businesses = []
            for biz in businesses:
                if biz['url'] not in seen:
                    seen.add(biz['url'])
                    unique_businesses.append(biz)
            
            businesses = unique_businesses[:max_results]
            self.stats["total_searched"] = len(businesses)
            print(f"✅ Web Unlocker found {len(businesses)} businesses")
            return businesses
            
        except Exception as e:
            print(f"  ❌ Web Unlocker search failed: {e}")
            return []
    
    def extract_emails_from_businesses(self, businesses):
        if not businesses:
            print("❌ No businesses to scrape")
            return []
        
        leads = []
        total = len(businesses)
        self.stats["start_time"] = time.time()
        
        print(f"\n{'='*80}")
        print(f"🌐 Starting to scrape {total} businesses")
        print(f"{'='*80}")
        
        for i, biz in enumerate(businesses, 1):
            url = biz['url']
            company = biz['title']
            description = biz.get('description', '')[:200] if biz.get('description') else ''
            
            print(f"\n[{i}/{total}] 🌐 Scraping: {company[:40]}...")
            print(f"   URL: {url[:70]}...")
            
            try:
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
    
    def save_to_json(self, leads, filename=None):
        if not leads:
            print("❌ No leads to save")
            return None
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"leads_{timestamp}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved {len(leads)} leads to {filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")
            return None
    
    def save_to_csv(self, leads, filename=None):
        if not leads:
            print("❌ No leads to save")
            return None
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"leads_{timestamp}.csv"
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Email', 'Company', 'Source URL', 'Description', 'Scraped Date', 'Status'])
                for lead in leads:
                    writer.writerow([
                        lead.get('email', ''),
                        lead.get('company', ''),
                        lead.get('source_url', ''),
                        lead.get('description', ''),
                        lead.get('scraped_date', ''),
                        lead.get('status', '')
                    ])
            print(f"📊 Saved {len(leads)} leads to {filename}")
            return filename
        except Exception as e:
            print(f"❌ Failed to save CSV: {e}")
            return None
    
    def display_summary(self):
        elapsed = self.stats["end_time"] - self.stats["start_time"] if self.stats["start_time"] else 0
        minutes = elapsed / 60 if elapsed > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"📊 EXTRACTION SUMMARY")
        print(f"{'='*80}")
        print(f"  🔍 Businesses searched: {self.stats['total_searched']}")
        print(f"  🌐 Businesses scraped: {self.stats['total_scraped']}")
        print(f"  📧 Total emails found: {self.stats['total_emails_found']}")
        print(f"  📁 Unique leads: {len(self.leads)}")
        print(f"  ⏱️  Time elapsed: {minutes:.2f} minutes")
        if minutes > 0:
            print(f"  🚀 Speed: {len(self.leads) / minutes:.2f} leads per minute")
        print(f"{'='*80}")
    
    def run(self, industry, location, max_results=20):
        print(f"\n{'='*80}")
        print(f"🚀 B2B LEAD EXTRACTOR")
        print(f"{'='*80}")
        print(f"  📌 Industry: {industry}")
        print(f"  📌 Location: {location}")
        print(f"  📌 Max Results: {max_results}")
        print(f"  ⚡ Concurrent Requests: {settings.MAX_CONCURRENT_REQUESTS}")
        print(f"  📍 SERP API Zone: {self.serp_zone}")
        print(f"  📍 Web Unlocker Zone: {self.web_unlocker_zone}")
        print(f"{'='*80}")
        
        # Try SERP API
        businesses = self.search_businesses_serp(industry, location, max_results)
        
        # If SERP API fails, try Web Unlocker
        if not businesses:
            print("\n📌 SERP API found 0 results. Trying Web Unlocker as fallback...")
            businesses = self.search_businesses_web_unlocker(industry, location, max_results)
        
        if not businesses:
            print("❌ No businesses found")
            print("\n💡 Tips:")
            print("  1. Try a different industry (e.g., 'plumber', 'electronics')")
            print("  2. Try a different location (e.g., 'Texas', 'California')")
            print("  3. Check your Bright Data credits at: https://brightdata.com/billing")
            return []
        
        # Extract emails
        leads = self.extract_emails_from_businesses(businesses)
        
        if leads:
            self.save_to_json(leads)
            self.save_to_csv(leads)
        else:
            print("❌ No leads found")
        
        self.display_summary()
        return leads

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("📋 B2B LEAD EXTRACTOR - FINAL FIXED VERSION")
    print("✅ SERP API + Web Unlocker API")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
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
        extractor = QuickLeadExtractor()
        leads = extractor.run(industry=industry, location=location, max_results=max_results)
        
        print("\n" + "=" * 80)
        print("✅ EXTRACTION COMPLETE!")
        print("=" * 80)
        
        if leads:
            print(f"📁 Files saved:")
            print(f"  • JSON: leads_*.json")
            print(f"  • CSV: leads_*.csv")
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
        exit(1)
