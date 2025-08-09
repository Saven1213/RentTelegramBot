

from aiogram import Router, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram import Bot



from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext



from datetime import timedelta, datetime

from pydantic.v1.typing import test_type

from bot.db.crud.bike import get_bike_by_type, get_bike_by_id
from bot.db.crud.user import get_user, add_user



router = Router()

@router.message(CommandStart())
async def start_command(message: Message):


    tg_id = message.from_user.id
    username = message.from_user.username
    user = await get_user(tg_id)

    if user is None:
        await add_user(tg_id, username)
    try:
        if user[3] is None:
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
                    InlineKeyboardButton(text='Пробная функция оплаты', callback_data='test_payment')
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
    except IndexError:
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
                InlineKeyboardButton(text='Пробная функция оплаты', callback_data='test_payment')
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
        "⏰ <i>Режим работы: пн-пт, 8:00-20:00</i>\n"
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

    print(user, ' посмотрел функцию аренду скутера (1)')

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='Dio', callback_data='view_scooter-dio'),
            InlineKeyboardButton(text='Jog', callback_data='view_scooter-jog')
        ],
        [
            InlineKeyboardButton(text='Gear', callback_data='view_scooter-gear')
        ],
        [
            InlineKeyboardButton(text='Назад', callback_data='main')
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

    print(user, ' вернулся в меню')

    tg_id = callback.from_user.id
    username = callback.from_user.username
    user = await get_user(tg_id)

    if user is None:
        await add_user(tg_id, username)

    if user and user[3] is None:
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
                InlineKeyboardButton(text='Пробная функция оплаты', callback_data='test_payment')
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
        "⏰ <i>Режим работы: пн-пт, 8:00-20:00</i>\n"
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

    user = await get_user(tg_id)

    print(user, ' выбирает скутер')

    data = callback.data.split('-')[1]

    bikes = await get_bike_by_type(data)

    if bikes is None:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text='Назад', callback_data='scooter')
            ]
        ])
        await callback.message.edit_text(f'На данный момент {data} нет посмотрите другие варианты!', reply_markup=keyboard)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for bike in bikes:
        keyboard.inline_keyboard.append(
            [
                InlineKeyboardButton(text=f'{bike[2]} #{bike[1]}', callback_data=f'bikerent-{bike[0]}')
            ]
        )
    keyboard.inline_keyboard.append(
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data='scooter')
        ]
    )
    await callback.message.edit_text('Скутеры на выбор: ', reply_markup=keyboard)


@router.callback_query(F.data.split('-')[0] == 'bikerent')
async def bike_number(callback: CallbackQuery):
    tg_id = callback.from_user.id

    user = await get_user(tg_id)

    print(user, ' находится на карточке мотоцикла')

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
            InlineKeyboardButton(text='🛵 Арендовать', callback_data=f'rent_scooter_but-{bike[0]}'),
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

@router.callback_query(F.data == 'test_payment')
async def test_payment(callback: CallbackQuery, bot: Bot):
    tg_id = callback.from_user.id

    user = await get_user(tg_id)

    print(user, ' протестил функцию оплаты (1)')

    payment_check = """
    <code>┌──────────────────────────────┐</code>
    <b>  � ЧЕК ОПЛАТЫ #A23245674</b>  
    <code>├──────────────────────────────┤</code>
    <b>│ Модель:</b> Jog  
    <b>│ Тариф:</b> Месяц  
    <b>│ Начало:</b> 10.07.2025  
    <b>│ Окончание:</b> 10.08.2025 
    <code>├──────────────────────────────┤</code>
    <b>│ Итого к оплате:</b> <u>12000₽</u>  
    <code>└──────────────────────────────┘</code>

    ⚠️ <i>Ваша аренда завершается через 2 дня!</i>
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Продлить аренду", callback_data=f"extend"),
            InlineKeyboardButton(text="⏳ Оплачу позже", callback_data="pay_later")
        ],
        [
            InlineKeyboardButton(text="❌ Не продлевать", callback_data=f"cancel")
        ],
        [
            InlineKeyboardButton(text="📞 Поддержка", url="t.me/hulkbike_support")
        ]
    ])

    await bot.send_message(
        chat_id=callback.from_user.id,
        text=payment_check,
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.callback_query(F.data == 'extend')
async def extend_bike(callback: CallbackQuery):
    tg_id = callback.from_user.id

    user = await get_user(tg_id)

    print(user, ' продлил оплату ')


    payment_success = f"""
    <code>┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓</code>
    <b>  💳 ОПЛАТА ПРОИЗВЕДЕНА  </b>
    <code>┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫</code>
    <b>│</b> 🔹 Номер заказа: <code>#A23245674</code>
    <b>│</b> 🔹 Сумма: <b>12000₽</b>
    <b>│</b> 🔹 Способ: <i>СБП</i>
    <code>┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫</code>
    <b>│</b> 🏍 Модель: <b>JOG</b>
    <b>│</b> ⏳ Срок аренды: <b>месяц</b>
    <b>│</b> 📍 Локация: <i>Краснодар</i>
    <code>┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛</code>

    <b>✅ Ваш скутер готов к использованию!</b>
    <i>Приятной поездки и соблюдайте ПДД!</i> 🚦
    """

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛵 Мой скутер", callback_data="my_bike"),
            InlineKeyboardButton(text="📊 Профиль", callback_data="profile")
        ],
        [
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
            InlineKeyboardButton(text="📝 Чек", callback_data=f"receipt")
        ],
        [
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")
        ]
    ])
    await callback.message.edit_text(
        text=payment_success,
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.callback_query(F.data == 'pay_later')
async def pay_later(callback: CallbackQuery):
    await callback.message.delete()

    tg_id = callback.from_user.id

    user = await get_user(tg_id)

    print(user, ' нажал напомнить позже про оплату ')

@router.callback_query(F.data == 'cancel')
async def cancel_rent_handler(callback: CallbackQuery):
    tg_id = callback.from_user.id

    user = await get_user(tg_id)

    print(user, ' отменил оплату')

    cancel_message = f"""
<code>┌──────────────────────────────┐</code>
<b>  🚫 АРЕНДА ОТМЕНЕНА  </b>
<code>├──────────────────────────────┤</code>
<b>│</b> 🔹 Скутер: <b>JOG</b>
<b>│</b> 🔹 Номер: <code>#27</code>
<code>├──────────────────────────────┤</code>
<b>│</b> ⏳ Время отмены: <i>{datetime.now().strftime('%d.%m %H:%M')}</i>
<b>│</b> ⏳ Конец аренды: <i>10.08.2025</i>
<code>└──────────────────────────────┛</code>

<i>Скутер доступен для новой аренды.</i>
Спасибо, что пользовались Hulk Bike! 🛵💚
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Оставить отзыв", callback_data="leave_feedback")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")]
    ])

    await callback.message.edit_text(
        text=cancel_message,
        parse_mode="HTML",
        reply_markup=keyboard
    )



