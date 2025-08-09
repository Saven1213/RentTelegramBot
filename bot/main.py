from datetime import datetime

from aiogram.types import Message
from aiogram import Bot, Dispatcher
import asyncio

import logging
from datetime import datetime, timedelta

from bot.db.models import async_main
from config import TOKEN


from inc_routers import router

bot = Bot(token=TOKEN)
# from db import async_main


async def main():

    await bot.delete_webhook(drop_pending_updates=True)
    await async_main()
    dp = Dispatcher()
    dp.include_router(router)



    # await async_main()

    try:

        await asyncio.gather(
            dp.start_polling(bot)
        )
    except:
        print('БОТ выключен!')
        await dp.stop_polling()
        await bot.session.close()





if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())