import asyncio
import logging
from datetime import timezone

from aiogram import Bot, Dispatcher

from bot.db import async_main

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.db.crud.payments.check_status import check_payments
from middlewares.ban_middleware import BanMiddleware

from bot.scheduler import check_rent_status, deactivate_expired_rents, delete_old_history, check_payments_job
from config import TOKEN
from inc_routers import main_router

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
bot = Bot(token=TOKEN)
dp = Dispatcher()

main_router.message.middleware(BanMiddleware())
main_router.callback_query.middleware(BanMiddleware())

# async def on_startup(dispatcher: Dispatcher):
#     await init_db()
#     print("✅ DB initialized")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await async_main()
    dp.include_router(main_router)



    scheduler.add_job(check_rent_status, "interval", minutes=1, args=[bot])
    scheduler.add_job(deactivate_expired_rents, "interval",  minutes=5, args=[bot])
    scheduler.add_job(delete_old_history, 'interval', days=30)
    scheduler.add_job(check_payments_job, 'interval', seconds=30)
    scheduler.start()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        if scheduler.running:
            scheduler.shutdown()
        await asyncio.sleep(0.1)






if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
