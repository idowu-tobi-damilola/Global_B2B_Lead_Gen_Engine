
# Does NOT modify your original files

import sys
from expiration import ExpirationManager

# Check if system is still active
mgr = ExpirationManager()
if not mgr.is_active():
    print("\n" + "=" * 60)
    print("🔒 SERVICE EXPIRED")
    print("=" * 60)
    print(mgr.get_message())
    print("=" * 60)
    sys.exit(0)

# If active, run your scraper
print("✅ System active. Starting scraper...")
exec(open("run_with_sheets.py").read())