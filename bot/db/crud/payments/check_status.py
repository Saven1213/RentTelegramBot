import aiosqlite
from bot.db.crud.user import get_user, get_all_admins
from ..bike import get_bike_by_id

from cardlink._types import Bill, BillStatus
from cardlink.client import CardLink

from aiogram import Bot

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import cl

from .config import DB_PATH, t

import aiosqlite
from datetime import datetime


from ..rent_data import add_rent_data


# async def check_payments(bot: Bot) -> None:
#     async with aiosqlite.connect(DB_PATH) as conn:
#         cursor = await conn.cursor()
#
#         await cursor.execute(f'''
#             SELECT id, bill_id, user_id, amount, currency, days, created_at
#             FROM {t}
#             WHERE status = 'pending'
#             AND (updated_at IS NULL OR julianday('now') - julianday(updated_at) > ?)
#             LIMIT 10
#         ''', (1 / 1440,))  # 1 минута
#
#         pending_payments = await cursor.fetchall()
#
#         for payment in pending_payments:
#             payment_id, bill_id, user_id, amount, currency, days, created_at = payment
#
#             try:
#                 # Проверяем время создания
#                 created_dt = datetime.fromisoformat(created_at) if isinstance(created_at, str) else created_at
#                 time_diff = (datetime.now() - created_dt).total_seconds() / 60
#
#                 if time_diff > 15:
#                     # ❌ ВРЕМЯ ВЫШЛО - автоматически помечаем как просроченный
#                     await cursor.execute(f'''
#                         UPDATE {t}
#                         SET status = 'expired',
#                             updated_at = ?
#                         WHERE id = ?
#                     ''', (datetime.now(), payment_id))
#
#                     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#                         [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
#                     ])
#
#                     await bot.send_message(user_id,
#                                            "❌ <b>ВРЕМЯ ОПЛАТЫ ИСТЕКЛО</b>\n\n"
#                                            "⏰ Вы не успели оплатить в течение 15 минут.\n\n"
#                                            "💡 Создайте новый счет для оплаты:",
#                                            parse_mode='HTML', reply_markup=keyboard
#                                            )
#                     continue
#
#                 # Пытаемся проверить статус у платежной системы
#                 try:
#                     user = await get_user(user_id)
#                     bill: Bill = await cl.get_bill_status(id=bill_id)
#
#                     if bill.status == BillStatus.success:
#                         # ✅ ПЛАТЕЖ УСПЕШЕН
#                         await cursor.execute(f'''
#                             UPDATE {t}
#                             SET status = 'success',
#                                 updated_at = ?,
#                                 commission = ?
#                             WHERE id = ?
#                         ''', (datetime.now(), getattr(bill, 'commission', 0), payment_id))
#
#                         keyboard = InlineKeyboardMarkup(inline_keyboard=[
#                             [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
#                         ])
#
#                         await bot.send_message(user_id,
#                                                "🎉 <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>\n\n",
#                                                parse_mode='HTML', reply_markup=keyboard
#                                                )
#
#                         await add_rent_data(user[1], user[3], days=days)
#
#                     elif bill.status == BillStatus.expired:
#                         # ❌ ПЛАТЕЖ ПРОСРОЧЕН
#                         await cursor.execute(f'''
#                             UPDATE {t}
#                             SET status = 'expired',
#                                 updated_at = ?
#                             WHERE id = ?
#                         ''', (datetime.now(), payment_id))
#
#                         keyboard = InlineKeyboardMarkup(inline_keyboard=[
#                             [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")]
#                         ])
#
#                         await bot.send_message(user_id,
#                                                "❌ <b>ПЛАТЕЖ ПРОСРОЧЕН</b>\n\n",
#                                                parse_mode='HTML', reply_markup=keyboard
#                                                )
#
#                     else:
#                         # 🔄 Обновляем время проверки
#                         await cursor.execute(f'''
#                             UPDATE {t}
#                             SET updated_at = ?
#                             WHERE id = ?
#                         ''', (datetime.now(), payment_id))
#
#                 except Exception as bill_error:
#                     # 🚨 ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ОШИБКИ
#                     error_message = str(bill_error)
#                     error_type = type(bill_error).__name__
#
#                     print(f"🔍 ДЕТАЛИ ОШИБКИ для платежа {payment_id}:")
#                     print(f"Тип: {error_type}")
#                     print(f"Сообщение: {error_message}")
#                     print(f"Bill ID: {bill_id}")
#                     print(f"User ID: {user_id}")
#
#                     # ВРЕМЕННО: только логируем, но НЕ помечаем как expired
#                     print(f"⚠️ Ошибка API, но платеж #{payment_id} остается в pending")
#
#                     # Обновляем время проверки для следующей попытки
#                     await cursor.execute(f'''
#                         UPDATE {t}
#                         SET updated_at = ?
#                         WHERE id = ?
#                     ''', (datetime.now(), payment_id))
#
#             except Exception as e:
#                 print(f"❌ Общая ошибка проверки платежа {payment_id}: {e}")
#                 await cursor.execute(f'''
#                     UPDATE {t}
#                     SET updated_at = ?
#                     WHERE id = ?
#                 ''', (datetime.now(), payment_id))
#
#         await conn.commit()

