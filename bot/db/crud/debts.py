import aiosqlite
from .config import DB_PATH

t = 'debts'

async def add_debt(tg_id, amount, description):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        INSERT INTO {t}
        (tg_id, amount, description)
        VALUES (?, ?, ?)
        """, (tg_id, amount, description))

        await conn.commit()


async def get_debts(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT tg_id, amount, description
        FROM {t}
        WHERE tg_id = ?
        """, (tg_id, ))


        data = await cursor.fetchall()

        return data

async def remove_debt(tg_id: int, amount: int, description: str) -> bool:
    """Удаление долга из базы данных"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute(
                "DELETE FROM debts WHERE tg_id = ? AND amount = ? AND description = ?",
                (tg_id, amount, description)
            )
            await conn.commit()
            return True
    except Exception as e:
        print(f"Ошибка при удалении долга: {e}")
        return False