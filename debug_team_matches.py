import json
from api import FootballAPI

api = FootballAPI()
# 8650 is Liverpool, 10260 is Man Utd. Let's try Man Utd.
team_id = 10260 

# We need to call the internal _get method to see raw data, 
# because get_matches filters it.
print(f"Fetching data for team {team_id}...")
data = api._get("teams", {"id": team_id})

if data and "fixtures" in data:
    all_fixtures = data["fixtures"].get("allFixtures", {}).get("fixtures", [])
    if all_fixtures:
        first_match = all_fixtures[0]
        print("First match object keys:", first_match.keys())
        print(json.dumps(first_match, indent=2))
    else:
        print("No fixtures found.")
else:
    print("No data found or fixtures missing.")
