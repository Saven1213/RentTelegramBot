import aiosqlite

from bot.db.crud.bike import change_status_not_free


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


async def change_role(tg_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
        SELECT admin FROM users WHERE tg_id = ?
        """, (tg_id,))

        result = await cursor.fetchone()
        if not result:
            return

        current_role = result[0]

        if current_role == 'user':
            new_role = 'admin'
        elif current_role == 'admin':
            new_role = 'user'
        else:
            return

        await cursor.execute("""
        UPDATE users SET admin = ? WHERE tg_id = ?
        """, (new_role, tg_id))

        await conn.commit()


async def change_ban_status(tg_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
        SELECT ban FROM users WHERE tg_id = ?
        """, (tg_id,))

        result = await cursor.fetchone()
        if not result:
            return

        current_ban_status = result[0]


        new_ban_status = 1 if current_ban_status == 0 else 0

        await cursor.execute("""
        UPDATE users SET ban = ? WHERE tg_id = ?
        """, (new_ban_status, tg_id))

        await conn.commit()

async def set_null_status_bike(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        UPDATE {t}
        SET bike_id = NULL, bike_name = NULL
        WHERE tg_id = ?
        """, (tg_id, ))

        await conn.commit()







