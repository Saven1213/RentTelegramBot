from datetime import datetime, timedelta

import aiosqlite



from .config import DB_PATH
t = 'rent_details'

async def add_rent_data(tg_id: int, bike_id: int, days: int):
    async with aiosqlite.connect("rent-bike.db") as conn:
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=days)

        await conn.execute(
            f"""
            INSERT INTO {t} (user_id, bike_id, start_time, end_time, status, notified)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tg_id, bike_id, start_time.isoformat(), end_time.isoformat(), "active", 0),
        )
        await conn.commit()

async def get_data_rents(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT *
        FROM {t}
        WHERE user_id = ?
        """, (tg_id, ))

        data = await cursor.fetchall()

        return data

async def get_current_rent(id_):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT *
        FROM {t}
        WHERE id = ?
        """, (id_, ))

        data = await cursor.fetchone()

        return data