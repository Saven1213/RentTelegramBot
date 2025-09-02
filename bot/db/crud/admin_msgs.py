import aiosqlite

async def save_admin_msg(user_id: int, admin_chat_id: int, msg_id: int):
    async with aiosqlite.connect("rent-bike.db") as db:
        await db.execute(
            "INSERT OR IGNORE INTO admin_msgs(user_id, admin_chat_id, msg_id) VALUES (?, ?, ?)",
            (user_id, admin_chat_id, msg_id)
        )
        await db.commit()

async def get_admin_msgs(user_id: int) -> list[tuple[int, int]]:
    async with aiosqlite.connect("rent-bike.db") as db:
        cursor = await db.execute(
            "SELECT admin_chat_id, msg_id FROM admin_msgs WHERE user_id = ?",
            (user_id,)
        )
        rows = await cursor.fetchall()
        return rows

async def clear_admin_msgs(user_id: int):
    async with aiosqlite.connect("rent-bike.db") as db:
        await db.execute(
            "DELETE FROM admin_msgs WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

