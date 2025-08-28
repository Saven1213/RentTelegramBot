import aiosqlite
from .config import DB_PATH

t = 'debts'

async def add_debts(tg_id, amount, description):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        INSERT INTO {t}
        (tg_id, amount, description)
        VALUES (?, ?)
        """, (tg_id, amount, description))

        await conn.commit()


async def get_debts(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT * 
        FROM {t}
        WHERE tg_id = ?
        """, (tg_id, ))


        data = await cursor.fetchall()

        return data