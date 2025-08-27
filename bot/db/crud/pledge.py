import aiosqlite

from .config import DB_PATH
t = 'pledges'


async def add_pledge(tg_id, amount, order_id, bike_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        INSERT INTO {t}
        (tg_id, bike_id, amount, order_id, status)
        VALUES (?, ?, ?, ?, ?)
        """, (tg_id, bike_id, amount, order_id, 'active'))

        await conn.commit()
        await cursor.close()