async def check_payments(bot: Bot) -> None:


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


            if isinstance(created_at, str):
                try:
                    created_dt = datetime.fromisoformat(created_at)
                except ValueError:

                    created_dt = datetime.now()
            else:
                created_dt = created_at

            time_diff = (datetime.now() - created_dt).total_seconds() / 60


            if time_diff > 1:
                await cursor.execute(f'''
                    UPDATE {t}
                    SET status = 'expired',
                        updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), payment_id))

                # Пытаемся удалить сообщение со счётом
                if message_id:
                    try:
                        await bot.delete_message(chat_id=user_id, message_id=message_id)
                    except:
                        pass

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")
                        ],
                        [
                            InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile")
                        ]
                    ]
                )
                await bot.send_message(
                    user_id,
                    "❌ <b>ВРЕМЯ ОПЛАТЫ ИСТЕКЛО</b>\n\n"
                    "⏰ Вы не успели оплатить в течение 15 минут.\n\n"
                    "💡 Вы можете оплатить заново в личном кабинете",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
                continue

            # Проверяем статус у платёжной системы
            try:
                user = await get_user(user_id)
                bill: Bill = await cl.get_bill_status(id=bill_id)
            except Exception as e:
                # Обновляем updated_at и продолжаем, чтобы не блокировать остальные платежи
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

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")
                        ],
                        [
                            InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile")
                        ]
                    ]
                )
                await bot.send_message(
                    user_id,
                    f"🎉 <b>ОПЛАТА ПРОШЛА УСПЕШНО!</b>\n\n"
                    f"✅ Вы можете пользоваться арендой ещё <b>{days} дней</b>.",
                    parse_mode='HTML',
                    reply_markup=keyboard
                )

                await add_rent_data(user[1], user[3], days=days)

            elif bill.status == BillStatus.fail:
                await cursor.execute(f'''
                    UPDATE {t}
                    SET status = 'fail',
                        updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), payment_id))

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")
                        ],
                        [
                            InlineKeyboardButton(text="👤 Личный кабинет", callback_data="profile")
                        ]
                    ]
                )

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
                    parse_mode="HTML", reply_markup=keyboard
                ),

                admins = await get_all_admins()

                bike = await get_bike_by_id(user[3])
                bike_id, bike_type = bike[1], bike[2]

                for admin in admins:
                    await bot.send_message(
                        admin[1],
                        (
                            "⚠️ <b>Неудачная попытка оплаты</b>\n\n"
                            f"👤 Пользователь: <code>{user[1]}</code>\n"
                            f"🛵 Скутер: <b>{bike_type}</b> (ID: <code>{bike_id}</code>)\n"
                            f"⏳ Аренда на: <b>{days} дней</b>\n"
                            f"💰 Сумма: <b>{amount} ₽</b>\n\n"
                            "💡 Пользователь может попробовать снова или выбрать другой способ оплаты."
                        ),
                        parse_mode="HTML"
                    )

            else:
                # Обновляем время последней проверки
                await cursor.execute(f'''
                    UPDATE {t}
                    SET updated_at = ?
                    WHERE id = ?
                ''', (datetime.now().isoformat(), payment_id))

        await conn.commit()




