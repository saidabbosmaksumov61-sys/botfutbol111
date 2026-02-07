from api import FootballAPI
from datetime import datetime, timedelta

def debug_count():
    api = FootballAPI()
    today = datetime.now()
    dates = [
        (today - timedelta(days=1)).strftime("%Y%m%d"),
        today.strftime("%Y%m%d"),
        (today + timedelta(days=1)).strftime("%Y%m%d")
    ]
    
    total_matches = 0
    
    for d in dates:
        print(f"Fetching {d}...")
        data = api._get("data/matches", {"date": d})
        if data and "leagues" in data:
            day_matches = 0
            for league in data["leagues"]:
                matches = league.get("matches", [])
                day_matches += len(matches)
                for m in matches:
                    if m['status'].get('started') and not m['status'].get('finished'):
                        print(f"LIVE FOUND! {m['home']['name']} vs {m['away']['name']} (ID: {m['id']})")
            print(f"  Matches: {day_matches}")
            total_matches += day_matches
        else:
             print("  No data/leagues found.")
             
    print(f"Total Matches scanned: {total_matches}")

if __name__ == "__main__":
    debug_count()
