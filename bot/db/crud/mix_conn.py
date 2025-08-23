import aiosqlite
from datetime import datetime, timedelta

DB_PATH = "rent-bike.db"

async def rent_bike(tg_id, bike_id, time):
    """
    Арендует скутер для пользователя.
    Возвращает tuple: (user_tuple, bike_tuple, rented_now)
    """

    async with aiosqlite.connect("rent-bike.db") as conn:
        cursor = await conn.cursor()

        # Получаем пользователя
        await cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        user = await cursor.fetchone()

        # Если пользователь уже арендует — возвращаем с rented_now=False
        if user[3] is not None and user[3] != 'null':
            # Получаем скутер на всякий случай
            await cursor.execute("SELECT * FROM bikes WHERE id = ?", (user[3],))
            bike = await cursor.fetchone()
            return user, bike, False

        # Получаем скутер
        await cursor.execute("SELECT * FROM bikes WHERE id = ?", (bike_id,))
        bike = await cursor.fetchone()

        # Обновляем данные пользователя и скутера
        await cursor.execute(
            "UPDATE users SET bike_id = ?, bike_name = ? WHERE tg_id = ?",
            (bike_id, bike[2], tg_id)
        )
        await cursor.execute(
            "UPDATE bikes SET is_free = 0, user = ? WHERE id = ?",
            (tg_id, bike_id)
        )

        # Добавляем запись о прокате
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(days=time)
        await cursor.execute(
            "INSERT INTO rent_details (user_id, bike_id, start_time, end_time, status) VALUES (?, ?, ?, ?, ?)",
            (tg_id, bike_id, start_time.isoformat(), end_time.isoformat(), "active")
        )

        await conn.commit()
        return user, bike, True


