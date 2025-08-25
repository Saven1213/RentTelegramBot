from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup

from bot.db.crud.payments.create_payment import create_payment
from cardlink import CardLink
from cardlink._types import Bill
from bot.db.crud.bike import get_price

from bot.config import cl

import uuid

# from bot.db.crud.user import get_user

router = Router()



@router.callback_query(F.data == 'pay_later')
async def pay_later(callback: CallbackQuery):
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
        "⏰ <i>Ваша аренда заканчивается через день</i>\n\n"
        "💡 <i>Не забудьте завершить оплату вовремя</i>",
        parse_mode='HTML',
        reply_markup=keyboard
    )

@router.callback_query(F.data == 'extend')
async def extend(callback: CallbackQuery, state: FSMContext):

    await state.clear()



    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='📅 3 дня', callback_data=f'f"pay_extend-3"'),
            InlineKeyboardButton(text='📅 7 дней', callback_data=f'f"pay_extend-7')
        ],
        [
            InlineKeyboardButton(text='📅 30 дней', callback_data=f'f"pay_extend-30')
        ],
        [
            InlineKeyboardButton(text='✏️ Выбрать вручную', callback_data=f'write_period')
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

@router.callback_query(F.data.split('-')[0] == 'write_period')
async def write_period(callback: CallbackQuery, state: FSMContext):


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
        await message.answer(
            "❌ Неверный формат ввода.\n\n"
            "Пожалуйста, укажите количество дней цифрой, например: <b>5</b>", parse_mode='HTML'
        )




@router.callback_query(F.data == 'extend_back')
async def extend_back(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Вернуться к оплате", callback_data="extend")],
        [InlineKeyboardButton(text="⏳ Отложить оплату", callback_data="pay_later")]
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

    data = callback.data.split('-')[1]
    tg_id = callback.from_user.id

    user = await get_user(tg_id)
    day, week, month = await get_price(user[4])

    if int(data) < 7:
        price = day
    elif int(data) < 30:
        price = week
    else:
        price = month

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
            [InlineKeyboardButton(text='🔄 Проверить оплату', callback_data=f'check_pay-{created_bill.id}')]
        ]
    )
    msg = await callback.message.answer(
        text=f"💳 Счет для продления на {data} дней\n"
             f"Сумма: {price} RUB\n\n"
             f"Ссылка для оплаты действительна 15 минут",
        reply_markup=keyboard
    )

    await create_payment(tg_id, order_id, created_bill.id, price, data, msg.message_id)

