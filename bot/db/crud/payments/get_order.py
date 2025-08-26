import aiosqlite
from .config import DB_PATH, t


async def get_order(order_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT *
        FROM {t}
        WHERE order_id = ?
        """, (order_id, ))

        order = await cursor.fetchone()

        return order
