from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup
from pydantic.v1 import NoneStr

from bot.db.crud.payments.add_fail_status import fail_status
from bot.db.crud.payments.create_payment import create_payment
from bot.db.crud.rent_data import get_rent_by_user_id, add_new_status
from cardlink import CardLink
from cardlink._types import Bill
from bot.db.crud.bike import get_price

from bot.config import cl

import uuid

# from bot.db.crud.user import get_user

router = Router()



@router.callback_query(F.data.split('-')[0] == 'pay_later')
async def pay_later(callback: CallbackQuery):

    tg_id = callback.from_user.id

    data = callback.data.split('-')[1]

    if data != 'none':
        await fail_status(data)

    data_rent = await get_rent_by_user_id(tg_id)
    end_time = data_rent[5]

    formated = datetime.fromisoformat(end_time) + timedelta(hours=3)


    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Личный кабинет", callback_data="profile")]
    ])

    await callback.message.edit_text(
        "💳 <b>ОПЛАТА ОТЛОЖЕНА</b>\n\n"
        "✅ <i>Вы можете оплатить аренду позже</i>\n\n"
        "📋 <b>Для оплаты перейдите в:</b>\n"
        "▫️ Личный кабинет → Мой скутер\n"
        "▫️ Выберите текущую аренду\n"
        "▫️ Нажмите \"Оплатить\"\n\n"
        "⚠️ <b>Внимание!</b>\n"
       f"⏰ <i>Ваша аренда заканчивается: </i><b>{str(formated).split('.')[0]}</b>\n\n"
        "💡 <i>Не забудьте завершить оплату вовремя</i>",
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.callback_query(F.data == 'extend')
async def extend(callback: CallbackQuery, state: FSMContext):

    await state.clear()



    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📅 3 дня', callback_data=f'pay_extend-3'),
            InlineKeyboardButton(text='📅 7 дней', callback_data=f'pay_extend-7')
        ],
        [
            InlineKeyboardButton(text='📅 30 дней', callback_data=f'pay_extend-30')
        ],
        [
            InlineKeyboardButton(text='✏️ Выбрать вручную', callback_data=f'write_time')
        ],
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data=f'extend_back')
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

class SelectPeriodExtend(StatesGroup):
    select_period = State()

@router.callback_query(F.data == 'write_time')
async def write_period(callback: CallbackQuery, state: FSMContext):

    # try:
    #     await callback.message.delete()
    # except TelegramBadRequest:
    #     pass


    await state.set_state(SelectPeriodExtend.select_period)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='↩️ Назад', callback_data=f'extend')
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

@router.message(SelectPeriodExtend.select_period)
async def confirm_period(message: Message, state: FSMContext):
    msg = message.text



    if msg.isdigit():

        days = int(msg)

        if days < 36500:
            if days >= 3:

                callback_data = f"pay_extend-{days}"

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text='✅ Подтвердить', callback_data=callback_data)
                    ],
                    [
                        InlineKeyboardButton(text='🔄 Изменить срок аренды', callback_data='extend')
                    ]
                ])

                await message.answer(
                    f"⏳ Вы указали срок аренды: <b>{days} дней</b>.\n\n"
                    f"✅ Проверьте данные и подтвердите аренду, либо измените срок.",
                    reply_markup=keyboard, parse_mode='HTML')

                await state.clear()
            else:
                await message.answer(
                    "⚠️ Минимальный срок аренды — <b>3 дня</b>.\n"
                    "Попробуйте ввести другое количество дней ⬇️", parse_mode='HTML'
                )
        else:
            await message.answer('⛔ Вы не можете арендовать больше чем на 100 лет!')
    else:
        await message.answer(
            "❌ Неверный формат ввода.\n\n"
            "Пожалуйста, укажите количество дней цифрой, например: <b>5</b>", parse_mode='HTML'
        )




