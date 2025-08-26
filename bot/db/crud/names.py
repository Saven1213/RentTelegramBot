import aiosqlite

DB_PATH = 'rent-bike.db'
t = 'names'


async def get_personal_data(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT *
        FROM {t}
        WHERE tg_id = ?
        """, (tg_id, ))

        data = await cursor.fetchone()

        return data