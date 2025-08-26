import aiosqlite


from .config import DB_PATH, t

async def change_status_order(order_id, new_status):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        UPDATE {t}
        SET status = ?
        WHERE order_id = ?
        """, (new_status, order_id))

        await conn.commit()
        await cursor.close()