from api import FootballAPI
import json

def test():
    api = FootballAPI()
    
    print("Testing get_teams (League 47 - PL)...")
    teams = api.get_teams(47) # Premier League
    print(f"Found {len(teams)} teams.")
    if teams:
        print(f"Sample Team: {teams[0]}")
        
        team_id = teams[0]['id']
        print(f"\nTesting get_matches for team {team_id}...")
        matches = api.get_matches(team_id, "upcoming")
        print(f"Found {len(matches)} upcoming matches.")
        if matches:
            print(f"Sample Match: {matches[0]}")
            
    else:
        print("FAILED to get teams.")

if __name__ == "__main__":
    test()
