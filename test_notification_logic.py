import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime, timedelta, timezone

# Helper to mock database
import sqlite3
import database
import api
import scheduler

# Redirect DB to test file
TEST_DB = "test_bot_users.db"
database.DB_NAME = TEST_DB
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

database.init_db()

# Add a test user
USER_ID = 12345
database.add_user(USER_ID, "uz")
# Set Favorite Team (Real ID for Real Madrid: 8633, but we use dummy)
TEAM_ID = 999
database.set_favorite(USER_ID, TEAM_ID, "Test Team FC")

# Mock API
mock_api = MagicMock()
scheduler.api = mock_api
# Also mock api.py's internal api used in handlers if needed, but here we test scheduler.
# scheduler.py imports api instance as 'api'. We patched it.

# Mock Bot
mock_bot = AsyncMock()

async def test_scheduler():
    print("--- Testing Reminders ---")
    # 1. Test Reminder (1 hour before)
    now = datetime.now(timezone.utc)
    match_time = now + timedelta(minutes=60)
    
    mock_api.get_matches.return_value = [{
        "id": 101,
        "date": match_time.isoformat().replace("+00:00", "Z"),
        "home": "Test Home",
        "away": "Test Away",
        "league_id": 1,
        "status": "Upcoming"
    }]
    mock_api.get_team_details.return_value = {"id": TEAM_ID, "name": "Real Test FC"}
    # Mock league name for get_league_name check (scheduler calls api.get_leagues)
    mock_api.get_leagues.return_value = [{"id": 1, "name": "Test League"}]

    await scheduler.check_reminders(mock_bot)
    
    # Verify Reminder Sent
    # Check if send_message called
    if mock_bot.send_message.called:
        args = mock_bot.send_message.call_args[0]
        print(f"✅ Reminder sent to {args[0]}: \n{args[1]}")
    else:
        print("❌ Reminder NOT sent!")

    mock_bot.reset_mock()
    
    print("\n--- Testing HT Notification ---")
    # 2. Test HT
    mock_api.get_all_matches.return_value = [{
        "id": 202,
        "home": "Team A",
        "away": "Team B",
        "home_id": TEAM_ID, # User loves this team
        "away_id": 888,
        "score": "1 - 1",
        "status_text": "HT",
        "is_live": True, # Technically HT is live-ish in strict sense of not finished?
        # api.py says is_live = started and not finished. HT is started and not finished.
        "is_finished": False
    }]
    
    await scheduler.check_live_notifications(mock_bot)
    
    if mock_bot.send_message.called:
        args = mock_bot.send_message.call_args[0]
        print(f"✅ HT Notification sent: \n{args[1]}")
    else:
        print("❌ HT Notification NOT sent!")
        
    mock_bot.reset_mock()

    print("\n--- Testing FT Notification ---")
    # 3. Test FT
    mock_api.get_all_matches.return_value = [{
        "id": 202,
        "home": "Team A",
        "away": "Team B",
        "home_id": TEAM_ID,
        "away_id": 888,
        "score": "2 - 1",
        "status_text": "Finished",
        "is_live": False,
        "is_finished": True
    }]
    
    # We need to simulate that HT was already notified so it doesn't block? 
    # No, they are separate events.
    
    await scheduler.check_live_notifications(mock_bot)
    
    if mock_bot.send_message.called:
        args = mock_bot.send_message.call_args[0]
        print(f"✅ FT Notification sent: \n{args[1]}")
    else:
        print("❌ FT Notification NOT sent!")

    # Cleanup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

if __name__ == "__main__":
    asyncio.run(test_scheduler())
