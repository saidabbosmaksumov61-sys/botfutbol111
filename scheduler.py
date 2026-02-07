import asyncio
from datetime import datetime, timedelta, timezone
import database
from api import FootballAPI
from locales import get_text
import keyboards
from aiogram import Bot

api = FootballAPI()

# Cache sent notifications to avoid duplicates: { "team_id_match_date": timestamp }
# Ideally use DB for this too, but memory is okay for simple reboot persistence loss
sent_notifications = set()

async def start_scheduler(bot: Bot):
    print("Scheduler started...")
    # Last time we checked reminders (hourly)
    last_reminder_check = 0
    
    while True:
        try:
            now_ts = datetime.now().timestamp()
            
            # 1. Check Live Scores (Every 10 seconds)
            await check_live_notifications(bot)
            
            # 2. Check Match Reminders (Every 5 minutes is enough for "1 hour before" logic)
            if now_ts - last_reminder_check > 300:
                await check_reminders(bot)
                last_reminder_check = now_ts
                
            await asyncio.sleep(10) 
        except Exception as e:
            print(f"Scheduler Loop Error: {e}")
            await asyncio.sleep(10)

async def check_live_notifications(bot: Bot):
    """
    Check matches for events (Start, Goal, HT, 2nd Half, FT) and notify fans.
    """
    # Get all team IDs that users have favorited
    interested_teams = database.get_all_favorite_teams()
    if not interested_teams:
        return

    # Pass interested teams to API to ensure we get their matches
    all_matches = api.get_all_matches(interested_team_ids=interested_teams)
    
    # We care about matches that are Live or recently Finished (to catch FT event)
    # Actually, we need to inspect all of them to catch 'Started' even if they just started.
    
    for m in all_matches:
        match_id = m['id']
        home_name = m['home']
        away_name = m['away']
        score_str = m['score']
        status_text = m['status_text'] # e.g. "HT", "FT", "60'"
        is_live = m['is_live']
        is_finished = m['is_finished']
        match_time = m['match_time']

        # Determine events to trigger
        events_to_notify = []

        # 1. Game Started
        if is_live and not database.is_goal_notified(match_id, "start"):
            events_to_notify.append(("start", "game_start_text"))
        
        # 2. Goals (Existing logic)
        # Only check goals if game is live or just finished
        if (is_live or is_finished) and score_str and score_str != "0 - 0" and score_str != "v":
             if not database.is_goal_notified(match_id, score_str):
                 # Store full event for processing
                 events_to_notify.append(("goal", "goal_text"))

        # 3. Half Time
        if status_text == "HT" and not database.is_goal_notified(match_id, "ht"):
            events_to_notify.append(("ht", "ht_notify_text"))

        # 4. Second Half Started
        # Condition: Live, Time > 45, NOT HT, and HT was already notified (or imply it passed)
        # Simple check: If time is like 46, 47... and we haven't notified 2nd_half
        # But time format is string. safe check: if match is live, not HT, and we have recorded 'ht' event?
        # Or just checking if minute > 45 is enough?
        try:
            minute = int(match_time) if match_time and match_time.isdigit() else 0
            if is_live and minute > 45 and status_text != "HT" and not database.is_goal_notified(match_id, "2nd_half"):
                 events_to_notify.append(("2nd_half", "2nd_half_text"))
        except:
            pass

        # 5. Game Finished
        if is_finished and not database.is_goal_notified(match_id, "ft"):
            events_to_notify.append(("ft", "ft_text"))

        if not events_to_notify:
            continue

        # Prepare users to notify
        home_fans = database.get_users_by_team(m['home_id'])
        away_fans = database.get_users_by_team(m['away_id'])
        target_users = {u['id']: u for u in home_fans + away_fans}.values()

        if not target_users:
            # Mark all pending events as notified to avoid re-checking loop
            for event_type, _ in events_to_notify:
                key = score_str if event_type == "goal" else event_type
                database.mark_goal_notified(match_id, key)
            continue

        for event_type, lang_key in events_to_notify:
            # For goal: key is score_str. For others: key is event_type literal.
            db_key = score_str if event_type == "goal" else event_type
            
            # Double check inside loop (though list unique)
            if database.is_goal_notified(match_id, db_key):
                continue
                
            # Extra data for message
            extra = ""
            if event_type == "goal":
                 match_events = api.get_match_events(match_id)
                 extra = match_events[-1] if match_events else "Goal!"

            print(f"Notifying {event_type} for Match {match_id}")

            for user in target_users:
                lang = user['lang']
                
                # Construct Message
                # We need keys in locales.py: game_start_text, ht_text_notify, 2nd_half_text, ft_text
                # Note: 'ht_text' might already exist for display in handlers. assume we need new ones or reuse.
                # Construct text based on event
                
                msg = ""
                if event_type == "goal":
                     msg = get_text(lang, "goal_text").format(home=home_name, away=away_name, score=score_str, event=extra)
                else:
                     # Generic format for status updates
                     # We can use a generic template or specific simple texts
                     # Let's assume we add these keys to locales.py
                     t_key = lang_key
                     base_msg = get_text(lang, t_key)
                     # Most messages need home/away teams
                     msg = f"{base_msg}\n\n⚽ {home_name} {score_str} {away_name}"
                
                try:
                    await bot.send_message(user['id'], msg, reply_markup=keyboards.get_notification_keyboard())
                except Exception as ex:
                    pass
            
            # Mark as done
            database.mark_goal_notified(match_id, db_key)

async def check_reminders(bot: Bot):
    """
    Existing logic for 1-hour reminders.
    """
    team_ids = database.get_all_favorite_teams()
    if not team_ids:
        return
        
    for team_id in team_ids:
        matches = api.get_matches(team_id, "upcoming")
        if not matches:
            continue
            
        for m in matches:
            try:
                iso_str = m['date'].replace("Z", "+00:00")
                match_time = datetime.fromisoformat(iso_str)
                now = datetime.now(timezone.utc)
                
                diff = match_time - now
                minutes_diff = diff.total_seconds() / 60
                
                if 50 <= minutes_diff <= 65:
                    match_id_unique = f"rem_{team_id}_{m['date']}"
                    
                    if match_id_unique in sent_notifications:
                        continue
                        
                    team_name = database.get_team_name(team_id)
                    users = database.get_users_by_team(team_id)
                    for user in users:
                        lang = user['lang']
                        text = get_text(lang, "reminder_text").format(
                            team=team_name,
                            home=m['home'], 
                            away=m['away']
                        )
                        try:
                            await bot.send_message(user['id'], text, reply_markup=keyboards.get_notification_keyboard())
                        except Exception as ex:
                            print(f"Failed to send reminder to {user['id']}: {ex}")
                            
                    sent_notifications.add(match_id_unique)
            except Exception as e:
                print(f"Reminder check error: {e}")

