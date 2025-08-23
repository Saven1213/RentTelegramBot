from aiogram import Bot

from datetime import datetime, timedelta
import aiosqlite
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiosqlite import connect

DB_PATH = "rent-bike.db"  # путь к базе


async def check_rent_status(bot: Bot):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🔄 Продлить аренду', callback_data='extend'),
            InlineKeyboardButton(text='⏳ Оплачу позже', callback_data='pay_later')
        ],
        [
            InlineKeyboardButton(text='❌ Не продлевать', callback_data='cancel')
        ],
        [
            InlineKeyboardButton(text="📞 Поддержка", url="t.me/hulkbike_support")
        ]
    ])

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT user_id, end_time, notified FROM rent_details WHERE status = 'active'"
            )
            rows = await cursor.fetchall()

        now_utc = datetime.utcnow()
        now_msk = now_utc + timedelta(hours=3)

        for user_id, end_time_str, notified in rows:
            if end_time_str:
                end_time_utc = datetime.fromisoformat(end_time_str)
                end_time_msk = end_time_utc + timedelta(hours=3)

                time_left = end_time_msk - now_msk

                # Проверяем, что до конца аренды осталось от 23 до 24 часов
                # И что уведомление еще не отправлялось
                if timedelta(hours=23) <= time_left <= timedelta(hours=24) and notified == 0:
                    hours_left = int(time_left.total_seconds() // 3600)
                    minutes_left = int((time_left.total_seconds() % 3600) // 60)

                    await bot.send_message(
                        user_id,
                        f"⏰ <b>АРЕНДА ЗАКАНЧИВАЕТСЯ ЧЕРЕЗ ДЕНЬ!</b>\n\n"
                        f"📅 <b>Окончание:</b> {end_time_msk.strftime('%d.%m.%Y %H:%M')} МСК\n"
                        f"⏳ <b>Осталось:</b> {hours_left}ч {minutes_left}м\n\n"
                        f"💡 <i>Хотите продлить аренду?</i>",
                        parse_mode='HTML',
                        reply_markup=keyboard
                    )

                    # Помечаем, что уведомление отправлено
                    async with aiosqlite.connect(DB_PATH) as conn:
                        await conn.execute(
                            "UPDATE rent_details SET notified = 1 WHERE user_id = ? AND end_time = ?",
                            (user_id, end_time_str)
                        )
                        await conn.commit()

                    print(f"Уведомление отправлено пользователю {user_id}")

    except Exception as e:
        print(f"Ошибка в check_rent_status: {e}")


async def deactivate_expired_rents(bot: Bot):
    try:
        now_ = datetime.utcnow()

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT user_id, end_time FROM rent_details WHERE status = 'active'"
            )
            rows = await cursor.fetchall()

            for user_id, end_time_str in rows:
                if end_time_str:
                    end_time = datetime.fromisoformat(end_time_str)

                    if end_time <= now_:
                        # Получаем данные пользователя и скутера ДО обновления
                        cursor_user = await db.execute(
                            "SELECT username, bike_id, bike_name FROM users WHERE tg_id = ?",
                            (user_id,)
                        )
                        user_result = await cursor_user.fetchone()
                        username = user_result[0] if user_result else f"user_{user_id}"
                        bike_id = user_result[1] if user_result else None
                        bike_name = user_result[2] if user_result else None

                        bike_info = f"{bike_name} #{bike_id}" if bike_id and bike_name else "не указан"

                        # Обновляем статусы (теперь после получения данных)
                        await db.execute(
                            "UPDATE rent_details SET status = 'unactive' WHERE user_id = ? AND end_time = ?",
                            (user_id, end_time_str)
                        )
                        await db.execute(
                            "UPDATE users SET bike_id = NULL, bike_name = NULL WHERE tg_id = ?",
                            (user_id,)
                        )
                        await db.execute(
                            "UPDATE bikes SET user = NULL, is_free = 1 WHERE user = ?",
                            (user_id,)
                        )

                        # Получаем админов
                        cursor_admins = await db.execute(
                            "SELECT tg_id FROM users WHERE admin = 'admin' OR admin = 'moderator'"
                        )
                        admins = await cursor_admins.fetchall()

                        await db.commit()

                        # Сообщение пользователю
                        end_time_msk = end_time + timedelta(hours=3)
                        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                            [
                                InlineKeyboardButton(text="✅ Сдал скутер", callback_data="return_bike"),
                                InlineKeyboardButton(text="📍 Где база?",
                                                     url="https://maps.yandex.ru/?text=Краснодар, Корницкого 47")
                            ],
                            [
                                InlineKeyboardButton(text='🏠 Главное меню', callback_data='main')
                            ]
                        ])

                        await bot.send_message(
                            user_id,
                            f"⛔ **Аренда завершена!**\n\n"
                            f"Дата и время окончания: **{end_time_msk.strftime('%Y-%m-%d %H:%M МСК')}**\n\n"
                            f"Пожалуйста, сдайте скутер на базу. 🚲",
                            parse_mode="Markdown",
                            reply_markup=keyboard
                        )

                        # Сообщение админам
                        for admin_tuple in admins:
                            admin_id = admin_tuple[0]
                            try:
                                await bot.send_message(
                                    admin_id,
                                    f"<code>┌──────────────────┐</code>\n"
                                    f"<b>  🏁 АРЕНДА ЗАВЕРШЕНА  </b>\n"
                                    f"<code>├──────────────────┤</code>\n"
                                    f"<b>│</b> 👤 @{username}\n"
                                    f"<b>│</b> 🔢 <code>{user_id}</code>\n"
                                    f"<b>│</b> 🏍 {bike_info}\n"
                                    f"<b>│</b> ⏰ {end_time_msk.strftime('%d.%m %H:%M')}\n"
                                    f"<code>└──────────────────┛</code>",
                                    parse_mode='HTML'
                                )
                            except Exception as e:
                                print(f"Ошибка отправки админу {admin_id}: {e}")

    except Exception as e:
        print(f"Ошибка в deactivate_expired_rents: {e}")


async def delete_old_history():
    try:

        three_months_ago = datetime.utcnow() - timedelta(days=90)

        async with aiosqlite.connect(DB_PATH) as conn:

            await conn.execute(
                "DELETE FROM rent_details WHERE end_time < ?",
                (three_months_ago.isoformat(),)
            )
            await conn.commit()


            cursor = await conn.execute("SELECT changes()")
            deleted_count = await cursor.fetchone()

            print(f"Удалено записей аренд: {deleted_count[0] if deleted_count else 0}")

    except Exception as e:
        print(f"Ошибка при удалении истории: {e}")