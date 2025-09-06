from aiogram import Bot



from datetime import datetime, timedelta, time
import aiosqlite
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiosqlite import connect
from pydantic import BaseModel

from bot.db.crud.bike import get_bike_by_id
from bot.db.crud.names import get_personal_data
from bot.db.crud.payments.check_status import check_payments, check_payment_debts


DB_PATH = "rent-bike.db"


async def check_rent_status(bot: Bot):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🔄 Продлить аренду', callback_data='extend'),
            InlineKeyboardButton(text='⏳ Оплачу позже', callback_data='pay_later')
        ],
        [
            InlineKeyboardButton(text='❌ Не продлевать', callback_data='cancel_pay_rent')
        ]
    ])

    try:
        async with aiosqlite.connect(DB_PATH) as conn:
            cursor = await conn.execute(
                "SELECT id, user_id, end_time, notified FROM rent_details WHERE status = 'active'"
            )
            rows = await cursor.fetchall()

        now_utc = datetime.utcnow()
        now_msk = now_utc + timedelta(hours=3)

        for id_, user_id, end_time_str, notified in rows:
            if end_time_str and notified == 0:
                end_time_utc = datetime.fromisoformat(end_time_str)
                end_time_msk = end_time_utc + timedelta(hours=3)

                notification_hour = 10

                if now_msk.date() == end_time_msk.date():


                    if time(notification_hour, 0) <= now_msk.time() < time(notification_hour + 1, 0):
                # if 1 == 1:
                #     if 1 == 1:
                        time_left = end_time_msk - now_msk
                        hours_left = int(time_left.total_seconds() // 3600)
                        minutes_left = int((time_left.total_seconds() % 3600) // 60)


                        await bot.send_message(
                            user_id,
                            f"⏰ <b>АРЕНДА ЗАКАНЧИВАЕТСЯ СЕГОДНЯ!</b>\n\n"
                            f"📅 <b>Окончание:</b> {end_time_msk.strftime('%d.%m.%Y %H:%M')} МСК\n"
                            f"⏳ <b>Осталось:</b> {hours_left}ч {minutes_left}м\n\n"
                            f"💡 <i>Хотите продлить аренду?</i>",
                            parse_mode='HTML',
                            reply_markup=keyboard
                        )


                        async with aiosqlite.connect(DB_PATH) as conn:
                            await conn.execute(
                                "UPDATE rent_details SET notified = 1, pay_later = 1 WHERE user_id = ? AND end_time = ?",
                                (user_id, end_time_str)
                            )
                            await conn.commit()







    except Exception as e:

        pass

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

                        cursor_user = await db.execute(
                            "SELECT username, bike_id, bike_name FROM users WHERE tg_id = ?",
                            (user_id,)
                        )
                        user_result = await cursor_user.fetchone()
                        username = user_result[0] if user_result else f"user_{user_id}"
                        bike_id = user_result[1] if user_result else None
                        bike_name = user_result[2] if user_result else None

                        bike_info = f"{bike_name} #{bike_id}" if bike_id and bike_name else "не указан"


                        # await db.execute(
                        #     "UPDATE rent_details SET status = 'unactive' WHERE user_id = ? AND end_time = ?",
                        #     (user_id, end_time_str)
                        # )
                        # await db.execute(
                        #     "UPDATE users SET bike_id = NULL, bike_name = NULL WHERE tg_id = ?",
                        #     (user_id,)
                        # )
                        # await db.execute(
                        #     "UPDATE bikes SET user = NULL, is_free = 1 WHERE user = ?",
                        #     (user_id,)
                        # )


                        cursor_admins = await db.execute(
                            "SELECT tg_id FROM users WHERE admin = 'admin' OR admin = 'moderator'"
                        )
                        admins = await cursor_admins.fetchall()

                        # await db.commit()


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
                            f"Пожалуйста, сдайте скутер на базу в течении часа. 🚲\n\n"
                            f"*Или можете оплатить продление до этого времени в личном кабинете.*\n\n"
                            f"⚠️ *Внимание:* Сумма просрочки составляет **150% в день** от дневного тарифа",
                            parse_mode="Markdown",
                            reply_markup=keyboard
                        )


                        pd = await get_personal_data(user_id)

                        for admin_tuple in admins:
                            admin_id = admin_tuple[0]
                            try:
                                await bot.send_message(
                                    admin_id,
                                    f"<code>┌──────────────────┐</code>\n"
                                    f"<b>  🏁 АРЕНДА ЗАВЕРШЕНА  </b>\n"
                                    f"<code>├──────────────────┤</code>\n"
                                    f"<b>│</b> 👤 {pd[3]} {pd[4]}\n"
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

async def check_payments_job():
    from bot.main import bot
    await check_payments(bot)

async def check_payments_debts_job():
    from bot.main import bot
    await check_payment_debts(bot)

async def check_pay_later_in_data():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        UPDATE rent_details
        SET pay_later = 0
        WHERE status = 'unactive'
        """)

        await conn.commit()

async def check_pay_later_in_data_job():
    await check_pay_later_in_data()


class DR(BaseModel):
    id: int
    user_id: int
    bike_id: int
    notified: int
    start_time: str
    end_time: str
    status: str
    days: int
    pay_later: int


async def check_delay():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
        SELECT * 
        FROM rent_details
        WHERE datetime('now', 'utc') > datetime(end_time)
        AND status = 'active'
        """)

        delayed_rents = await cursor.fetchall()



        for rent_row in delayed_rents:
            dr = DR(
                id=rent_row[0],
                user_id=rent_row[1],
                bike_id=rent_row[2],
                notified=rent_row[3],
                start_time=rent_row[4],
                end_time=rent_row[5],
                status=rent_row[6],
                days=rent_row[7],
                pay_later=rent_row[8]
            )

            end_time_utc = datetime.fromisoformat(dr.end_time.replace('Z', '+00:00'))
            time_delayed = datetime.utcnow() - end_time_utc

            if time_delayed >= timedelta(days=1):
                days_delayed = time_delayed.days


                await cursor.execute("""
                SELECT *
                FROM delays
                WHERE rent_id = ?
                """, (dr.id, ))

                current_delay = await cursor.fetchone()




                await cursor.execute("""
                SELECT * FROM bikes WHERE id = ?
                """, (dr.bike_id,))

                bike = await cursor.fetchone()


                if not bike:
                    continue


                match dr.days:
                    case days if days >= 30:
                        daily_rate = bike[9]
                    case days if days >= 7:
                        daily_rate = bike[8]
                    case days if days >= 3:
                        daily_rate = bike[7]

                amount_delay = int(daily_rate * 1.5 * days_delayed)

                if current_delay:
                    await cursor.execute("""
                    UPDATE delays
                    SET days_delay = ?, amount_delay = ?
                    WHERE rent_id = ?
                    """, (days_delayed, amount_delay, dr.id))
                else:
                    await cursor.execute("""
                    INSERT INTO delays
                    (rent_id, tg_id, days_delay, amount_delay)
                    VALUES (?, ?, ?, ?)
                    """, (dr.id, dr.user_id, days_delayed, amount_delay))

                await conn.commit()

async def check_delay_job():
    await check_delay()



