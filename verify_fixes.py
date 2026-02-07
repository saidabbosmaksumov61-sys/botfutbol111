import asyncio
from api import FootballAPI
from unittest.mock import MagicMock
import time

async def verify():
    print("--- Verifying API Changes ---")
    api = FootballAPI()
    
    # 1. Verify get_matches includes 'id'
    print("Fetching PL teams...")
    teams = api.get_teams(47)
    if not teams:
        print("SKIP: No teams found (API might be blocking or empty).")
    else:
        team_id = teams[0]['id']
        print(f"Fetching matches for Team {team_id}...")
        matches = api.get_matches(team_id, "past") # Use past to ensure we get data
        if matches:
            first_match = matches[0]
            if "id" in first_match:
                print(f"[PASS] Match object has 'id': {first_match['id']}")
            else:
                print(f"[FAIL] Match object missing 'id'. Keys: {first_match.keys()}")
                
            # 2. Verify get_match_events
            match_id = first_match['id']
            print(f"Fetching events for match {match_id}...")
            # We don't guarantee this match has goals, but method should run
            events = api.get_match_events(match_id)
            print(f"Events type: {type(events)}")
            print(f"Events found: {events}")
            print("[PASS] get_match_events executed without error.")
        else:
            print("[WARNING] No past matches found to verify ID.")

    print("\n--- Verifying Middleware Logic (Mock) ---")
    from middlewares import SubscriptionMiddleware
    
    # Mock Objects
    middleware = SubscriptionMiddleware()
    handler = MagicMock(return_value="Passed")
    event = MagicMock()
    event.from_user.id = 12345
    
    # Mock Bot
    bot = MagicMock()
    # Mock get_chat_member to fail (raise exception) to test Fail Open
    bot.get_chat_member.side_effect = Exception("API Error")
    
    data = {"bot": bot}
    
    result = await middleware(handler, event, data)
    
    if result == "Passed":
        print("[PASS] Middleware failed open on API error.")
    else:
        print(f"[FAIL] Middleware blocked user on API error. Result: {result}")

    # Test Caching
    # Now bot.get_chat_member should succeed
    bot.get_chat_member.side_effect = None
    bot.get_chat_member.return_value.status = "member"
    
    # First call - should cache
    await middleware(handler, event, data)
    
    # Now make API fail again, but cache should allow pass
    bot.get_chat_member.reset_mock()
    bot.get_chat_member.side_effect = Exception("Should not be called")
    
    result_cached = await middleware(handler, event, data)
    if result_cached == "Passed":
         # Check if mock was called
         if bot.get_chat_member.called:
             print("[FAIL] Middleware hit API despite cache.")
         else:
             print("[PASS] Middleware used cache (did not hit API).")
    
if __name__ == "__main__":
    asyncio.run(verify())
