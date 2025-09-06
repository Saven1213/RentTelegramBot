import aiosqlite
from .config import DB_PATH


t = 'delays'

async def get_delays_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT *
        FROM {t}
        WHERE tg_id = ?
        """, (tg_id, ))

        delays = await cursor.fetchone()

        return delays

async def delete_delays(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        DELETE FROM {t}
        WHERE tg_id = ?
        """, (tg_id, ))

        await conn.commit()

