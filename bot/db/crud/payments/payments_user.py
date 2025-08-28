import aiosqlite
from .config import DB_PATH


async def get_user_payments(user_id: int):
    """Получить все платежи пользователя"""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,))
        return await cursor.fetchall()

async def get_payment_by_id(payment_id: int):
    """Получить платеж по ID"""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        SELECT * FROM payments WHERE id = ?
        """, (payment_id,))
        return await cursor.fetchone()