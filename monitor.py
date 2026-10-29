import requests
import re
import json

TARGET_URL = "https://www.opentix.life/event/2072537230141886465"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
}

print(f"Fetching {TARGET_URL}...", flush=True)
res = requests.get(TARGET_URL, headers=headers, timeout=15)
print(f"Status Code: {res.status_code}", flush=True)

# 1. Check if Nuxt state data exists inside the HTML
if "window.__NUXT__" in res.text:
    print("Found window.__NUXT__ in HTML!", flush=True)
    # Find snippets containing ticket or seat terms
    matches = re.findall(r'.{0,50}(?:remainingTickets|pricePlans|performances|price).{0,50}', res.text)
    print(f"Found {len(matches)} matches around ticket keywords. First few:")
    for m in matches[:5]:
        print(f"  -> {m.strip()}")
else:
    print("No __NUXT__ state found in HTML.")

# 2. Check for any internal API paths mentioned in the source scripts
api_matches = list(set(re.findall(r'https?://[a-zA-Z0-9.\-_/]*(?:api|oapi|programs|events)[a-zA-Z0-9.\-_/]*', res.text)))
print(f"\nFound {len(api_matches)} API URLs inside the page scripts:")
for url in api_matches[:10]:
    print(f"  * {url}")
