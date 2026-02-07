from api import FootballAPI
from datetime import datetime, timedelta

def debug_live_matches():
    api = FootballAPI()
    
    # 1. Check Today
    today = datetime.now()
    today_str = today.strftime("%Y%m%d")
    print(f"--- Checking Matches for TODAY ({today_str}) ---")
    matches_today = api.get_all_matches(today_str)
    live_today = [m for m in matches_today if m['is_live']]
    print(f"Found {len(matches_today)} matches, {len(live_today)} LIVE.")
    for m in live_today:
        print(f"LIVE: {m['home']} vs {m['away']} - {m['match_time']} (ID: {m['id']})")
        
    # 2. Check Yesterday
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y%m%d")
    print(f"\n--- Checking Matches for YESTERDAY ({yesterday_str}) ---")
    matches_yesterday = api.get_all_matches(yesterday_str)
    live_yesterday = [m for m in matches_yesterday if m['is_live']]
    print(f"Found {len(matches_yesterday)} matches, {len(live_yesterday)} LIVE.")
    for m in live_yesterday:
        # Use simple formatting to avoid unicode errors in windows console if encoding issues arise
        try:
            print(f"LIVE: {m['home']} vs {m['away']} - {m['match_time']} (ID: {m['id']})")
        except:
            print(f"LIVE: {m['home'].encode('utf-8')} vs {m['away'].encode('utf-8')} - {m['match_time']} (ID: {m['id']})")

    if not live_today and not live_yesterday:
        print("\n[WARNING] No LIVE matches found in Top 5 leagues cache.")

if __name__ == "__main__":
    debug_live_matches()
