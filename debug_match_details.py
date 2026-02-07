import requests
import json
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
        except Exception as e:
            print(f"Error: {e}")
            return None

    def debug_search_live(self):
        # 1. Try to find ANY live match in Top 5 leagues
        date_str = datetime.now().strftime("%Y%m%d")
        data = self._get("data/matches", {"date": date_str})
        
        found = False
        if data and "leagues" in data:
            for league in data["leagues"]:
                for m in league.get("matches", []):
                    status = m.get("status", {})
                    if status.get("started") and not status.get("finished"):
                        print(f"\n--- LIVE MATCH FOUND: {m['home']['name']} vs {m['away']['name']} ---")
                        print(json.dumps(status, indent=4))
                        found = True
                        break
                if found: break
        
        if not found:
            print("No live matches found in general list. Checking specific team fixtures...")
            # 2. Check a big team's fixtures (e.g. Real Madrid 8633) to see structure even if not live
            data = self._get("teams", {"id": 8633})
            if data and "fixtures" in data:
                fixtures = data["fixtures"].get("allFixtures", {}).get("fixtures", [])
                if fixtures:
                    m = fixtures[0] # Next match
                    print(f"\n--- NEXT MATCH FIXTURE: {m['home']['name']} vs {m['away']['name']} ---")
                    print(json.dumps(m.get("status", {}), indent=4))

if __name__ == "__main__":
    api = FootballAPI()
    api.debug_search_live()
