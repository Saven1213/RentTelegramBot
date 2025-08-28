from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from aiogram.types import Message, CallbackQuery

from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from bot.db.crud.names import get_personal_data
from bot.db.crud.payments.create_payment import create_payment
from bot.db.crud.user import get_user, add_user

router = Router()

from cardlink._types import Bill
from bot.config import cl
import uuid




@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    await state.clear()

    tg_id = message.from_user.id
    username = message.from_user.username
    user = await get_user(tg_id)
    pd = await get_personal_data(tg_id)
    if user is None:
        await add_user(tg_id, username)

    if pd:

        try:
            if user[3] is None or user[3] == 'null':
                if user[-1] == 'admin' or user[-1] == 'moderator':
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text='🛵 Арендовать скутер', callback_data='scooter')
                        ],
                        [
                            InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                        ],
                        [
                            InlineKeyboardButton(text='❓ Помощь', url='http://t.me/'),
                            InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                        ],
                        [
                            InlineKeyboardButton(text='⚡ Админ панель', callback_data='admin_main')
                        ]

                    ])
                else:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text='🛵 Арендовать скутер', callback_data='scooter')
                        ],
                        [
                            InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                        ],
                        [
                            InlineKeyboardButton(text='❓ Поддержка', callback_data='support'),
                            InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                        ]
                    ])
            else:
                if user[-1] == 'admin' or user[-1] == 'moderator':
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                        ],
                        [
                            InlineKeyboardButton(text='❓ Поддержка', callback_data='support'),
                            InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                        ],
                        [
                            InlineKeyboardButton(text='⚡ Админ панель', callback_data='admin_main')
                        ]
                    ])
                else:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                        ],
                        [
                            InlineKeyboardButton(text='❓ Поддержка', callback_data='support'),
                            InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                        ]
                    ])

        except TypeError:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text='🛵 Арендовать скутер', callback_data='scooter')
                ],
                [
                    InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                ],
                [
                    InlineKeyboardButton(text='❓ Поддержка', callback_data='support'),
                    InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                ]
            ])

        welcome_text = (
            "🛵 <b>ХАЛК БАЙК - ПРОКАТ СКУТЕРОВ</b> 🟢\n\n"
            "⚡ <b>Почему выбирают нас:</b>\n"
            "✅ <b>Быстро</b> - оформление за 10 минут ⏱️\n"
            "💰 <b>Выгодно</b> - от 300₽/день\n"
            "🛡️ <b>Безопасно</b> - исправная техника + шлемы 🪖\n\n"
            "—————————————————\n"
            "📌 <b>Как начать?</b>\n"
            "1️⃣ Приходите на базу: <i>ул. Корницкого, 47</i> 📍\n"
            "2️⃣ Выбирайте скутер - парк всегда обновляется 🔄\n"
            "3️⃣ Подписываете договор - и получаете ключи! 🚀\n\n"
            "—————————————————\n"
            "⏰ <i>Режим работы: пн-пт, 10:00-20:00</i>\n"
            "❓ Есть вопросы? Жмите «Помощь» 💬"
        )

        await message.answer(
            text=welcome_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:

        text = (
            "🛵 <b>ХАЛК БАЙК - ПРОКАТ СКУТЕРОВ</b> 🟢\n\n"
            "📋 <b>Для начала аренды:</b>\n"
            "✅ <b>Заполните анкету</b> - это обязательно\n"
            "🚀 <b>Арендуйте скутер</b> - после подтверждения\n\n"
            "—————————————————\n"
            "📌 <b>Как это работает?</b>\n"
            "1️⃣ Заполняете анкету 📝\n"
            "2️⃣ Выбираете скутер 🏍️\n"
            "3️⃣ Подписываете договор 📄\n"
            "4️⃣ Получаете ключи! 🔑\n\n"
            "—————————————————\n"
            "💎 <i>Анкета занимает всего 1 минуту!</i>\n"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📝 Заполнить анкету", callback_data="action")]
            ]
        )

        await message.answer(text=text, parse_mode='HTML', reply_markup=keyboard)



