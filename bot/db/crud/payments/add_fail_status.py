import aiosqlite
from .config import DB_PATH, t


async def fail_status(order_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()

        await cursor.execute(f"""
        UPDATE {t}
        SET status = 'fail'
        WHERE order_id = ?
        """, (order_id, ))

        await conn.commit()
        await cursor.close()
