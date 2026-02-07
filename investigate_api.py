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
        if params is None:
            params = {}
        params["_"] = int(datetime.now().timestamp() * 1000)
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_standings(self, league_id):
        data = self._get("leagues", {"id": league_id})
        if data and "table" in data and data["table"]:
            tables = data["table"][0]["data"]["table"]["all"]
            # Print first item to see structure
            print("Standings Entry Sample:")
            print(json.dumps(tables[0], indent=2))
        else:
            print("No standings found")

    def get_matches(self, team_id):
        # Using a popular team ID, e.g. Man Utd 10260, or just generic matches
        data = self._get("teams", {"id": team_id})
        if data and "fixtures" in data:
            all_fixtures = data["fixtures"].get("allFixtures", {}).get("fixtures", [])
            print("Match Entry Sample:")
            if all_fixtures:
                # Find a finished or live match
                for m in all_fixtures:
                    status = m.get("status", {})
                    if status.get("finished") or status.get("started"):
                        print(json.dumps(m, indent=2))
                        break
api = FootballAPI()
print("--- PREMIER LEAGUE STANDINGS ---")
api.get_standings(47) # Premier League
print("\n--- MATCH DETAILS ---")
api.get_matches(47) # Man City ID is 8456? Wait 47 is league.
# Let's use a team ID. 
# Arsenal: 9825, Man City: 8456
api.get_matches(8456)