@router.callback_query(F.data == 'extend_back')
async def extend_back(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Вернуться к оплате", callback_data="extend")],
        [InlineKeyboardButton(text="⏳ Отложить оплату", callback_data="pay_later-none")]
    ])

    await callback.message.edit_text(
        "📋 <b>ВНИМАНИЕ!</b>\n\n"
        "💡 <i>Если перейдете в главное меню:</i>\n\n"
        "✅ <b>Оплата отложится</b>\n"
        "▫️ Будет доступна в профиле до конца аренды\n\n"
        "⚠️ <b>Если не оплатите до конца аренды:</b>\n"
        "▫️ Аренда автоматически завершится\n"
        "▫️ Необходимо будет вернуть скутер на базу\n\n",
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.callback_query(F.data.split('-')[0] == 'pay_extend')
async def payment(callback: CallbackQuery):
    from bot.db.crud.user import get_user

    try:
        await callback.message.delete()
    except TelegramBadRequest:
        pass

    data = callback.data.split('-')[1]
    tg_id = callback.from_user.id

    user = await get_user(tg_id)
    day, week, month = await get_price(user[3])

    if int(data) < 7:
        price = day * int(data)
    elif int(data) < 30:
        price = week * int(data)
    else:
        price = month * int(data)

    if int(data) == 1:
        text_time = "1 день"
    elif int(data) < 5:
        text_time = f"{data} дня"
    else:
        text_time = f"{data} дней"

    bike_id = user[3]
    order_id = f'order-{uuid.uuid4().hex[:8]}-{bike_id}-{tg_id}'


    created_bill: Bill = await cl.create_bill(
        amount=int(price),
        order_id=order_id,
        currency_in='RUB'
    )




    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='💳 Оплатить', url=created_bill.link_page_url)],
            [InlineKeyboardButton(text='⏳ Отложить оплату', callback_data=f'pay_later-{order_id}')]
        ]
    )
    msg = await callback.message.answer(
        text=f"💳 Счет для продления на {data} дней\n"
             f"Сумма: {price} RUB\n\n"
             f"Ссылка для оплаты действительна 15 минут",
        reply_markup=keyboard
    )

    await create_payment(tg_id, order_id, created_bill.id, price, data, msg.message_id, f'Продление аренды на {text_time}!')

@router.callback_query(F.data == 'cancel_pay_rent')
async def cancel(callback: CallbackQuery):
    tg_id = callback.from_user.id

    data_rent = await get_rent_by_user_id(tg_id)
    end_time = data_rent[5]

    formated = str(datetime.fromisoformat(end_time) + timedelta(hours=3))

    text = (
        f"<code>┌────────────────────────┐</code>\n"
        f"<b>  🏁 АРЕНДА ЗАВЕРШЕНА  </b>\n"
        f"<code>├────────────────────────┤</code>\n"
        f"<b>│</b> ⏰ <b>Сдать до:</b> {formated.split('.')[0]}\n"
        f"<b>│</b> 📍 <b>Адрес:</b> Краснодар\n"
        f"<b>│</b> ▫️ ул. Корницкого, 47\n"
        f"<code>└────────────────────────┛</code>\n\n"
        f"📋 <b>Памятка:</b>\n"
        f"▫️ <b>Личный кабинет</b> - вернуться в профиль\n"
        f"▫️ <b>Сдать скутер</b> - нажмите при сдаче на базе\n\n"
        f"💚 <i>Благодарим за выбор <b>Халк байк!</b></i>"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 Где база?", url="https://maps.yandex.ru/?text=Краснодар, Корницкого 47")],
            [InlineKeyboardButton(text="📊 Личный кабинет", callback_data="profile")],
            [InlineKeyboardButton(text="🛵 Сдать скутер", callback_data="return_bike_confirm")]
        ]
    )



    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )
    # ИСПРАВИТЬ ТУТ ЧТО ТО НЕ ТАК
    # if data_rent[6] != 'end_soon':
    #     await add_new_status(data_rent[0], 'end_soon')



