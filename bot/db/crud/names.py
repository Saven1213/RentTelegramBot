import aiosqlite

from .config import DB_PATH
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

async def add_personal_data(tg_id, first_name, last_name, number):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        INSERT INTO {t}
        (tg_id, first_name, last_name, number)
        VALUES (?, ?, ?, ?)
        """, (tg_id, first_name, last_name, number))

        await conn.commit()
        await cursor.close()

async def get_all_users_have_pd():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT *
        FROM {t}
        """)

        users = await cursor.fetchall()

        return users