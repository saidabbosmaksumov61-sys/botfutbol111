from api import FootballAPI
import json

def debug_raw():
    api = FootballAPI()
    print("Fetching ALL matches (Yesterday/Today/Tomorrow)...")
    matches = api.get_all_matches()
    live = [m for m in matches if m['is_live']]
    
    print(f"Found {len(live)} LIVE matches.")
    
    if live:
        print("--- Inspecting First Live Match (Processed) ---")
        print(json.dumps(live[0], indent=2))
        
        # Now let's try to get raw data for this match ID to see where time is hidden
        match_id = live[0]['id']
        print(f"\n--- Fetching Raw MatchDetails for ID {match_id} ---")
        # We can't easily get raw response from existing methods without modifying them or using _get directly
        # utilizing _get publically here (it's python, so we can)
        raw_details = api._get("matchDetails", {"matchId": match_id})
        
        if raw_details and 'header' in raw_details:
             status = raw_details['header'].get('status', {})
             print("\nRaw Header Status Object:")
             print(json.dumps(status, indent=2))
        else:
             print("Could not get matchDetails header.")

if __name__ == "__main__":
    debug_raw()
