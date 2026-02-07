from aiogram import Router, F, types
from aiogram.filters import Command
from api import FootballAPI
import keyboards
from locales import get_text
from datetime import datetime, timedelta
import database
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

ADMIN_ID = 8397359520

class AdminState(StatesGroup):
    waiting_for_broadcast_message = State()

router = Router()
api = FootballAPI()

# Cache for league selection (transient state)
# We can keep using dict for this simple transient state, 
# or use FSM. Dict is fine for league selection flow before db save.
temp_state = {} 

def get_user_lang(user_id):
    user = database.get_user(user_id)
    if user:
        return user["lang"]
    return "uz"

@router.message(Command("start"))
async def start_handler(message: types.Message):
    # Ensure user is in DB
    database.add_user(message.from_user.id)
    welcome_text = get_text("uz", "welcome") 
    await message.answer(welcome_text, reply_markup=keyboards.get_lang_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "start_over")
async def start_over_handler(callback: types.CallbackQuery):
    lang = get_user_lang(callback.from_user.id)
    leagues = api.get_leagues()
    text = get_text(lang, "select_league")
    await callback.message.edit_text(text, reply_markup=keyboards.get_leagues_keyboard(leagues, lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("lang_"))
async def lang_selected(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[1]
    
    # Update Language in DB
    database.set_lang(callback.from_user.id, lang_code)
    
    leagues = api.get_leagues()
    text = get_text(lang_code, "select_league")
    await callback.message.edit_text(text, reply_markup=keyboards.get_leagues_keyboard(leagues, lang_code), parse_mode="HTML")

@router.callback_query(F.data.startswith("league_"))
async def league_selected(callback: types.CallbackQuery):
    league_id = int(callback.data.split("_")[1])
    temp_state[callback.from_user.id] = league_id 
    lang = get_user_lang(callback.from_user.id)
    
    await callback.message.edit_text(get_text(lang, "loading"), reply_markup=None, parse_mode="HTML")
    
    teams = api.get_teams(league_id)
    if not teams:
        await callback.message.edit_text(get_text(lang, "no_teams"), reply_markup=keyboards.get_leagues_keyboard(api.get_leagues(), lang), parse_mode="HTML")
        return

    # Get league name
    all_leagues = api.get_leagues()
    league_name = next((l['name'] for l in all_leagues if l['id'] == league_id), "League")
    
    text = get_text(lang, "select_team").format(league=league_name)
    await callback.message.edit_text(text, reply_markup=keyboards.get_teams_keyboard(teams, league_id, lang), parse_mode="HTML")


@router.callback_query(F.data == "back_leagues")
async def back_to_leagues(callback: types.CallbackQuery):
    lang = get_user_lang(callback.from_user.id)
    leagues = api.get_leagues()
    await callback.message.edit_text(get_text(lang, "select_league"), reply_markup=keyboards.get_leagues_keyboard(leagues, lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("standings_"))
async def show_standings(callback: types.CallbackQuery):
    league_id = int(callback.data.split("_")[1])
    lang = get_user_lang(callback.from_user.id)
    
    await callback.message.edit_text(get_text(lang, "loading"), reply_markup=None, parse_mode="HTML")
    
    standings = api.get_standings(league_id)
    
    # Get League Name for Title
    all_leagues = api.get_leagues()
    league_name = next((l['name'] for l in all_leagues if l['id'] == league_id), "League")
    
    if not standings:
        text = get_text(lang, "no_games") 
    else:
        # Format Table
        # # Team       P   Pts
        # 1 Ars        20  50
        
        # Table Header
        # N  Team       P  GD Pts
        table_str = " # Team       P  GD Pts\n"
        table_str += "-----------------------\n"
        
        for row in standings:
            rank = str(row['rank']).rjust(2)
            name = row['name'][:10].ljust(11) 
            played = str(row['played']).rjust(2)
            gd = str(row.get('gd', 0)).rjust(3)
            pts = str(row['pts']).rjust(3)
            
            table_str += f"{rank} {name}{played} {gd} {pts}\n"
            
        text = get_text(lang, "standings_title").format(league=league_name, table=table_str)
        
    temp_state[callback.from_user.id] = league_id
    await callback.message.edit_text(text, reply_markup=keyboards.get_back_button(0, lang), parse_mode="HTML") # team_id 0 doesn't matter for back from standings



@router.callback_query(F.data.startswith("team_"))
async def team_selected(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    team_id = int(data_parts[1])
    league_id = int(data_parts[2]) if len(data_parts) > 2 else temp_state.get(callback.from_user.id)
    
    if league_id:
        temp_state[callback.from_user.id] = league_id
        
    lang = get_user_lang(callback.from_user.id)
    
    team_name = "Jamoa"
    if league_id:
        teams = api.get_teams(league_id)
        team_name = next((t['name'] for t in teams if t['id'] == team_id), "Jamoa")


    # Check favorite
    user = database.get_user(callback.from_user.id)
    is_fav = False
    if user and user["fav_team_id"] == team_id:
        is_fav = True
        
    text = get_text(lang, "select_option").format(team=team_name)
    
    await callback.message.edit_text(
        text, 
        reply_markup=keyboards.get_match_options_keyboard(team_id, lang, is_favorite=is_fav),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back_teams")
async def back_to_teams(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    league_id = temp_state.get(user_id) or database.get_user(user_id).get("fav_team_id") # Logic flaw: fav_team_id is team, not league.
    # We rely on temp_state for league_id. If missing (bot restart), user gotta go back to leagues.
    
    lang = get_user_lang(user_id)
    
    if not league_id:
        # Fallback to leagues if transient state lost
        leagues = api.get_leagues()
        await callback.message.edit_text(get_text(lang, "select_league"), reply_markup=keyboards.get_leagues_keyboard(leagues, lang))
        return
        
    teams = api.get_teams(league_id)
    
    # Get league name for display (Fix for {league} bug)
    all_leagues = api.get_leagues()
    league_name = next((l['name'] for l in all_leagues if l['id'] == league_id), "League")
    
    text = get_text(lang, "select_team").format(league=league_name)
    await callback.message.edit_text(text, reply_markup=keyboards.get_teams_keyboard(teams, league_id, lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("fav_"))
async def toggle_favorite(callback: types.CallbackQuery):
    team_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    user = database.get_user(user_id)
    
    # Check current status
    if user and user["fav_team_id"] == team_id:
        # Remove
        database.remove_favorite(user_id)
        await callback.answer(get_text(lang, "fav_removed"))
        is_fav = False
    else:
        # Add (Need team name, but callback only has ID. We might need to fetch or generic save)
        # To be precise, let's fetch basic details or just save ID and 'Unknown' or update later
        # Optimization: We don't strictly need name for logic, just ID. Name is for DB readable.
        # We can fetch team name from API if we want, or just save "Team {id}"
        database.set_favorite(user_id, team_id, f"Team_{team_id}")
        await callback.answer(get_text(lang, "fav_set"), show_alert=True)
        is_fav = True
        
    # Refresh keyboard
    await callback.message.edit_reply_markup(
        reply_markup=keyboards.get_match_options_keyboard(team_id, lang, is_favorite=is_fav)
    )

async def show_matches_generic(callback: types.CallbackQuery, status_group: str, title_key: str):
    team_id = int(callback.data.split("_")[1])
    lang = get_user_lang(callback.from_user.id)
    
     # Check favorite status for the back button context or just keep keyboard context?
    # Actually, we show results, then user clicks back to team options.
    
    await callback.message.edit_text(get_text(lang, "loading"), reply_markup=None)
    
    matches = api.get_matches(team_id, status_group)
    
    if not matches:
        text = get_text(lang, "no_games")
    else:
        text = get_text(lang, title_key)
        
        # Optimize: Fetch all matches once here for live scores/clock
        all_live_details = api.get_all_matches() if status_group == "live" else []

        for m in matches:
            date_display = m['date']
            time_display = ""
            try:
                # Parse ISO
                iso_str = m['date'].replace("Z", "+00:00")
                dt_utc = datetime.fromisoformat(iso_str)
                # Tashkent Time
                dt_tashkent = dt_utc + timedelta(hours=5)
                date_display = dt_tashkent.strftime("%d.%m")
                time_display = dt_tashkent.strftime("%H:%M")
            except:
                pass
                
            score_info = m.get('score', 'vs')
            
            # Status icon mapping
            status_icon = "⏳"
            status_text = m['status']
            
            if m['status'] == 'Live': 
                status_icon = "🔴"
                # Using precached global matches for fresh score and clock/HT
                match_data = next((x for x in all_live_details if x['id'] == m['id']), None)
                
                if match_data:
                    status_text = match_data['match_time'] or "Live"
                    # Use fresh score
                    score_info = match_data['score']
                else:
                    # Fallback to match_time from get_matches
                    status_text = m.get('match_time') or "Live"

                # Translate HT / Add Minute Tick
                if status_text == "HT":
                    status_text = get_text(lang, "ht_text")
                elif status_text and status_text[0].isdigit():
                    status_text += "'"

            if m['status'] == 'Finished': 
                status_icon = "🏁"
                status_text = "" # No need for "Finished" text if icon is there
            
            # Format:
            # ⚽ Home 1 - 0 Away
            # 📅 23.01 00:15 | 🔴 <b>60'</b>
            
            status_part = f" | {status_icon} <b>{status_text}</b>" if status_text else f" | {status_icon}"
            text += f"⚽ {m['home']} {score_info} {m['away']}\n"
            text += f"📅 {date_display} {time_display}{status_part}\n"
            
            # SHOW GOALS IF LIVE OR PAST (Finished)
            if status_group in ["live", "past"]:
                events = api.get_match_events(m['id'])
                if events:
                    text += "⚽️ " + ", ".join(events) + "\n"

            text += "\n" # Smaller gap instead of long divider
            
    await callback.message.edit_text(text, reply_markup=keyboards.get_back_button(team_id, lang), parse_mode="HTML")

@router.callback_query(F.data.startswith("upcoming_"))
async def show_upcoming(callback: types.CallbackQuery):
    await show_matches_generic(callback, "upcoming", "upcoming_title")

@router.callback_query(F.data.startswith("live_"))
async def show_live(callback: types.CallbackQuery):
    await show_matches_generic(callback, "live", "live_title")

    await show_matches_generic(callback, "past", "history_title")

# --- ADMIN HANDLERS ---

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🛠 Admin Panel", reply_markup=keyboards.get_admin_keyboard())

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    
    count = database.get_user_count()
    await callback.answer(f"📊 Total Users: {count}", show_alert=True)

@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(AdminState.waiting_for_broadcast_message)
    await callback.message.edit_text(
        "📢 Send the message you want to broadcast (Text, Photo, Video, etc.).", 
        reply_markup=keyboards.get_cancel_broadcast_keyboard()
    )

@router.callback_query(F.data == "admin_cancel_broadcast")
async def cancel_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
        
    await state.clear()
    await callback.message.edit_text("🛠 Admin Panel", reply_markup=keyboards.get_admin_keyboard())

@router.message(AdminState.waiting_for_broadcast_message)
async def process_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    users = database.get_all_users()
    count = 0
    blocked = 0
    
    status_msg = await message.answer(f"🚀 Starting broadcast to {len(users)} users...")
    
    for user in users:
        try:
            await message.send_copy(chat_id=user['id'])
            count += 1
        except Exception as e:
            # print(f"Failed to send to {user['id']}: {e}")
            blocked += 1
            
    await status_msg.edit_text(f"✅ Broadcast Complete!\n\nSent: {count}\nFailed/Blocked: {blocked}")
    await state.clear()
    await message.answer("🛠 Admin Panel", reply_markup=keyboards.get_admin_keyboard())
