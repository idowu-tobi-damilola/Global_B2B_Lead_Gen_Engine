# test_sdk.py - Test Bright Data SDK methods
import os
from dotenv import load_dotenv
from brightdata import SyncBrightDataClient

load_dotenv()

token = os.getenv("BRIGHTDATA_API_TOKEN")
print(f"Token: {token[:20]}...")

client = SyncBrightDataClient(token=token)

# List available methods
print("\n📋 Available methods:")
methods = [m for m in dir(client) if not m.startswith('_')]
for method in methods:
    print(f"  - {method}")

# Try to find search-related methods
print("\n🔍 Search-related methods:")
search_methods = [m for m in methods if 'search' in m.lower() or 'google' in m.lower()]
for method in search_methods:
    print(f"  ✅ {method}")

# Try to use the search
print("\n🌐 Trying to search...")
try:
    # Try different approaches
    if hasattr(client, 'search'):
        print("  ✅ 'search' attribute exists")
        if callable(client.search):
            print("  ✅ 'search' is callable")
        else:
            print("  ⚠️ 'search' is NOT callable")
            print(f"  Type: {type(client.search)}")
    
    if hasattr(client, 'google_search'):
        print("  ✅ 'google_search' attribute exists")
    
    if hasattr(client, 'search_google'):
        print("  ✅ 'search_google' attribute exists")
        
except Exception as e:
    print(f"  ❌ Error: {e}")
