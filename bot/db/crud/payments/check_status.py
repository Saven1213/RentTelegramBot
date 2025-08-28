import aiosqlite
from bot.db.crud.user import get_user, get_all_admins
from ..bike import get_bike_by_id

import json

from cardlink._types import Bill, BillStatus
from cardlink.client import CardLink

from aiogram import Bot

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import cl

from .config import DB_PATH, t

import aiosqlite
from datetime import datetime

from ..names import get_personal_data
from ..rent_data import add_rent_data




async def check_payments(bot: Bot) -> None:
    admins = await get_all_admins()
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()

        await cursor.execute(f'''
            SELECT id, bill_id, user_id, amount, currency, days, created_at, message_id
            FROM {t}
            WHERE status = 'pending'
            LIMIT 10
        ''')

        pending_payments = await cursor.fetchall()

        for payment in pending_payments:
            payment_id, bill_id, user_id, amount, currency, days, created_at, message_id = payment


            await cursor.execute("""
            SELECT username
            FROM users
            WHERE tg_id = ?
            """, (user_id, ))

            user = await cursor.fetchone()

            pd = await get_personal_data(user[1])



            bill: Bill = await cl.get_bill_status(id=bill_id)

            user_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")
                    ],
                    [
                        InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile")
                    ]
                ]
            )
            admin_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")
                    ]
                ]
            )

            if bill.status != BillStatus.success and bill.active is False:
                await cursor.execute(f'''
                    UPDATE {t}
                    SET status = 'expired',
                        updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), payment_id))

                if message_id:
                    try:
                        parsed = json.loads(message_id)
                    except (json.JSONDecodeError, TypeError):
                        parsed = message_id

                    if isinstance(parsed, dict):
                        for role_name, role_dict in parsed.items():
                            for chat_id, msg_id in role_dict.items():
                                try:

                                    await bot.delete_message(chat_id=int(chat_id), message_id=int(msg_id))


                                    if role_name == 'admin':
                                        await bot.send_message(
                                            chat_id=int(chat_id),
                                            text=(
                                                "❌ <b>СЧЁТ ПРОСРОЧЕН</b>\n\n"
                                                f"⏰ Клиент {pd[2]} {pd[3]} не оплатил в течение 15 минут."
                                            ),
                                            reply_markup=admin_keyboard,
                                            parse_mode="HTML"
                                        )
                                    else:
                                        await bot.send_message(
                                            chat_id=int(chat_id),
                                            text=(
                                                "❌ <b>ВРЕМЯ ОПЛАТЫ ИСТЕКЛО</b>\n\n"
                                                "⏰ Вы не успели оплатить в течение 15 минут.\n\n"
                                                "💡 Вы можете оплатить заново в личном кабинете"
                                            ),
                                            parse_mode="HTML",
                                            reply_markup=user_keyboard
                                        )
                                except Exception as e:
                                    print(f"Ошибка обработки {chat_id=} {msg_id=}: {e}")
                    else:
                        try:
                            await bot.delete_message(chat_id=int(user_id), message_id=int(parsed))
                            await bot.send_message(
                                chat_id=int(user_id),
                                text=(
                                    "❌ <b>ВРЕМЯ ОПЛАТЫ ИСТЕКЛО</b>\n\n"
                                    "⏰ Вы не успели оплатить в течение 15 минут.\n\n"
                                    "💡 Вы можете оплатить заново в личном кабинете"
                                ),
                                parse_mode="HTML", reply_markup=user_keyboard
                            )
                        except Exception as e:
                            print(f"Ошибка обработки {user_id=} {parsed=}: {e}")

                    continue


            try:
                user = await get_user(user_id)

            except Exception as e:

                await cursor.execute(f'''
                    UPDATE {t}
                    SET updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), payment_id))
                continue

            if bill.status == BillStatus.success:
                await cursor.execute(f'''
                    UPDATE {t}
                    SET status = 'success',
                        updated_at = ?,
                        commission = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), getattr(bill, 'commission', 0), payment_id))


                await bot.send_message(
                    user_id,
                    f"🎉 <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>\n\n"
                    f"✅ Вы можете пользоваться арендой ещё <b>{days} дней</b>.",
                    parse_mode='HTML',
                    reply_markup=user_keyboard
                )

                await add_rent_data(user[1], user[3], days=days)

            elif bill.status == BillStatus.fail:
                await cursor.execute(f'''
                    UPDATE {t}
                    SET status = 'fail',
                        updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), payment_id))



                await bot.send_message(
                    user_id,
                    (
                        "❌ <b>Оплата не прошла</b>\n\n"
                        "Возможно, на карте недостаточно средств или произошла ошибка при оплате.\n\n"
                        "💡 <b>Что можно сделать?</b>\n"
                        "• Попробуйте оплатить снова\n"
                        "• Используйте другой способ или карту\n\n"
                        "🔑 Перейдите в <b>Личный кабинет</b>, чтобы повторить оплату."
                    ),
                    parse_mode="HTML", reply_markup=user_keyboard
                ),



                bike = await get_bike_by_id(user[3])
                bike_id, bike_type = bike[1], bike[2]

                pd = await get_personal_data(user[1])

                for admin in admins:
                    await bot.send_message(
                        admin[1],
                        (
                            "⚠️ <b>Неудачная попытка оплаты</b>\n\n"
                            f"👤 Клиент: <code>{pd[2]} {pd[3]}</code>\n"
                            f"🛵 Скутер: <b>{bike_type}</b> (ID: <code>{bike_id}</code>)\n"
                            f"⏳ Аренда на: <b>{days} дней</b>\n"
                            f"💰 Сумма: <b>{amount} ₽</b>\n\n"
                            "💡 Клиент может попробовать снова или выбрать другой способ оплаты."
                        ),
                        parse_mode="HTML",
                        reply_markup=admin_keyboard
                    )

            else:

                await cursor.execute(f'''
                    UPDATE {t}
                    SET updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), payment_id))

        await conn.commit()



async def check_payment_debts(bot: Bot):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"""
        SELECT user_id, order_id, bill_id, message_id, amount, description
        FROM {t}
        WHERE status = 'pending_debt'
        """)

        pending_payments = await cursor.fetchall()

        for payment in pending_payments:
            user_id, order_id, bill_id, message_id, amount, description = payment

            bill: Bill = await cl.get_bill_status(id=bill_id)

            if bill.active is False and bill.status != BillStatus.success:
                await cursor.execute(f"""
                UPDATE {t}
                SET status = 'expired'
                WHERE order_id = ?
                """, (order_id,))
                await conn.commit()

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text='📊 Личный кабинет', callback_data='profile')],
                        [InlineKeyboardButton(text='🏠 В главное меню', callback_data='main')]
                    ]
                )

                try:
                    await bot.delete_message(chat_id=user_id, message_id=message_id)
                except Exception:
                    pass

                text = (
                    "⏰ <b>ПЛАТЕЖ ПРОСРОЧЕН</b>\n\n"
                    "❌ <i>Время оплаты истекло</i>\n\n"
                    "💡 <b>Что делать?</b>\n"
                    "▫️ Создайте новый счет для оплаты\n"
                    "▫️ Оплатите в течение 15 минут\n\n"
                    "⚠️ <i>Старый счет больше не действителен</i>"
                )

                await bot.send_message(chat_id=user_id, text=text, parse_mode='HTML', reply_markup=keyboard)

            if bill.status == BillStatus.success:

                await cursor.execute(f"""
                UPDATE {t}
                SET status = 'success'
                WHERE order_id = ?
                """, (order_id,))
                await conn.commit()

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text='💰 Мои долги', callback_data='my_debts')],
                        [InlineKeyboardButton(text='🏠 В главное меню', callback_data='main')]
                    ]
                )

                try:
                    await bot.delete_message(chat_id=user_id, message_id=message_id)
                except Exception:
                    pass

                description_for_msg = description.replace('_', ': ')

                text = (
                    "✅ <b>ПЛАТЕЖ УСПЕШНО ОПЛАЧЕН!</b>\n\n"
                    "💰 <i>Счет успешно обработан</i>\n\n"
                    "🎉 <b>Долг погашен</b>\n"
                    f"▫️ Сумма: <b>{amount} ₽</b>\n"
                    f"▫️ Описание: {description_for_msg}\n\n"
                    "💚 <i>Спасибо за оплату!</i>"
                )

                await cursor.execute("""
                DELETE FROM debts
                WHERE description = ?
                """, (description.split('_')[1], ))

                await conn.commit()

                await bot.send_message(chat_id=user_id, text=text, parse_mode='HTML', reply_markup=keyboard)

            if bill.status == BillStatus.fail:
                await cursor.execute(f"""
                UPDATE {t}
                SET status = 'fail'
                WHERE order_id = ?
                """, (order_id,))
                await conn.commit()

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="👨‍🔧 Техподдержка WhatsApp", url="https://wa.me/79188097196")],
                        [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="retry_payment")],
                        [InlineKeyboardButton(text='📊 Личный кабинет', callback_data='profile')],
                        [InlineKeyboardButton(text='🏠 В главное меню', callback_data='main')]
                    ]
                )

                text = (
                    "❌ <b>ПЛАТЕЖ НЕ ПРОШЕЛ</b>\n\n"
                    "💸 <i>Оплата не была завершена</i>\n\n"
                    "⚠️ <b>Возможные причины:</b>\n"
                    "▫️ Недостаточно средств на карте\n"
                    "▫️ Банк отклонил операцию\n"
                    "▫️ Технические проблемы\n\n"
                    "💡 <b>Наша поддержка поможет:</b>"
                )

                await bot.send_message(chat_id=user_id, text=text, parse_mode='HTML', reply_markup=keyboard)



