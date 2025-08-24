from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.cardlink import CardLink

from time import time

from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext



from datetime import datetime



from bot.db.crud.bike import get_bike_by_type, get_bike_by_id, get_price
from bot.db.crud.rent_data import get_data_rents, get_current_rent
from bot.db.crud.user import get_user, add_user, get_all_users
from bot.cardlink.api_types.CreatedInvoice import CreatedInvoice

router = Router()


cl = CardLink(token='sss', shop_id='123')

@router.message(CommandStart())
async def start_command(message: Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    user = await get_user(tg_id)

    if user is None:
        await add_user(tg_id, username)



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
                        InlineKeyboardButton(text='❓ Помощь', url='http://t.me/'),
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
                        InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                    ],
                    [
                        InlineKeyboardButton(text='❓ Помощь', url='http://t.me/'),
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
                InlineKeyboardButton(text='❓ Помощь', url='http://t.me/'),
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

@router.callback_query(F.data == 'scooter')
async def rent_scooter(callback: CallbackQuery):
    tg_id = callback.from_user.id

    user = await get_user(tg_id)

    # print(user, ' посмотрел функцию аренду скутера (1)')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🏍️ Dio', callback_data='view_scooter-dio'),
            InlineKeyboardButton(text='⚡ Jog', callback_data='view_scooter-jog')
        ],
        [
            InlineKeyboardButton(text='🚀 Gear', callback_data='view_scooter-gear')
        ],
        [
            InlineKeyboardButton(text='◀️ Назад', callback_data='main')
        ]
    ])

    price_message = """
    <code>——————————————————————</code>
    <b>🏍  ТАРИФЫ  🏍</b>  
    <code>——————————————————————</code>

    <b>🔵 DIO (50cc)</b>  
    ┣ 3 дня — <b>500₽</b>  
    ┣ Неделя — <b>400₽/день</b>  
    ┗ Месяц — <b>300₽/день</b>  

    <b>🟢 JOG (50cc)</b>  
    ┣ 3 дня — <b>600₽</b>  
    ┣ Неделя — <b>500₽/день</b>  
    ┗ Месяц — <b>400₽/день</b>  

    <b>🔴 GEAR (50cc)</b>  
    ┣ 3 дня — <b>700₽</b>  
    ┣ Неделя — <b>600₽/день</b>  
    ┗ Месяц — <b>500₽/день</b>  

    <code>——————————————————————</code>  
    
    """

    await callback.message.edit_text(
        text=price_message,
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.callback_query(F.data == 'main')
async def main(callback: CallbackQuery):
    tg_id = callback.from_user.id

    user = await get_user(tg_id)

    # print(user, ' вернулся в меню')

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
                    InlineKeyboardButton(text='❓ Помощь', url='http://t.me/'),
                    InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')
                ]
            ])

    else:
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
                    InlineKeyboardButton(text='👤 Личный кабинет', callback_data='profile')
                ],
                [
                    InlineKeyboardButton(text='❓ Помощь', url='http://t.me/'),
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


@router.callback_query(F.data.split('-')[0] == 'view_scooter')
async def change_scooter(callback: CallbackQuery):
    tg_id = callback.from_user.id
    data = callback.data.split('-')[1]

    bikes = await get_bike_by_type(data)

    # Проверяем, есть ли свободные скутеры
    free_bikes_available = False
    if bikes:
        for bike in bikes:
            # bike[3] - это поле user (кто арендовал)
            if bike[3] is None:  # Если скутер свободен
                free_bikes_available = True
                break

    if not free_bikes_available:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='Назад', callback_data='scooter')
            ]
        ])
        await callback.message.edit_text(
            f'На данный момент {data} нет в наличии 😢\nПосмотрите другие варианты!',
            reply_markup=keyboard
        )
        return

    # Если есть свободные скутеры
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for bike in bikes:
        # Показываем только свободные скутеры
        if bike[3] is None:  # bike[3] - поле user (кто арендовал)
            bike_icons = {
                'dio': '🔵',
                'jog': '🟢',
                'gear': '🔴'
            }
            icon = bike_icons.get(bike[2].lower(), '🏍')

            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"{icon} {bike[2].upper()} #{bike[1]}",
                        callback_data=f"bikerent-{bike[0]}"
                    )
                ]
            )

    # Если после фильтрации не осталось свободных скутеров (маловероятно, но на всякий случай)
    if not keyboard.inline_keyboard:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='Назад', callback_data='scooter')
            ]
        ])
        await callback.message.edit_text(
            f'На данный момент {data} нет в наличии 😢\nПосмотрите другие варианты!',
            reply_markup=keyboard
        )
        return

    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data='scooter')
        ]
    )
    await callback.message.edit_text('🚀 Свободные скутеры на выбор: ', reply_markup=keyboard)


