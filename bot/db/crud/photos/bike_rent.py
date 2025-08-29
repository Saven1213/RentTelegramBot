import aiosqlite
from aiogram.exceptions import TelegramBadRequest

from ..config import DB_PATH

t = 'photos_rent_bikes'

async def update_bike_photo(bike_id: int, photo_file_id: str):
    """Обновить фото скутера"""

    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        UPDATE {t}
        SET file_id = ?
        WHERE id = ?
        """, (photo_file_id, bike_id))

        await conn.commit()


async def update_bike_description(bike_id: int, description: str) -> bool:
    """Обновить описание скутера"""
    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.cursor()
            await cursor.execute(f"""
            UPDATE {t}
            SET description = ?
            WHERE id = ?
            """, (description, bike_id))

            await conn.commit()

            return True

    except Exception:
        return False


async def get_bike_extra_data(bike_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM photos_rent_bikes WHERE bike_id = ?", (bike_id,))
        return await cursor.fetchone()


async def delete_bike_photo(bike_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        DELETE FROM {t}
        WHERE bike_id = ?
        """, (bike_id, ))

        await conn.commit()

