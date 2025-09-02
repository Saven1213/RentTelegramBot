import aiosqlite
from .config import DB_PATH
t = 'equips'


async def save_equips(tg_id, helmet, chain, box, trunk, rubber, holder, charger):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        INSERT INTO {t}
        (tg_id, helmet, chain, box, trunk, rubber, holder, charger)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (tg_id, helmet,chain, box, trunk, rubber, holder, charger))

        await conn.commit()

async def get_equips_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT *
        FROM {t}
        WHERE tg_id = ?
        """, (tg_id, ))

        data = await cursor.fetchone()

        return data


