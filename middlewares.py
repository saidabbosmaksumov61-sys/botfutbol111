from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Callable, Dict, Any, Awaitable, Union
import config
from locales import get_text
import database
import time

# Simple TTL Cache for Subscription Status
# Format: {user_id: (is_subscribed, timestamp)}
subscription_cache = {}
CACHE_DURATION = 120 # 2 minutes

class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        bot = data['bot']
        user = event.from_user
        
        # Bypass check for admins or if channel is not set
        if not config.REQUIRED_CHANNEL:
            return await handler(event, data)

        # 1. Allow /start command to pass without check (so user can see language selection)
        if isinstance(event, Message) and event.text == "/start":
            return await handler(event, data)
            
        # 2. Allow Language Selection buttons to pass
        if isinstance(event, CallbackQuery) and event.data and event.data.startswith("lang_"):
            return await handler(event, data)

        # 3. Check Cache
        current_time = time.time()
        cached = subscription_cache.get(user.id)
        if cached:
            is_sub, timestamp = cached
            if current_time - timestamp < CACHE_DURATION:
                if is_sub:
                    return await handler(event, data)
                # If cached as not subbed, we might want to recheck sooner? 
                # Or just let them try and hit API again if cache is old?
                # Let's trust cache for 2 mins even if false, unless we want instant retry.
                # Actually, if they subbed, they want instant access. 
                # So maybe only cache POSITIVE result?
                # If we cache negative, they have to wait 2 mins. BAD.
                # So ONLY CACHE TRUE.
                pass 

        try:
            member = await bot.get_chat_member(chat_id=config.REQUIRED_CHANNEL, user_id=user.id)
            if member.status in ["left", "kicked"]:
                # Not subscribed
                
                # Get language for warning
                user_db = database.get_user(user.id)
                lang = user_db['lang'] if user_db else 'uz'
                
                warning_text = get_text(lang, "sub_warning")
                btn_text = get_text(lang, "sub_btn")
                
                sub_markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=btn_text, url=config.CHANNEL_URL)]
                ])
                
                if isinstance(event, Message):
                    await event.answer(warning_text, reply_markup=sub_markup, disable_web_page_preview=True)
                elif isinstance(event, CallbackQuery):
                    await event.answer(warning_text, show_alert=True)
                    # Also send message with link so they can click it
                    await event.message.answer(warning_text, reply_markup=sub_markup)
                return # Stop processing
            else:
                # Subscribed - Cache it!
                subscription_cache[user.id] = (True, current_time)
                
        except Exception as e:
            # FAIL OPEN: If bot cannot check (API error, rate limit, not admin), let user pass.
            print(f"CRITICAL: Subscription check failed. Allowing access. Error: {e}")
            # We can also cache this "allow" state briefly to avoid spamming logs?
            # Let's just allow.
            pass

        return await handler(event, data)
