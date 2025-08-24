import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.db import async_main

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from middlewares.ban_middleware import BanMiddleware

from bot.scheduler import check_rent_status, deactivate_expired_rents, delete_old_history
from config import TOKEN
from inc_routers import router

scheduler = AsyncIOScheduler()
bot = Bot(token=TOKEN)
dp = Dispatcher()

router.message.middleware(BanMiddleware())
router.callback_query.middleware(BanMiddleware())

# async def on_startup(dispatcher: Dispatcher):
#     await init_db()
#     print("✅ DB initialized")


async def main():

    dp.include_router(router)
    await async_main()
    await bot.delete_webhook(drop_pending_updates=True)

    scheduler.add_job(check_rent_status, "interval", hours=1, args=[bot])
    scheduler.add_job(deactivate_expired_rents, "interval",  munutes=30, args=[bot])
    scheduler.add_job(delete_old_history, 'interval', days=30)
    scheduler.start()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()






if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
