from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup


from bot.db.crud.admin_msgs import save_admin_msg, get_admin_msgs
from bot.db.crud.debts import get_debts
from bot.db.crud.delays import get_delays_user, delete_delays
from bot.db.crud.equips import get_equips_user, delete_equips
from bot.db.crud.mix_conn import rent_bike
from bot.db.crud.names import get_personal_data
from bot.db.crud.payments.add_fail_status import fail_status
from bot.db.crud.payments.create_payment import create_payment
from bot.db.crud.pledge import get_pledge, delete_pledge
from bot.db.crud.rent_data import get_rent_by_user_id, add_new_status
from bot.db.crud.user import get_all_admins, set_null_status_bike
from cardlink import CardLink
from cardlink._types import Bill
from bot.db.crud.bike import get_price, get_bike_by_id, set_user_null, change_status_is_free

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
            [InlineKeyboardButton(text="🛵 Сдать скутер", callback_data=f"return_bike_confirm-{data_rent[0]}")]
        ]
    )



    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )



@router.callback_query(F.data.split('-')[0] == 'return_bike_confirm')
async def return_bike(callback: CallbackQuery, bot: Bot):
    rent_id = callback.data.split('-')[1]
    tg_id = callback.from_user.id
    rent = await get_rent_by_user_id(tg_id)

    debts = await get_debts(tg_id)
    if not debts:
        pd = await get_personal_data(tg_id)


        bike = await get_bike_by_id(rent[2])

        bike_model = bike[2]
        bike_id = bike[1]

        keyboard_admin = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='✅ Подтвердить', callback_data=f'confirm_return_bike-{bike[0]}-{tg_id}'),
                    InlineKeyboardButton(text='❌ Отменить', callback_data=f'cancel_return_bike-{tg_id}')
                ]
            ]
        )

        full_name = f'{pd[2]} {pd[3]}'

        text_admin = (
            f"🛵 <b>НОВАЯ ЗАЯВКА НА ВОЗВРАТ СКУТЕРА</b>\n\n"
            f"👤 <b>Клиент:</b> {full_name}\n"
            f"🆔 <b>ID:</b> <code>{tg_id}</code>\n"
            f"🏍 <b>Скутер:</b> {bike_model} (#{bike_id})\n\n"
            f"✅ <i>Подтвердите возврат при получении скутера</i>"
        )


        admins = await get_all_admins()

        for admin in admins:
            admin_msg = await bot.send_message(chat_id=admin[1], text=text_admin, reply_markup=keyboard_admin, parse_mode='HTML')

            await save_admin_msg(user_id=tg_id, msg_id=admin_msg.message_id, admin_chat_id=admin[1], type_='return_bike')

        user_text = (
            '✅ Заявка отправлена администратору'
        )

        await callback.message.edit_text(text=user_text)

    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Оплатить долги', callback_data='my_debts')
                ]
            ]
        )

        text = (
            "📋 <b>ПРЕДВАРИТЕЛЬНАЯ ПРОВЕРКА</b>\n\n"
            "💡 <i>Обнаружена небольшая задолженность</i>\n\n"
            "✨ <b>Что делать?</b>\n"
            "▫️ Оплатите долг через кнопку ниже\n"
            "▫️ Это займет всего 2 минуты\n"
            "▫️ После оплаты сможете сдать скутер\n\n"
            "🛡️ <b>Не волнуйтесь!</b>\n"
            "▫️ Это стандартная процедура\n"
            "▫️ Мы поможем решить вопрос\n"
            "▫️ Скутер будет ждать вас на базе\n\n"
            "💚 <i>Благодарим за понимание!</i>"
        )

        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML')

@router.callback_query(F.data.split('-')[0] == 'confirm_return_bike')
async def c_return_bike(callback: CallbackQuery, bot: Bot):
    bike_id = callback.data.split('-')[1]



    user_id = callback.data.split('-')[2]

    admin_msgs = await get_admin_msgs(user_id=int(user_id))

    for admin_chat_id, msg_id, type_ in admin_msgs:
        if type_ == 'return_bike':
            try:
                await bot.delete_message(chat_id=admin_chat_id, message_id=msg_id)
            except TelegramBadRequest:
                pass

    equips = await get_equips_user(user_id)

    available_equip_lst = []
    try:
        for i, equip in enumerate(equips):
            equip_str = str(equip) if equip is not None else '0'
            match (i, equip_str):
                case (2, '1'):
                    available_equip_lst.append("шлем")
                case (3, '1'):
                    available_equip_lst.append("цепь")
                case (4, '1'):
                    available_equip_lst.append("термокороб")
                case (5, '1'):
                    available_equip_lst.append("багажник")
                case (6, '1'):
                    available_equip_lst.append("резинка")
                case (7, '1'):
                    available_equip_lst.append("держатель")
                case (8, '1'):
                    available_equip_lst.append("зарядка")
                case (0, '1') | (1, '1'):
                    continue
                case (_, '1'):
                    available_equip_lst.append(f"Экипировка #{i + 1}")
                case (_, '0'):
                    continue
    except TypeError:
        available_equip_lst = []


    text = (
        "🛡️ <b>ЭКИПИРОВКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        "📋 <b>Должен вернуть:</b>\n"
    )

    if available_equip_lst:
        for item in available_equip_lst:
            text += f"▫️ {item.capitalize()}\n"
    else:
        text += "▫️ Экипировка не выдавалась\n\n"

    text += (
        "\n✅ <b>Проверьте при приемке:</b>\n"
        "▫️ Состояние экипировки\n"
        "▫️ Комплектность\n"
        "▫️ Отсутствие повреждений\n\n"

    )

    delays = await get_delays_user(user_id)

    if delays:
        text += (
            '❗️❗️❗️ <b>ПРОСРОЧКА ПОЛЬЗОВАТЕЛЯ</b> ❗️❗️❗️\n'
            f'  Сумма: {delays[4]}'
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Все проверил', callback_data=f'check_pledge-{bike_id}-{user_id}'),
                InlineKeyboardButton(text='❌ Отклонить сдачу', callback_data=f'cancel_return_bike-{user_id}')
            ]
        ]
    )


    await callback.message.answer(text=text, reply_markup=keyboard, parse_mode='HTML')


