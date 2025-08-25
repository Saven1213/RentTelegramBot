import aiosqlite
from datetime import datetime

DB_PATH = 'rent-bike.db'


async def create_payment(tg_id, order_id, id_, price, time, message_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            INSERT INTO payments 
            (user_id, order_id, bill_id, amount, currency, status, created_at, description, days, message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            tg_id,
            order_id,
            id_,
            price,
            'RUB',
            'pending',
            datetime.now(),
            f"Продление аренды на {time} дней",
            time,
            message_id
        ))
        await conn.commit()