import aiosqlite
DB_PATH = 'rent-bike.db'
t = 'equips'


async def save_equips(tg_id, helmet, chain, box, trunk):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        INSERT INTO {t}
        (tg_id, helmet, chain, box, trunk)
        VALUES (?, ?, ?, ?, ?)
        """, (tg_id, helmet,chain, box, trunk))

        await conn.commit()