@router.callback_query(F.data == 'main')
async def main(callback: CallbackQuery):
    tg_id = callback.from_user.id

    user = await get_user(tg_id)



    tg_id = callback.from_user.id
    username = callback.from_user.username
    user = await get_user(tg_id)

    if user is None:
        await add_user(tg_id, username)

    if user and user[3] is None or user and user[3] == 'null':
        if user[-1] == 'admin' or user[-1] == 'moderator':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text='🛵 Арендовать скутер', callback_data='scooter')
                ],
                [
                    InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                ],
                [
                    InlineKeyboardButton(text='❓ Поддержка', callback_data='support'),
                    InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                ],
                [
                    InlineKeyboardButton(text='⚡ Админ панель', callback_data='admin_main')
                ]
            ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text='🛵 Арендовать скутер', callback_data='scooter')
                ],
                [
                    InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                ],
                [
                    InlineKeyboardButton(text='❓ Поддержка', callback_data='support'),
                    InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                ]
            ])

    else:
        if user[-1] == 'admin' or user[-1] == 'moderator':
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                ],
                [
                    InlineKeyboardButton(text='❓ Поддержка', callback_data='support'),
                    InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                ],
                [
                    InlineKeyboardButton(text='⚡ Админ панель', callback_data='admin_main')
                ]
            ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[

                [
                    InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                ],
                [
                    InlineKeyboardButton(text='❓ Поддержка', callback_data='support'),
                    InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                ]
            ])

    welcome_text = (
        "🛵 <b>ХАЛК БАЙК - ПРОКАТ СКУТЕРОВ</b> 🟢\n\n"

        "⚡ <b>Почему выбирают нас:</b>\n"
        "✅ <b>Быстро</b> - оформление за 10 минут ⏱️\n"
        "💰 <b>Выгодно</b> - от 300₽/день\n"
        "🛡️ <b>Безопасно</b> - исправная техника + шлемы 🪖\n\n"

        "—————————————————\n"
        "📌 <b>Как начать?</b>\n"
        "1️⃣ Приходите на базу: <i>ул. Корницкого, 47</i> 📍\n"
        "2️⃣ Выбирайте скутер - парк всегда обновляется 🔄\n"
        "3️⃣ Подписываете договор - и получаете ключи! 🚀\n\n"

        "—————————————————\n"
        "⏰ <i>Режим работы: пн-пт, 10:00-20:00</i>\n"
        "❓ Есть вопросы? Жмите «Помощь» 💬"
    )

    await callback.message.edit_text(
        text=welcome_text,
        parse_mode="HTML",
        reply_markup=keyboard
    )


# @router.callback_query(F.data == 'payment_func')
# async def payment_test(callback: CallbackQuery):
#     try:
#         tg_id = callback.from_user.id
#         user = await get_user(tg_id)
#
#         if not user:
#             await callback.answer("❌ Пользователь не найден", show_alert=True)
#             return
#
#         bike_id = user[3]
#         order_id = f'order-{uuid.uuid4().hex[:8]}-{bike_id}-{tg_id}'
#
#         # Создаем тестовый счет на 10 рублей
#         create_bill: Bill = await cl.create_bill(
#             amount=10,
#             order_id=order_id,
#             currency_in='RUB'
#         )
#
#         # Сохраняем в БД
#
#
#         keyboard = InlineKeyboardMarkup(inline_keyboard=[
#             [InlineKeyboardButton(text='💳 Оплатить', url=create_bill.link_page_url)]
#         ])
#
#         message = await callback.message.edit_text(
#             '🧪 Тестовый платеж: 10 руб\n'
#             f'🔗 Ссылка: {create_bill.link_page_url}\n'
#             f'📋 ID счета: {create_bill.id}',
#             reply_markup=keyboard
#         )
#         await create_payment(
#             tg_id=tg_id,
#             order_id=order_id,
#             id_=create_bill.id,
#             price=10,
#             time=10,
#             message_id=message.message_id
#         )
#
#     except Exception as e:
#         await callback.answer("❌ Ошибка создания тестового счета", show_alert=True)
#         # print(f"Test payment error: {e}")
# @router.message(F.photo)
# async def get_photo_id(message: Message):
#     photo = message.photo[-1].file_id


@router.callback_query(F.data == 'contacts')
async def contacts(callback: CallbackQuery):
    text = (
        "📞 <b>КОНТАКТЫ ХАЛК БАЙК</b> 🟢\n\n"
        "<blockquote>"
        "<code>"
        "👨‍🔧 Мастер/Техподдержка:\n"
        "+7 (918) 809-71-96\n"
        "WhatsApp\n\n"
        "👨‍💼 Основной аккаунт:\n"
        "+7 (995) 899-58-29\n"
        "WhatsApp\n"
        "</code>"
        "</blockquote>\n\n"
        "💬 <i>Выберите, кому написать:</i>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨‍🔧 Написать мастеру", url="https://wa.me/79188097196")],
            [InlineKeyboardButton(text="👨‍💼 Написать в основной", url="https://wa.me/79958995829")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="main")]
        ]
    )

    await callback.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

