@router.callback_query(F.data.split('-')[0] == 'bikerent')
async def bike_number(callback: CallbackQuery):
    tg_id = callback.from_user.id

    # user = await get_user(tg_id)
    #
    # print(user, ' находится на карточке мотоцикла')

    data = callback.data.split('-')[1]
    bike = await get_bike_by_id(data)

    # Иконки для разных моделей
    model_icons = {
        'dio': '🔵 DIO',
        'jog': '🟢 JOG',
        'gear': '🔴 GEAR'
    }
    model_display = model_icons.get(bike[2].lower(), f'🏍 {bike[2].upper()}')

    bike_card = f"""
<code>┏━━━━━━━━━━━━━━━━━━━━━━━━┓</code>
<b>  🏍 СКУТЕР #{bike[1]}  </b>
<code>┣━━━━━━━━━━━━━━━━━━━━━━━━┫</code>
<b>│  🚀 Модель:</b> {model_display}
<b>│  ⛽ Топливо:</b> АИ-{bike[5]}
<b>│  🔧 Последнее ТО в :</b> {bike[4]} км
<b>│  ✅ Статус:</b> СВОБОДЕН
<code>┗━━━━━━━━━━━━━━━━━━━━━━━━┛</code>

<i>✨ Готов к аренде прямо сейчас!</i>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🛵 Арендовать', callback_data=f'period-{bike[0]}'),
            InlineKeyboardButton(text='📞 Поддержка', url='t.me/hulkbike_support')
        ],
        [
            InlineKeyboardButton(text='↩️ К списку', callback_data=f'view_scooter-{bike[2].lower()}')
        ]
    ])

    await callback.message.edit_text(
        text=bike_card,
        parse_mode='HTML',
        reply_markup=keyboard
    )

# @router.callback_query(F.data == 'test_payment')
# async def test_payment(callback: CallbackQuery, bot: Bot):
#     tg_id = callback.from_user.id
#
#     user = await get_user(tg_id)
#
#     print(user, ' протестил функцию оплаты (1)')
#
#     payment_check = """
#     <code>┌──────────────────────────────┐</code>
#     <b>  � ЧЕК ОПЛАТЫ #A23245674</b>
#     <code>├──────────────────────────────┤</code>
#     <b>│ Модель:</b> Jog
#     <b>│ Тариф:</b> Месяц
#     <b>│ Начало:</b> 10.07.2025
#     <b>│ Окончание:</b> 10.08.2025
#     <code>├──────────────────────────────┤</code>
#     <b>│ Итого к оплате:</b> <u>12000₽</u>
#     <code>└──────────────────────────────┘</code>
#
#     ⚠️ <i>Ваша аренда завершается через 2 дня!</i>
#     """
#
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(text="🔄 Продлить аренду", callback_data=f"extend"),
#             InlineKeyboardButton(text="⏳ Оплачу позже", callback_data="pay_later")
#         ],
#         [
#             InlineKeyboardButton(text="❌ Не продлевать", callback_data=f"cancel")
#         ],
#         [
#             InlineKeyboardButton(text="📞 Поддержка", url="t.me/hulkbike_support")
#         ]
#     ])
#
#     await bot.send_message(
#         chat_id=callback.from_user.id,
#         text=payment_check,
#         parse_mode='HTML',
#         reply_markup=keyboard
#     )

