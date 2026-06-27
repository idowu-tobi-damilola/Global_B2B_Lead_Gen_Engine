# main.py
import asyncio
import logging
import sys
from scrapers.basic_scraper import BasicScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

async def main():
    print("=" * 80)
    print("B2B LEAD SCRAPER")
    print("Keeps ALL emails EXCEPT gmail.com and yahoo.com")
    print("=" * 80)
    
    test_urls = [
        "https://httpbin.org/anything/test",
    ]
    
    print("\nChoose an option:")
    print("  1. Test with demo URL (httpbin.org)")
    print("  2. Test with a real website")
    print("  3. Test multiple URLs")
    print("  4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == '1':
        pass
    elif choice == '2':
        custom_url = input("Enter URL to scrape: ").strip()
        if custom_url:
            test_urls = [custom_url]
    elif choice == '3':
        print("\nEnter URLs (one per line, empty line to finish):")
        custom_urls = []
        while True:
            url = input().strip()
            if not url:
                break
            custom_urls.append(url)
        if custom_urls:
            test_urls = custom_urls
    elif choice == '4':
        print("Exiting...")
        return
    
    print("\n" + "=" * 80)
    print(f"Will scrape {len(test_urls)} URL(s):")
    for i, url in enumerate(test_urls, 1):
        print(f"  {i}. {url}")
    print("=" * 80 + "\n")
    
    scraper = BasicScraper()
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(test_urls)}] Processing: {url}")
        print('='*80)
        
        result = await scraper.scrape_single_url(url)
        
        print(f"\nResults for: {url}")
        print(f"  Success: {'Yes' if result['success'] else 'No'}")
        print(f"  Total emails found: {len(result['all_emails'])}")
        print(f"  Valid emails (kept): {len(result['valid_emails'])}")
        print(f"  Excluded (gmail/yahoo): {len(result['excluded_emails'])}")
        
        if result['valid_emails']:
            print("\n  VALID EMAILS FOUND:")
            for email in result['valid_emails'][:20]:
                company = scraper.email_filter.get_company_from_email(email)
                print(f"    {email} (Company: {company})")
            if len(result['valid_emails']) > 20:
                print(f"    ... and {len(result['valid_emails']) - 20} more")
        
        if result['excluded_emails']:
            print("\n  EXCLUDED (gmail.com / yahoo.com):")
            for email in result['excluded_emails'][:5]:
                print(f"    {email}")
            if len(result['excluded_emails']) > 5:
                print(f"    ... and {len(result['excluded_emails']) - 5} more")
        
        if result['error']:
            print(f"\n  Note: {result['error']}")
    
    print("\n" + "=" * 80)
    print("Scraping complete!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nStopped by user")
        sys.exit(0)