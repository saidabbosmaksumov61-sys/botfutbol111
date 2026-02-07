from api import FootballAPI
import json

def verify_team_filtering():
    api = FootballAPI()
    matches = api.get_all_matches()
    
    print(f"--- Verification for Date: {matches[0].get('date', 'Today') if matches else 'No matches'} ---")
    print(f"Total Filtered matches: {len(matches)}")
    
    for m in matches:
        print(f"[{m['league']}] {m['home']} vs {m['away']} | Score: {m['score']} | Time: {m['match_time']} | Live: {m['is_live']}")
        
    if not matches:
        print("No Top-5 teams found playing today in any competition.")

if __name__ == "__main__":
    verify_team_filtering()