# @router.callback_query(F.data == 'extend')
# async def extend_bike(callback: CallbackQuery):
#     tg_id = callback.from_user.id
#
#     user = await get_user(tg_id)
#
#     print(user, ' продлил оплату ')
#
#
#     payment_success = f"""
#     <code>┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓</code>
#     <b>  💳 ОПЛАТА ПРОИЗВЕДЕНА  </b>
#     <code>┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫</code>
#     <b>│</b> 🔹 Номер заказа: <code>#A23245674</code>
#     <b>│</b> 🔹 Сумма: <b>12000₽</b>
#     <b>│</b> 🔹 Способ: <i>СБП</i>
#     <code>┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫</code>
#     <b>│</b> 🏍 Модель: <b>JOG</b>
#     <b>│</b> ⏳ Срок аренды: <b>месяц</b>
#     <b>│</b> 📍 Локация: <i>Краснодар</i>
#     <code>┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛</code>
#
#     <b>✅ Ваш скутер готов к использованию!</b>
#     <i>Приятной поездки и соблюдайте ПДД!</i> 🚦
#     """
#
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [
#             InlineKeyboardButton(text="🛵 Мой скутер", callback_data="my_bike"),
#             InlineKeyboardButton(text="📊 Профиль", callback_data="profile")
#         ],
#         [
#             InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
#             InlineKeyboardButton(text="📝 Чек", callback_data=f"receipt")
#         ],
#         [
#             InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")
#         ]
#     ])
#     await callback.message.edit_text(
#         text=payment_success,
#         parse_mode='HTML',
#         reply_markup=keyboard
#     )
#
# @router.callback_query(F.data == 'pay_later')
# async def pay_later(callback: CallbackQuery):
#     await callback.message.delete()
#
#     tg_id = callback.from_user.id
#
#     user = await get_user(tg_id)
#
#     print(user, ' нажал напомнить позже про оплату ')
#
# @router.callback_query(F.data == 'cancel')
# async def cancel_rent_handler(callback: CallbackQuery):
#     tg_id = callback.from_user.id
#
#     user = await get_user(tg_id)
#
#     print(user, ' отменил оплату')
#
#     cancel_message = f"""
# <code>┌──────────────────────────────┐</code>
# <b>  🚫 АРЕНДА ОТМЕНЕНА  </b>
# <code>├──────────────────────────────┤</code>
# <b>│</b> 🔹 Скутер: <b>JOG</b>
# <b>│</b> 🔹 Номер: <code>#27</code>
# <code>├──────────────────────────────┤</code>
# <b>│</b> ⏳ Время отмены: <i>{datetime.now().strftime('%d.%m %H:%M')}</i>
# <b>│</b> ⏳ Конец аренды: <i>10.08.2025</i>
# <code>└──────────────────────────────┛</code>
#
# <i>Скутер доступен для новой аренды.</i>
# Спасибо, что пользовались Hulk Bike! 🛵💚
# """
#
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_feedback")],
#         [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")]
#     ])
#
#     await callback.message.edit_text(
#         text=cancel_message,
#         parse_mode="HTML",
#         reply_markup=keyboard
#     )

@router.callback_query(F.data.split('-')[0] == 'period')
async def period(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    data = callback.data.split('-')[1]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📅 3 дня', callback_data=f'rent_scooter_but-{data}-3'),
            InlineKeyboardButton(text='📅 7 дней', callback_data=f'rent_scooter_but-{data}-7')
        ],
        [
            InlineKeyboardButton(text='📅 30 дней', callback_data=f'rent_scooter_but-{data}-30')
        ],
        [
            InlineKeyboardButton(text='✏️ Выбрать вручную', callback_data=f'write_period-{data}')
        ]
    ])

    await callback.message.edit_text(
        "🏍️ <b>ВЫБЕРИТЕ СРОК АРЕНДЫ</b>\n\n"
        "🚀 <i>Готовы к поездке? Выбирайте удобный период:</i>\n\n"
        "🔹 <b>3 дня</b> — идеально для теста\n"
        "🔹 <b>7 дней</b> — оптимальный вариант\n"
        "🔹 <b>30 дней</b> — максимальная выгода\n\n"
        "💎 <i>Нужен другой срок? Укажите вручную</i>",
        parse_mode='HTML',
        reply_markup=keyboard
    )