@router.callback_query(F.data.split('-')[0] == 'check_pledge')
async def check_pledge(callback: CallbackQuery):
    bike_id = callback.data.split('-')[1]
    user_id = callback.data.split('-')[2]

    pledge = await get_pledge(int(user_id))

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить",
                                  callback_data=f'success_equip-{bike_id}-{user_id}')]
        ]
    )

    await delete_equips(user_id)

    if pledge:
        text = (
            "💰 <b>ЗАЛОГ К ВОЗВРАТУ</b>\n\n"
            
            f"💵 <b>Сумма залога:</b> {int(pledge[3])} ₽\n\n"
            
            "💡 <i>После выдачи нажмите подтвердить</i>"
        )


    else:
        text = (
            "💰 <b>ПРОВЕРКА ЗАЛОГА</b>\n\n"
            "⚠️ <b>Залог не найден</b>\n\n"
            "Нажмите подтвердить"
        )



    await callback.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard
    )




@router.callback_query(F.data.split('-')[0] == 'success_equip')
async def end_rent(callback: CallbackQuery, bot: Bot):
    bike_id = callback.data.split('-')[1]
    user_id = callback.data.split('-')[2]
    text = (
        "🔧 <b>ФИНАЛЬНЫЙ ОСМОТР</b>\n\n"
        "📋 Проверьте состояние мопеда:\n"
        "▫️ Царапины и повреждения\n"
        "▫️ Исправность оборудования\n"
        "▫️ Документы и ключи\n\n"
    )

    pledge = await get_pledge(int(user_id))

    if pledge:
        await delete_pledge(int(user_id))




    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='✅ Подтвердить возврат', callback_data=f'complete_rent-{user_id}-{bike_id}')
            ]
        ]
    )

    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML')




@router.callback_query(F.data.split('-')[0] == 'complete_rent')
async def complete_rent(callback: CallbackQuery, bot: Bot):
    user_id = callback.data.split('-')[1]

    delays = await get_delays_user(user_id)





    bike_id = callback.data.split('-')[2]

    order_id = f'order-{uuid.uuid4().hex[:8]}-{bike_id}-{user_id}'



    if delays:
        description = f'Оплата просрочки на {delays[4]} р'
        await delete_delays(tg_id=user_id)
        await create_payment(tg_id=user_id, order_id=order_id, id_='hands', price=delays[4], time=0, message_id='none', description=description, status='success')

    await add_new_status(user_id=int(user_id), status='unactive')

    user_text = (
        "🏁 <b>АРЕНДА ЗАВЕРШЕНА</b>\n\n"
        "✅ <i>Скутер успешно возвращен</i>\n\n"
        "💚 <b>Спасибо за аренду!</b>\n"
        "▫️ Ждем вас снова в Халк Байк\n\n"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")]
        ]
    )

    pd = await get_personal_data(user_id)
    full_name = f'{pd[2]} {pd[3]}'
    bike = await get_bike_by_id(bike_id)
    admin_text = (
        "📋 <b>АРЕНДА ЗАВЕРШЕНА</b>\n\n"
        f"👤 <b>Пользователь:</b> {full_name}\n"
        f"🏍 <b>Скутер:</b> {bike[2]} #{bike[1]}\n\n"
    )


    await set_user_null(bike_id)

    await callback.message.edit_text(
        text=admin_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

    await change_status_is_free(bike_id)

    await bot.send_message(chat_id=user_id, text=user_text, reply_markup=keyboard, parse_mode='HTML')

    await set_null_status_bike(user_id)



@router.callback_query(F.data.split('-')[0] == 'cancel_return_bike')
async def cancel_return_bike(
        callback: CallbackQuery,
        bot: Bot
):
    user_id = callback.data.split('-')[1]

    admin_msgs = await get_admin_msgs(user_id=int(user_id))

    for admin_chat_id, msg_id, type_ in admin_msgs:
        if type_ == 'return_bike':
            try:
                await bot.delete_message(chat_id=admin_chat_id, message_id=msg_id)
            except TelegramBadRequest:
                pass

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='🏠 В главное меню', callback_data='main')
            ]
        ]
    )


    await bot.send_message(chat_id=user_id, text='❌ Админ отклонил заявку', reply_markup=keyboard)









