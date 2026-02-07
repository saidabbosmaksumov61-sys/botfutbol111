import requests
import json
import os
from datetime import datetime

class FootballAPI:
    def __init__(self):
        self.base_url = "https://www.fotmob.com/api"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def _get(self, endpoint, params=None):
        if params is None: params = {}
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            return response.json()
        except:
            return None

    def find_live(self):
        try:
            with open("top_5_teams.json", "r") as f:
                team_ids = json.load(f)
        except:
            print("No teams file")
            return

        print(f"Checking {len(team_ids)} teams for live matches...")
        
        # Check first 50 teams to save time/rate limits
        for tid in team_ids[:50]: 
            data = self._get("teams", {"id": tid})
            if not data or "fixtures" not in data: continue
            
            fixtures = data["fixtures"].get("allFixtures", {}).get("fixtures", [])
            for m in fixtures:
                status = m.get("status", {})
                if status.get("started") and not status.get("finished"):
                    print(f"\nFOUND LIVE MATCH: {m['home']['name']} vs {m['away']['name']}")
                    print(json.dumps(status, indent=4))
                    return
        print("No live matches found in sample.")

if __name__ == "__main__":
    api = FootballAPI()
    api.find_live()