class SelectPeriod(StatesGroup):
    change_period = State()



@router.callback_query(F.data.split('-')[0] == 'write_period')
async def write_period(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('-')[1]  # достаём {data}
    await state.update_data(rent_data=data)  # сохраняем в FSM
    await state.set_state(SelectPeriod.change_period)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data=f'period-{data}')
        ]
    ])

    await callback.message.edit_text(
        "✏️ <b>УКАЖИТЕ СРОК АРЕНДЫ</b>\n\n"
        "📝 <i>Введите количество дней цифрами:</i>\n"
        "• Например: 3, 5, 7, 10, 14...\n\n"
        "⚠️ <b>Минимальный срок:</b> 3 дня\n"
        "💡 <i>Чем дольше — тем выгоднее цена!</i>",
        parse_mode='HTML',
        reply_markup=keyboard
    )


@router.message(SelectPeriod.change_period)
async def state_period_handler(message: Message, state: FSMContext):
    msg = message.text
    data = await state.get_data()
    rent_data = data.get("rent_data")

    if msg.isdigit():
        days = int(msg)
        if days >= 3:

            callback_data = f"rent_scooter_but-{rent_data}-{days}"


            await message.answer(
                f"⏳ Вы указали срок аренды: <b>{days} дней</b>.\n\n"
                f"✅ Проверьте данные и подтвердите аренду, либо измените срок.",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[
                        InlineKeyboardButton(
                            text="✅ Подтвердить аренду",
                            callback_data=callback_data
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="🔄 Изменить срок аренды",
                            callback_data=f"write_period-{rent_data}"
                        )
                    ]]
                ), parse_mode='HTML'
            )

            await state.clear()
        else:
            await message.answer(
                "⚠️ Минимальный срок аренды — <b>3 дня</b>.\n"
                "Попробуйте ввести другое количество дней ⬇️", parse_mode='HTML'
            )
    else:
        await message.answer(
            "❌ Неверный формат ввода.\n\n"
            "Пожалуйста, укажите количество дней цифрой, например: <b>5</b>", parse_mode='HTML'
        )


@router.callback_query(F.data.split('-')[0] == 'rent_scooter_but')
async def but_rent(callback: CallbackQuery):
    tg_id = callback.from_user.id
    bike_id = int(callback.data.split('-')[1])
    time_ = int(callback.data.split('-')[2])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
    ])

    # user_data, bike_data, rented_now = await rent_bike(tg_id, bike_id, time)

    # Получаем актуальные цены
    prices = await get_price()
    bike_model = await get_bike_by_id(bike_id)

    # Форматирование времени
    if time_ == 1:
        text_time = "1 день"
    elif time_ < 5:
        text_time = f"{time} дня"
    else:
        text_time = f"{time} дней"

    # Расчет цены
    if time_ == 1:
        price = prices[bike_model]['day']
    elif time_ < 7:
        price = prices[bike_model]['day'] * time
    elif time_ < 30:
        weeks = time_ // 7
        remaining_days = time_ % 7
        price = (prices[bike_model]['week'] * weeks +
                prices[bike_model]['day'] * remaining_days)
    else:
        months = time_ // 30
        remaining_days = time_ % 30
        price = (prices[bike_model]['month'] * months +
                prices[bike_model]['day'] * remaining_days)

    # if rented_now:
        # Создаем счет с правильной ценой (БЕЗ умножения на 100)
    created_invoice: CreatedInvoice = await cl.create_invoice(
        amount=price,  # цена уже в рублях из БД
        order_id=f"order-{tg_id}-{bike_id}-{int(time())}",
        currency_in='RUB'
    )

    keyboard_invoice = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='💳 Оплатить', url=created_invoice.link_url)],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
    ])

    await callback.message.edit_text(
        f"🎉 Отличный выбор!\n\n"
        f"🚴 Скутер <b>{bike_model}</b>\n"
        f"💵 Сумма к оплате: <b>{price} руб</b>\n\n"
        f"Для подтверждения аренды нажмите кнопку оплаты ниже 👇",
        reply_markup=keyboard_invoice,
        parse_mode='HTML'
    )

    # else:
    #     await callback.message.edit_text(
    #         "⚠️ У вас уже есть активная аренда скутера!\n\n"
    #         "Сначала завершите текущую аренду, а потом сможете взять новый 🚴",
    #         reply_markup=keyboard
    #     )


