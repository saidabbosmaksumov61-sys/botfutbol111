import asyncio
import logging
import sys
import os
from aiohttp import web

# Add project directory to path to fix ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiogram import Bot, Dispatcher
import config
import handlers
from middlewares import SubscriptionMiddleware
import database
import scheduler

async def health_check(request):
    return web.Response(text="Bot is running OK")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

async def main():
    if not config.BOT_TOKEN:
        print("ERROR: BOT_TOKEN is not set in .env file via config.py")
        return

    # Initialize DB
    database.init_db()

    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    
    # Register Middleware
    # dp.message.middleware(SubscriptionMiddleware())
    # dp.callback_query.middleware(SubscriptionMiddleware())
    
    dp.include_router(handlers.router)
    
    print("Bot ishga tushdi (DB + Scheduler + WebServer)...")
    
    # Start Scheduler in background
    asyncio.create_task(scheduler.start_scheduler(bot))
    
    # Start Dummy Web Server (For Render Port Binding)
    asyncio.create_task(start_web_server())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
