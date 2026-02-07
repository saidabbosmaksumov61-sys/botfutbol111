from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from locales import get_text


def get_attribution_button():
    return InlineKeyboardButton(text="by : @noventis_bots", url="https://t.me/noventis_bots")

def get_notification_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(get_attribution_button())
    return builder.as_markup()

def get_lang_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbekcha", callback_data="lang_uz")
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.adjust(1)
    builder.row(get_attribution_button())
    return builder.as_markup()

def get_leagues_keyboard(leagues, lang="uz"):
    builder = InlineKeyboardBuilder()
    for league in leagues:
        # Add a trophy icon for each league
        builder.button(text=f"🏆 {league['name']}", callback_data=f"league_{league['id']}")
    builder.adjust(2)
    # builder.row(InlineKeyboardButton(text=get_text(lang, "home"), callback_data="start_over")) -> Removed home button from home page
    builder.row(get_attribution_button())
    return builder.as_markup()

def get_teams_keyboard(teams, league_id, lang="uz"):
    builder = InlineKeyboardBuilder()
    
    # Standings Button at the top
    builder.button(text=get_text(lang, "standings_btn"), callback_data=f"standings_{league_id}")
    builder.adjust(1)
    
    # Teams in 2 columns
    team_builder = InlineKeyboardBuilder()
    for team in teams:
        team_builder.button(text=f"🛡️ {team['name']}", callback_data=f"team_{team['id']}_{league_id}")
    team_builder.adjust(2)
    
    builder.attach(team_builder)
    
    # Navigation at the bottom
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "back_leagues"), callback_data="back_leagues"),
        InlineKeyboardButton(text=get_text(lang, "home"), callback_data="start_over")
    )
    builder.row(get_attribution_button())
    return builder.as_markup()

def get_match_options_keyboard(team_id, lang="uz", is_favorite=False):
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text(lang, "upcoming_btn"), callback_data=f"upcoming_{team_id}")
    builder.button(text=get_text(lang, "live_btn"), callback_data=f"live_{team_id}")
    builder.button(text=get_text(lang, "history_btn"), callback_data=f"history_{team_id}")
    builder.adjust(1)
    
    fav_text = get_text(lang, "remove_fav") if is_favorite else get_text(lang, "add_fav")
    builder.row(InlineKeyboardButton(text=fav_text, callback_data=f"fav_{team_id}"))
    
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "back_teams"), callback_data="back_teams"),
        InlineKeyboardButton(text=get_text(lang, "home"), callback_data="start_over")
    )
    builder.row(get_attribution_button())
    return builder.as_markup()

def get_back_button(team_id, lang="uz"):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=get_text(lang, "back"), callback_data=f"team_{team_id}"),
        InlineKeyboardButton(text=get_text(lang, "home"), callback_data="start_over")
    )
    builder.row(get_attribution_button())
    return builder.as_markup()

def get_admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Stats", callback_data="admin_stats")
    builder.button(text="📢 Broadcast", callback_data="admin_broadcast")
    builder.adjust(2)
    return builder.as_markup()

def get_cancel_broadcast_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancel", callback_data="admin_cancel_broadcast")
    return builder.as_markup()
