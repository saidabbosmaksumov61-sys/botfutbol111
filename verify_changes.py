import asyncio
from unittest.mock import MagicMock, AsyncMock
import locales
import database
import scheduler

# Mock database
original_get_users_by_team = database.get_users_by_team
original_get_team_name = database.get_team_name
original_is_goal_notified = database.is_goal_notified
original_mark_goal_notified = database.mark_goal_notified

database.get_users_by_team = MagicMock(return_value=[
    {"id": 123, "lang": "en"},
    {"id": 456, "lang": "uz"}
])
database.get_team_name = MagicMock(return_value="Real Madrid")
database.is_goal_notified = MagicMock(return_value=False)
database.mark_goal_notified = MagicMock()

# Mock API
scheduler.api.get_all_matches = MagicMock(return_value=[
    {
        "id": 1001,
        "is_live": True,
        "home": "Real Madrid",
        "away": "Barcelona",
        "home_id": 10,
        "away_id": 20,
        "score": "1 - 0",
        "league": "La Liga"
    }
])
scheduler.api.get_match_events = MagicMock(return_value=["Vinicius Jr (30')"])
scheduler.api.get_matches = MagicMock(return_value=[
    {
        "id": 2002,
        "date": "2024-01-01T12:00:00Z",
        "home": "Real Madrid",
        "away": "Barcelona",
        "status": "Upcoming"
    }
])

async def verify():
    bot = AsyncMock()
    
    print("--- Testing Live Goal Notification ---")
    await scheduler.check_live_notifications(bot)
    
    # Check calls
    print(f"Bot send_message calls: {bot.send_message.call_count}")
    for call in bot.send_message.call_args_list:
        args, _ = call
        user_id, text = args
        print(f"To User {user_id}:\n{text}\n")

    print("\n--- Testing Reminder Notification ---")
    # For reminder verification, we can just check the text formatting since the logic depends on time
    # matches = scheduler.api.get_matches(1, "upcoming")
    # We force the logic by calling get_text directly as if we were in the loop
    team_name = database.get_team_name(10)
    text_en = locales.get_text("en", "reminder_text").format(
        team=team_name,
        home="Real Madrid", 
        away="Barcelona"
    )
    print(f"Reminder Text (EN):\n{text_en}\n")

    text_uz = locales.get_text("uz", "reminder_text").format(
         team=team_name,
        home="Real Madrid", 
        away="Barcelona"
    )
    print(f"Reminder Text (UZ):\n{text_uz}\n")

if __name__ == "__main__":
    asyncio.run(verify())
