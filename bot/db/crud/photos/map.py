import aiosqlite

from bot.db.crud.config import DB_PATH

async def add_photo(file_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()

        await cursor.execute("""
        SELECT *
        FROM photo_map
        """)

        data = await cursor.fetchone()

        if data:

            await cursor.execute("""
            UPDATE photo_map
            SET file_id = ?
            """, (file_id, ))

        else:
            await cursor.execute("""
            INSERT INTO photo_map
            (file_id)
            VALUES (?)
            """, (file_id,))

        await conn.commit()

