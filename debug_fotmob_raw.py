import requests
import json
from datetime import datetime

base_url = "https://www.fotmob.com/api/data/matches"
date_str = datetime.now().strftime("%Y%m%d")
params = {"date": date_str}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

response = requests.get(base_url, headers=headers, params=params)
data = response.json()

live_matches = []
for league in data.get("leagues", []):
    for m in league.get("matches", []):
        if m.get("status", {}).get("started") and not m.get("status", {}).get("finished"):
            live_matches.append(m)

if live_matches:
    print(f"Found {len(live_matches)} live matches.")
    for m in live_matches:
        status = m.get("status", {})
        print(f"\nMatch: {m.get('home', {}).get('name')} vs {m.get('away', {}).get('name')}")
        print(f"Status Object: {json.dumps(status, indent=2)}")
else:
    print("No live matches found right now.")