@router.callback_query(F.data == 'pay_later')
async def pay_later(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Личный кабинет", callback_data="profile")]
    ])

    await callback.message.edit_text(
        "💳 <b>ОПЛАТА ОТЛОЖЕНА</b>\n\n"
        "✅ <i>Вы можете оплатить аренду позже</i>\n\n"
        "📋 <b>Для оплаты перейдите в:</b>\n"
        "▫️ Личный кабинет → Мои аренды\n"
        "▫️ Выберите текущую аренду\n"
        "▫️ Нажмите \"Оплатить\"\n\n"
        "⚠️ <b>Внимание!</b>\n"
        "⏰ <i>Ваша аренда заканчивается через день</i>\n\n"
        "💡 <i>Не забудьте завершить оплату вовремя</i>",
        parse_mode='HTML',
        reply_markup=keyboard
    )


# Админ панель


@router.callback_query(F.data == 'admin_main')
async def admin_menu(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = await get_user(tg_id)


    if user[-1] == 'moderator':
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👥 Все пользователи", callback_data="view_users")
                ],
                [
                    InlineKeyboardButton(text="⚡ Сделать/Снять admin", callback_data="toggle_admin")
                ],
                [
                    InlineKeyboardButton(text="⛔ Забанить/Разбанить", callback_data="toggle_ban")
                ],

                [
                    InlineKeyboardButton(text='🛵 Посмотреть активные аренды', callback_data='active_rents')
                ],
                [
                    InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")
                ]
            ]
        )
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👥 Все пользователи", callback_data="view_users")
                ],
                [
                    InlineKeyboardButton(text="⛔ Забанить/Разбанить", callback_data="toggle_ban")
                ],
                [
                    InlineKeyboardButton(text='🛵 Посмотреть активные аренды', callback_data='active_rents')
                ],
                [
                    InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")
                ]
            ]
        )

    await callback.message.edit_text(
        "🛠 Добро пожаловать в админ-панель!\n\n"
        "Выберите действие ниже:",
        reply_markup=keyboard
    )

@router.callback_query(F.data == 'view_users')
async def view_users_admin(callback: CallbackQuery):
    users_list = await get_all_users()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for user in users_list:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(text=f"@{user[2]}", callback_data=f'view_user-{user[1]}')
            ]
        )
    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(text='В админ меню', callback_data='admin_main')
        ]
    )

    await callback.message.edit_text('Клиенты', reply_markup=keyboard)


