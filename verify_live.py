import asyncio
from api import FootballAPI
import database
from datetime import datetime

async def test_live_tracking():
    api = FootballAPI()
    database.init_db()
    
    print(f"Testing live tracking at {datetime.now()}...")
    matches = api.get_all_matches()
    live = [m for m in matches if m['is_live']]
    
    print(f"Total matches today: {len(matches)}")
    print(f"Live matches: {len(live)}")
    
    for m in live:
        print(f"LIVE: {m['home']} {m['score']} {m['away']} (ID: {m['id']})")
        # Check if we can get events
        events = api.get_match_events(m['id'])
        print(f"  Events: {events}")
        
    if not live:
        print("No live matches right now. Testing with a finished match if possible.")
        finished = [m for m in matches if m['is_finished']]
        if finished:
            m = finished[0]
            print(f"FINISHED (Mock Live): {m['home']} {m['score']} {m['away']} (ID: {m['id']})")
            events = api.get_match_events(m['id'])
            print(f"  Events: {events}")

if __name__ == "__main__":
    asyncio.run(test_live_tracking())
