

from .config import DB_PATH

from datetime import datetime, timedelta
import aiosqlite


async def rent_bike(tg_id: int, bike_id: int, days: int, pledge: float | int = 0):
    """
    Арендует скутер для пользователя.
    - tg_id: Telegram ID пользователя
    - bike_id: ID скутера
    - days: срок аренды (целое число)
    - pledge: залог (может быть 0, если не нужен)

    Возвращает tuple: (user_tuple, bike_tuple, rented_now: bool)
    """
    async with aiosqlite.connect("rent-bike.db") as conn:
        cursor = await conn.cursor()


        await cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        user = await cursor.fetchone()


        if user and user[3] is not None and user[3] != 'null':
            await cursor.execute("SELECT * FROM bikes WHERE id = ?", (user[3],))
            bike = await cursor.fetchone()
            return user, bike, False


        await cursor.execute("SELECT * FROM bikes WHERE id = ?", (bike_id,))
        bike = await cursor.fetchone()


        await cursor.execute(
            "UPDATE users SET bike_id = ?, bike_name = ? WHERE tg_id = ?",
            (bike_id, bike[2], tg_id)
        )
        await cursor.execute(
            "UPDATE bikes SET is_free = 0, user = ? WHERE id = ?",
            (tg_id, bike_id)
        )


        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=int(days))

        await cursor.execute(
            """
            INSERT INTO rent_details (user_id, bike_id, start_time, end_time, days, pledge, status, notified, pay_later)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tg_id,
                bike_id,
                start_time.isoformat(),
                end_time.isoformat(),
                int(days),
                pledge,
                "active",
                False,
                0
            )
        )

        await conn.commit()
        return user, bike, True


async def get_user_and_data(tg_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        user = await cursor.fetchone()

        await cursor.execute("SELECT * FROM names WHERE tg_id = ?", (tg_id,))
        personal_data = await cursor.fetchone()

        return user, personal_data




