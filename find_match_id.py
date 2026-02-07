from api import FootballAPI
api = FootballAPI()
teams = api.get_teams(47) # Premier League
if teams:
    team_id = teams[0]['id']
    matches = api.get_matches(team_id, "past")
    if matches:
        print(f"Recent match ID: {matches[-1]['id']} ({matches[-1]['home']} vs {matches[-1]['away']})")
    else:
        print("No past matches found.")
else:
    print("No teams found.")
