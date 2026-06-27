# protected_infinite_deep_search.py - Protected version with expiration check
# This file wraps your existing scraper with expiration control

import sys
from expiration import check_expiration

# Check if system is still active
if not check_expiration():
    print("\n" + "=" * 60)
    print("🔒 SERVICE EXPIRED")
    print("=" * 60)
    print("This service has expired. Please contact the provider.")
    print("=" * 60)
    sys.exit(0)

# If active, run your scraper
print("✅ System active. Starting scraper...")

# Read and execute with proper encoding
with open("infinite_deep_search.py", "r", encoding="utf-8") as f:
    exec(f.read())
