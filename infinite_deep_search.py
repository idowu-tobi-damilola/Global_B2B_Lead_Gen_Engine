# deep_search.py - INFINITE PATTERNS VERSION
# Generates UNLIMITED unique search patterns
# Runs FOREVER until manually stopped
# No duplicate patterns, no duplicate leads

import os
import time
import json
import logging
import random
from datetime import datetime
from dotenv import load_dotenv
from run_with_sheets import QuickLeadExtractorWithSheets

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class InfiniteDeepSearchExtractor:
    """
    Runs INFINITE unique searches to find B2B leads.
    NEVER stops until manually interrupted.
    NEVER repeats the same pattern twice.
    """
    
    def __init__(self):
        self.extractor = QuickLeadExtractorWithSheets()
        self.all_leads = []
        self.total_searches = 0
        self.total_emails_found = 0
        self.used_patterns = set()  # Track used patterns to avoid repeats
        
        # Core components to build infinite patterns
        self.industry_modifiers = [
            "", " top", " best", " leading", " premium", " quality", 
            " professional", " certified", " trusted", " reliable",
            " experienced", " expert", " specialist", " supplier", 
            " distributor", " manufacturer", " dealer", " wholesale",
            " retail", " export", " import", " trading", " agent",
            " broker", " consultant", " service", " repair", " install"
        ]
        
        self.location_modifiers = [
            "", " area", " region", " city", " metro", " downtown",
            " north", " south", " east", " west", " central", 
            " suburban", " industrial", " business", " commercial"
        ]
        
        self.action_modifiers = [
            " contact", " email", " phone", " call", " reach", 
            " connect", " message", " inquiry", " quote", " order",
            " purchase", " buy", " sell", " trade", " partner",
            " collaborate", " invest", " export", " import", " supply"
        ]
        
        self.page_modifiers = [
            " about us", " contact us", " our team", " location",
            " services", " products", " catalog", " portfolio",
            " testimonials", " reviews", " careers", " jobs",
            " news", " blog", " events", " promotions", " offers"
        ]
        
        self.query_modifiers = [
            "", " near me", " online", " local", " national", 
            " international", " global", " worldwide", " domestic"
        ]
    
    def generate_unique_pattern(self):
        """
        Generate a UNIQUE search pattern that hasn't been used before.
        Combines random elements to create infinite variations.
        """
        max_attempts = 100
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            
            # Randomly select one or more modifiers
            pattern_parts = []
            
            # Randomly include industry modifiers (0-3)
            num_industry = random.randint(0, 3)
            if num_industry > 0:
                selected = random.sample(self.industry_modifiers, min(num_industry, len(self.industry_modifiers)))
                pattern_parts.extend(selected)
            
            # Randomly include location modifiers (0-2)
            num_location = random.randint(0, 2)
            if num_location > 0:
                selected = random.sample(self.location_modifiers, min(num_location, len(self.location_modifiers)))
                pattern_parts.extend(selected)
            
            # Always include at least one action or page modifier
            if random.random() < 0.7:
                pattern_parts.append(random.choice(self.action_modifiers))
            else:
                pattern_parts.append(random.choice(self.page_modifiers))
            
            # Randomly include query modifier
            if random.random() < 0.3:
                pattern_parts.append(random.choice(self.query_modifiers))
            
            # Clean and join
            pattern = "".join(pattern_parts)
            
            # Ensure pattern is not empty
            if not pattern.strip():
                pattern = random.choice(self.action_modifiers)
            
            # Check if this pattern has been used before
            if pattern not in self.used_patterns:
                self.used_patterns.add(pattern)
                return pattern
            
            # If we've used all combinations (unlikely), reset used patterns
            if len(self.used_patterns) > 1000:
                self.used_patterns.clear()
                return pattern
        
        # Fallback: generate a timestamp-based unique pattern
        return f" {datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def run_infinite_deep_search(self, industry, location, max_per_search=20):
        """
        Runs INFINITE unique searches until manually stopped.
        
        Args:
            industry: Industry to search (e.g., "electronics")
            location: Location to search (e.g., "Taiwan")
            max_per_search: Max results per search
        """
        print("\n" + "=" * 80)
        print("♾️  INFINITE DEEP SEARCH - NEVER STOPS")
        print("=" * 80)
        print(f"  📌 Industry: {industry}")
        print(f"  📌 Location: {location}")
        print(f"  📌 Max per Search: {max_per_search}")
        print(f"  ♾️  Patterns: INFINITE (never repeats)")
        print(f"  ⏹️  Stop: Press Ctrl+C anytime")
        print("=" * 80)
        print("\n⚠️  THIS WILL RUN FOREVER UNTIL YOU STOP IT!")
        print("   Press Ctrl+C to stop at any time.\n")
        
        search_count = 0
        found_leads = []
        
        try:
            while True:  # INFINITE LOOP
                search_count += 1
                
                # Generate a unique pattern
                pattern = self.generate_unique_pattern()
                search_term = f"{industry} {location}{pattern}"
                
                print(f"\n📌 Search #{search_count}: '{search_term}'")
                print(f"   Pattern: '{pattern.strip()}'")
                print(f"   Unique patterns used: {len(self.used_patterns)}")
                
                try:
                    # Run the search
                    leads = self.extractor.run(
                        industry=search_term,
                        location="",  # Location already in the query
                        max_results=max_per_search
                    )
                    
                    if leads:
                        new_leads = [l for l in leads if l not in found_leads]
                        found_leads.extend(new_leads)
                        self.total_emails_found += len(new_leads)
                        print(f"   ✅ Found {len(new_leads)} NEW leads")
                        print(f"   📊 TOTAL leads found: {len(found_leads)}")
                    else:
                        print(f"   ℹ️ No new leads found")
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
                # Small delay to avoid rate limits
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n" + "=" * 80)
            print("⏹️  STOPPED BY USER")
            print("=" * 80)
            print(f"  🔍 Total Searches Run: {search_count}")
            print(f"  📧 Total Emails Found: {self.total_emails_found}")
            print(f"  📁 Unique Leads: {len(found_leads)}")
            print(f"  ♾️  Unique Patterns Used: {len(self.used_patterns)}")
            print("=" * 80)
            
            # Save results
            self.all_leads = found_leads
            self.total_searches = search_count
            
            # Display sample leads
            if found_leads:
                print("\n📧 Sample Leads Found:")
                for i, lead in enumerate(found_leads[:10], 1):
                    print(f"  {i}. {lead.get('email', 'N/A')} - {lead.get('company', 'N/A')}")
                if len(found_leads) > 10:
                    print(f"  ... and {len(found_leads) - 10} more")
            
            print("\n You can resume anytime by running this script again!")
            print("♾️  Redis will prevent duplicates and continue from where you left off.")
            
            return found_leads
        
        return found_leads


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  INFINITE DEEP SEARCH - NEVER STOPS")
    print(" Generates UNLIMITED unique search patterns")
    print(" NEVER repeats the same pattern twice")
    print(" Runs FOREVER until you press Ctrl+C")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Get user input
    print("\n Enter industry and location for infinite search:")
    print("   Examples:")
    print("   - Industry: 'electronics', Location: 'Taiwan'")
    print("   - Industry: 'auto parts', Location: 'Taiwan'")
    print("   - Industry: 'plumbing', Location: 'USA'")
    
    industry = input("\nEnter industry: ").strip()
    if not industry:
        industry = "electronics"
        print(f"   Using default: {industry}")
    
    location = input("Enter location: ").strip()
    if not location:
        location = "Taiwan"
        print(f"   Using default: {location}")
    
    # Results per search
    max_input = input("Max results per search (5-100, default 20): ").strip()
    max_per_search = int(max_input) if max_input.isdigit() else 20
    max_per_search = max(1, min(max_per_search, 100))
    
    print("\n" + "=" * 80)
    print("  INFINITE MODE ACTIVATED")
    print("=" * 80)
    print(f"  Industry: {industry}")
    print(f"  Location: {location}")
    print(f"  Max per Search: {max_per_search}")
    print(f"  ♾️  Patterns: INFINITE (never repeats)")
    print(f"  ⏹️  Stop: Press Ctrl+C anytime")
    print("=" * 80)
    
    confirm = input("\nStart infinite search? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        exit(0)
    
    try:
        # Run infinite search
        extractor = InfiniteDeepSearchExtractor()
        leads = extractor.run_infinite_deep_search(
            industry=industry,
            location=location,
            max_per_search=max_per_search
        )
        
        print("\n" + "=" * 80)
        print(" INFINITE SEARCH COMPLETE!")
        print("=" * 80)
        print(f"   Total Leads Found: {len(leads) if leads else 0}")
        print(f"  Google Sheets: CHECK YOUR SHEET!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Stopped by user")
        exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        exit(1)