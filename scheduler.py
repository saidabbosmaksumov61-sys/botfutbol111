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
            # await check_live_notifications(bot)
            
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
    Check live matches for goals and notify ONLY users who favorited the playing teams.
    """
    all_matches = api.get_all_matches()
    live_matches = [m for m in all_matches if m['is_live']]
    
    if not live_matches:
        return

    for m in live_matches:
        match_id = m['id']
        score_str = m['score'] # e.g. "1 - 0"
        
        if score_str == "0 - 0" or score_str == "v" or not score_str:
            continue
            
        if not database.is_goal_notified(match_id, score_str):
            # Goal detected!
            print(f"Goal in match {match_id}: {m['home']} {score_str} {m['away']}")
            
            # Fetch events to get player name and minute
            events = api.get_match_events(match_id)
            last_event = events[-1] if events else "Goal!"
            
            # Target Users: Fans of Home OR Fans of Away
            home_fans = database.get_users_by_team(m['home_id'])
            away_fans = database.get_users_by_team(m['away_id'])
            
            # Combine unique users
            target_users = {u['id']: u for u in home_fans + away_fans}.values()
            
            if not target_users:
                # Mark as notified even if no one is watching to avoid re-processing
                database.mark_goal_notified(match_id, score_str)
                continue

            for user in target_users:
                user_id = user['id']
                lang = user['lang']
                
                # Format: GOAL !!! \n {home} {score} {away} \n {scorer} {minute}' \n\n [by : @noventis_bots]
                text = get_text(lang, "goal_text").format(
                    home=m['home'],
                    score=score_str,
                    away=m['away'],
                    event=last_event
                )
                
                try:
                    await bot.send_message(user_id, text, reply_markup=keyboards.get_notification_keyboard())
                except Exception as ex:
                    pass
            
            # Mark as notified
            database.mark_goal_notified(match_id, score_str)

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

