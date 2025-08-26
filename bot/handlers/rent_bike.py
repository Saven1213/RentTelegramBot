import uuid

import json


from aiogram import Router, F, Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from bot.db.crud.bike import get_bike_by_type, get_bike_by_id, get_price
from bot.db.crud.mix_conn import rent_bike
from bot.db.crud.payments.add_fail_status import fail_status
from bot.db.crud.payments.create_payment import create_payment
from bot.db.crud.user import get_user, get_all_admins

from bot.config import cl
from cardlink._types import Bill



router = Router()


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
    select_period = State()



@router.callback_query(F.data.split('-')[0] == 'write_period')
async def write_period(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split('-')[1]
    await state.update_data(rent_data=data)
    await state.set_state(SelectPeriod.select_period)

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


@router.message(SelectPeriod.select_period)
async def state_period_handler(message: Message, state: FSMContext):
    msg = message.text
    data = await state.get_data()
    rent_data = data.get("rent_data")

    if msg.isdigit():
        days = int(msg)
        if days >= 3:

            callback_data = f"rent_scooter_but-{rent_data}-{days}-none"


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
    none_or_data = callback.data.split('-')[-1]
    if none_or_data == 'none':
        pass
    else:
        await fail_status(order_id=none_or_data)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
    ])

    # user_data, bike_data, rented_now = await rent_bike(tg_id, bike_id, time_)


    # Получаем актуальные цены
    prices = await get_price(bike_id)
    bike_model = await get_bike_by_id(bike_id)
    user = await get_user(tg_id)

    # # Форматирование времени
    # if time_ == 1:
    #     text_time = "1 день"
    # elif time_ < 5:
    #     text_time = f"{time_} дня"
    # else:
    #     text_time = f"{time_} дней"


    if time_ == 1:
        price = prices[-3]
    elif time_ < 7:
        price = prices[-3] * time_
    elif time_ < 30:
        price = prices[-2] * time_
    else:
        price = prices[-1] * time_

    if user[3] == 'null' or user[3] is None:

    # created_invoice: CreatedInvoice = await cl.create_invoice(
    #     amount=price,
    #     order_id=f"order-{tg_id}-{bike_id}-{int(time())}",
    #     currency_in='RUB'
    # )

        keyboard_invoice = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='💳 Оплатить', callback_data=f'payment_rent-{bike_id}-{price}-{time_}'), InlineKeyboardButton(text='💸 Оплатить в руки', callback_data=f'payment_to_hands-{bike_id}-{price}-{time_}')],
            [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]
        ])

        await callback.message.edit_text(
            f"🎉 Отличный выбор!\n\n"
            f"🚴 Скутер <b>{bike_model[2]} #{bike_model[1]}</b>\n"
            f"💵 Сумма к оплате: <b>{price} руб</b>\n\n"
            f"Для подтверждения аренды нажмите кнопку оплаты ниже 👇",
            reply_markup=keyboard_invoice,
            parse_mode='HTML'
        )
    else:
        await callback.message.edit_text(
            "⚠️ У вас уже есть активная аренда скутера!\n\n"
            "Сначала завершите текущую аренду, а потом сможете взять новый 🚴",
            reply_markup=keyboard
        )

@router.callback_query(F.data.split('-')[0] == 'payment_rent')
async def payment_rent_scoot(callback: CallbackQuery):

    tg_id = callback.from_user.id

    days = callback.data.split('-')[-1]

    price = callback.data.split('-')[2]
    bike_id = callback.data.split('-')[1]
    order_id = f'order_{uuid.uuid4().hex[:8]}_{bike_id}_{tg_id}'

    pledge = 2000




    created_bill: Bill = await cl.create_bill(amount=10, order_id=order_id, currency_in='RUB')
    if int(days) == 1:
        text_time = "1 день"
    elif int(days) < 5:
        text_time = f"{days} дня"
    else:
        text_time = f"{days} дней"
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='💳 Оплатить', url=created_bill.link_page_url)
            ],
            [
                InlineKeyboardButton(text='Назад', callback_data=f'rent_scooter_but-{bike_id}-{days}-{order_id}')
            ]
        ]
    )

    msg = await callback.message.edit_text(text=(
        f"💳 <b>ОПЛАТА АРЕНДЫ</b>\n\n"
        f"📦 Стоимость аренды: <b>{int(price)} ₽</b>\n"
        f"🛡️ Залог: {pledge}<b> ₽</b>\n"
        f"──────────────────\n"
        f"💰 <b>ИТОГО: {int(price) + pledge} ₽</b>\n\n"
    ), reply_markup=keyboard, parse_mode='HTML')

    await create_payment(tg_id, order_id, created_bill.id, price, days, msg.message_id, f'Аренда скутера на {text_time}', pledge=pledge)


@router.callback_query(F.data.split('-')[0] == 'payment_to_hands')
async def to_hands(callback: CallbackQuery, bot: Bot):
    bike_id = callback.data.split('-')[1]
    price = callback.data.split('-')[2]
    tg_id = callback.from_user.id
    admins = await get_all_admins()
    bike = await get_bike_by_id(bike_id)
    bike_type = bike[2]
    user = await get_user(tg_id)
    order_id = f'order_{uuid.uuid4().hex[:8]}_{bike_id}_{tg_id}'
    days = callback.data.split('-')[-1]
    pledge = 2000


    if int(days) == 1:
        text_time = "1 день"
    elif int(days) < 5:
        text_time = f"{days} дня"
    else:
        text_time = f"{days} дней"

    text = (
        f"📢 <b>Новая заявка на аренду</b>\n\n"
        f"👤 Пользователь: <code>{user[2]}</code>\n"
        f"🛵 Скутер: <b>{bike_type}</b> (ID: <code>{bike[1]}</code>)\n"
        f"💵 Сумма аренды: <b>{price} ₽</b>\n\n"
        "✅ Подтвердите или отмените аренду ниже"
    )

    keyboard_admin = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Подтвердить', callback_data=f'confirm_rent_admin-{order_id}-{bike_id}'),
                InlineKeyboardButton(text='Отменить', callback_data=f'cancel_rent_admin-{order_id}')
            ]
        ]
    )








    user_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
            ]
        ]
    )


    msg_user = await callback.message.edit_text(
        text=(
            "✅ Ваша заявка на аренду отправлена администратору!\n"
            "Ожидайте подтверждения."
        ),
        parse_mode="HTML",
        reply_markup=user_keyboard
    )

    messages = {'user': {}, 'admin': {}}

    for admin in admins:
        msg = await bot.send_message(
            admin[1],
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard_admin
        )
        messages['admin'][admin[1]] = msg.message_id
    messages['user'][tg_id] = msg_user.message_id
    messages_json = json.dumps(messages)


    await create_payment(tg_id=tg_id, order_id=order_id, id_='hands', price=price, time=days, message_id=messages_json, description=f'Аренда скутера на {text_time}', pledge=pledge)