@router.callback_query(F.data.split('-')[0] == 'view_user')
async def view_select_user_admin(callback: CallbackQuery):
    data = callback.data.split('-')[1]
    user = await get_user(data)
    user_card = f"""
    <code>┌──────────────────────────────┐</code>
    <b>  👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ  </b>
    <code>├──────────────────────────────┤</code>
    <b>│</b> 🔹 ID: <code>#{user[0]}</code>
    <b>│</b> 🔹 TG: @{user[2] or 'не указан'}
    <b>│</b> 🔹 TG ID: <code>{user[1]}</code>
    <code>├──────────────────────────────┤</code>
    <b>│</b> 🏍 Текущий скутер: 
    <b>│</b>   ▫️ ID: <b>{user[3] or '—'}</b>
    <b>│</b>   ▫️ Модель: <b>{user[4] or '—'}</b>
    <code>├──────────────────────────────┤</code>
    <b>│</b> 👥 Рефералы: <b>{user[5] or 0}</b>
    <b>│</b> 🚫 Статус: <b>{'🔴 Заблокирован' if user[6] else '🟢 Активен'}</b>
    <code>└──────────────────────────────┘</code>
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 История аренд", callback_data=f"rent_history-{user[1]}")
        ],
        [
            InlineKeyboardButton(text="🎁 Реферальная программа", callback_data="referral_user")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings_user")
        ],
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data='admin_main')
        ]
    ])




    await callback.message.edit_text(text=user_card, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data.split('-')[0] == 'rent_history')
async def check_rent_history(callback: CallbackQuery):
    data = callback.data.split('-')[1]
    rents = await get_data_rents(data)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    user = await get_user(data)

    if rents:
        for rent in rents:
            # Определяем иконку статуса
            status_icon = "🟢" if rent[5] == 'active' else "🔴"  # rent[5] - статус

            keyboard.inline_keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f'{status_icon} Аренда #{rent[0]}',
                        callback_data=f'history_rents-{rent[0]}'
                    )
                ]
            )

        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(text='↩️ Назад', callback_data=f'view_user-{user[1]}')
            ]
        )

        await callback.message.answer(
            f"📋 <b>ИСТОРИЯ АРЕНД</b>\n"
            f"👤 <i>Пользователь: @{user[2] or 'Неизвестный'}</i>\n\n"
            f"🏍️ <b>Список всех поездок:</b>\n"
            f"🟢 — активные\n"
            f"🔴 — завершенные/отмененные",
            parse_mode='HTML',
            reply_markup=keyboard
        )
    else:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(text='↩️ Назад', callback_data=f'view_user-{user[1]}')
            ]
        )

        await callback.message.edit_text(
            f'📭 <b>ИСТОРИЯ АРЕНД ПУСТА</b>\n\n'
            f'✨ <i>У @{user[2] or "Неизвестного"} еще не было аренд скутеров</i>',
            reply_markup=keyboard,
            parse_mode='HTML'
        )


@router.callback_query(F.data.split('-')[0] == 'history_rents')
async def current_rent_user_admin(callback: CallbackQuery):
    data = callback.data.split('-')[1]
    data_rent = await get_current_rent(data)


    start_time = datetime.fromisoformat(data_rent[3]).strftime('%d.%m.%Y %H:%M')
    end_time = datetime.fromisoformat(data_rent[4]).strftime('%d.%m.%Y %H:%M') if data_rent[4] else "Не завершена"


    status_icons = {
        'active': '🟢 Активна',
        'unactive': '✅ Завершена',
        'cancelled': '❌ Отменена',
        'pending': '⏳ Ожидание'
    }
    status = status_icons.get(data_rent[5], data_rent[5])

    rent_card = f"""
<code>┌──────────────────────────────┐</code>
<b>  📋 ДЕТАЛИ АРЕНДЫ #{data_rent[0]}  </b>
<code>├──────────────────────────────┤</code>
<b>│</b> 🆔 ID аренды: <code>#{data_rent[0]}</code>
<b>│</b> 👤 ID пользователя: <code>{data_rent[1]}</code>
<b>│</b> 🏍 ID скутера: <code>{data_rent[2]}</code>
<code>├──────────────────────────────┤</code>
<b>│</b> 🕐 Начало: <b>{start_time}</b>
<b>│</b> 🕔 Окончание: <b>{end_time}</b>
<b>│</b> 📊 Статус: <b>{status}</b>
<code>└──────────────────────────────┛</code>
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data=f"rent_history-{data_rent[1]}")]
        ])

    await callback.message.edit_text(
        text=rent_card,
        parse_mode='HTML',
        reply_markup=keyboard
    )










