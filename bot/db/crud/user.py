import aiosqlite

from bot.db.crud.bike import change_status_not_free
from bot.handlers.notifies import write_period

from .config import DB_PATH


t = 'users'
async def get_user(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
            SELECT * FROM {t} WHERE tg_id = ?
        """, (tg_id,))
        user = await cursor.fetchone()

        return user if user else None

async def add_user(tg_id, username):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        INSERT INTO {t} (tg_id, username, refferals, ban, admin) VALUES (?, ?, ?, ?, ?)
        """, (tg_id, username, 0, False, 'user'))

        await conn.commit()

        return True

async def rent_scooter_crud(tg_id, bike_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT bike_type FROM bikes WHERE bike_id = ?
        """, (bike_id, ))

        bike_name = await cursor.fetchone()

        await cursor.execute(f"""
        UPDATE users 
        SET bike_id = ?, bike_name = ? 
        WHERE tg_id = ?
        """, (bike_id, bike_name, tg_id))

        await change_status_not_free(bike_id, tg_id)


        await conn.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        SELECT *
        FROM users
        """)
        users = await cursor.fetchall()

        return users

async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT *
        FROM {t}
        WHERE (admin = 'moderator' OR admin = 'admin')
        """)

        admins = await cursor.fetchall()

        return admins





