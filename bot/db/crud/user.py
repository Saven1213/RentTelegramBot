import aiosqlite


async def get_user(tg_id):
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
            SELECT * FROM users WHERE tg_id = ?
        """, (tg_id,))
        user = await cursor.fetchone()

        return user if user else None

async def add_user(tg_id, username):
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        INSERT INTO users (tg_id, username, refferals, ban) VALUES (?, ?, ?, ?)
        """, (tg_id, username, 0, False))

        await conn.commit()

        return True

