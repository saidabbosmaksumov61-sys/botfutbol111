from api import FootballAPI
import json

def get_top_5_teams():
    api = FootballAPI()
    leagues = [47, 87, 54, 55, 53]
    all_team_ids = set()
    
    for l_id in leagues:
        teams = api.get_teams(l_id)
        for t in teams:
            all_team_ids.add(t['id'])
    
    # Save to a file for easy access by other parts of the bot
    with open("top_5_teams.json", "w") as f:
        json.dump(list(all_team_ids), f)
    
    print(f"Fetched {len(all_team_ids)} teams from Top-5 leagues.")

if __name__ == "__main__":
    get_top_5_teams()
