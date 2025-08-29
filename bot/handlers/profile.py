import re

import uuid
from datetime import datetime

from typing import Union

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.crud.bike import get_bike_by_id
from bot.db.crud.debts import get_debts
from bot.db.crud.equips import get_equips_user
from bot.db.crud.mix_conn import get_user_and_data
from bot.db.crud.names import get_personal_data, add_personal_data
from bot.db.crud.payments.add_fail_status import fail_status
from bot.db.crud.payments.create_payment import create_payment
from bot.db.crud.payments.payments_user import get_user_payments, get_payment_by_id
from bot.db.crud.photos.map import get_map
from bot.db.crud.user import get_user
from cardlink._types import Bill, BillStatus
from bot.config import cl


router = Router()


@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery, state: FSMContext, bot: Bot):
    tg_id = callback.from_user.id

    data = await state.get_data()
    try:
        if data['msg_for_del']:
            await bot.delete_message(chat_id=tg_id, message_id=data['msg_for_del'])
    except KeyError:
        pass

    await state.clear()



    user, personal_data = await get_user_and_data(tg_id)

    if personal_data:
        name = f"{personal_data[-3]} {personal_data[-2]}" if personal_data[-3] else "Не указано"
    else:
        name = "Не указано"


    keyboard_rows = []

    if user[3] != 'null' and user[3] is not None:

        keyboard_rows.extend([
            [InlineKeyboardButton(text="🏍️ Мой скутер", callback_data="my_scooter")],
            [InlineKeyboardButton(text="🗺️ Карта границ", callback_data="city_map")],
            [
                InlineKeyboardButton(text="🛡️ Экипировка", callback_data="my_equips"),
                InlineKeyboardButton(text="💰 Долги", callback_data="my_debts")
            ],
            [InlineKeyboardButton(text="📊 История платежей", callback_data="history_my_payments")]
        ])

        if personal_data is None:
            keyboard_rows.append([InlineKeyboardButton(text="📝 Анкета", callback_data="action")])

    else:

        keyboard_rows.append([InlineKeyboardButton(text="🏍️ Мой скутер", callback_data="my_scooter")])

        if personal_data is None:
            keyboard_rows.append([InlineKeyboardButton(text="📝 Анкета", callback_data="action")])


    keyboard_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


    profile_text = f"""
👤 <b>МОЙ ПРОФИЛЬ</b>

📋 <b>Основная информация:</b>

├ 🔹 Имя: {name}
└ 🔹 ID: <code>{tg_id}</code>

💎 <i>Управляйте своими арендами и настройками</i>
"""
    try:
        msg_for_del = await callback.message.edit_text(
            text=profile_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except TelegramBadRequest:
        msg_for_del = await callback.message.answer(
            text=profile_text,
            parse_mode='HTML',
            reply_markup=keyboard
        )

    await state.update_data(msg_for_del=msg_for_del.message_id)


class Action(StatesGroup):
    first_name = State()
    last_name = State()
    number = State()


NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё\-]+$")

def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Начать сначала", callback_data="action")]])

def normalize_phone(raw: str) -> str | None:
    s = (raw or "").strip()
    s = s.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
    if s.startswith("+"):
        if s.startswith("+7") and s[1:].isdigit() and len(s) == 12:
            return s
        return None
    if s.isdigit():
        if s.startswith("8") and len(s) == 11:
            return "+7" + s[1:]
        if s.startswith("7") and len(s) == 11:
            return "+7" + s[1:]
    return None




@router.callback_query(lambda c: c.data == "action")
async def action_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Action.first_name)
    msg = await callback.message.edit_text(
        "Давай познакомимся! ✍️\n\nВведите ваше <b>имя</b> (только буквы):",
        parse_mode="HTML"
    )
    await state.update_data(msg1=msg.message_id)


@router.message(Action.first_name)
async def action_fn(message: Message, state: FSMContext, bot: Bot):
    msg_text = (message.text or "").strip()
    if not NAME_RE.fullmatch(msg_text):
        await message.answer(
            "Имя может содержать только буквы и дефис. Попробуйте ещё раз:",
            reply_markup=back_kb()
        )
        return


    data = await state.get_data()
    tg_id = message.from_user.id
    msg_user1 = message.message_id


    await state.set_state(Action.last_name)
    msg2 = await message.answer(
        "Отлично! Теперь введите вашу <b>фамилию</b> (только буквы):",
        parse_mode="HTML",
        reply_markup=back_kb()
    )
    await state.update_data(first_name=msg_text.capitalize(), msg2=msg2.message_id)


    try:
        await bot.delete_message(chat_id=tg_id, message_id=data['msg1'])
    except:
        pass
    try:
        await bot.delete_message(chat_id=tg_id, message_id=msg_user1)
    except:
        pass


@router.message(Action.last_name)
async def action_ln(message: Message, state: FSMContext, bot: Bot):
    msg_text = (message.text or "").strip()
    if not NAME_RE.fullmatch(msg_text):
        await message.answer(
            "Фамилия может содержать только буквы и дефис. Попробуйте ещё раз:",
            reply_markup=back_kb()
        )
        return

    data = await state.get_data()
    tg_id = message.from_user.id
    msg_user2 = message.message_id


    await state.set_state(Action.number)
    msg3 = await message.answer(
        "Хорошо! Теперь введите ваш <b>номер телефона</b>.\n\n"
        "Примеры: <code>89182223455</code>, <code>+79284569475</code>, <code>+7-918-037-84-28</code>",
        parse_mode="HTML",
        reply_markup=back_kb()
    )
    await state.update_data(last_name=msg_text.capitalize(), msg3=msg3.message_id)


    try:
        await bot.delete_message(chat_id=tg_id, message_id=data['msg2'])
    except:
        pass
    try:
        await bot.delete_message(chat_id=tg_id, message_id=msg_user2)
    except:
        pass

# Ввод номера
@router.message(Action.number)
async def action_number(message: Message, state: FSMContext, bot: Bot):
    tg_id = message.from_user.id
    normalized = normalize_phone(message.text)
    msg_user3 = message.message_id


    try:
        await bot.delete_message(chat_id=tg_id, message_id=msg_user3)
    except Exception as e:
        pass

    if not normalized:
        await message.answer(
            "Номер телефона некорректен. Проверьте формат и попробуйте снова.\n\n"
            "Допустимые примеры: <code>89182223455</code>, <code>+79284569475</code>, <code>+7-918-037-84-28</code>",
            parse_mode="HTML",
            reply_markup=back_kb()
        )
        return

    data = await state.get_data()
    first_name = data.get("first_name", "")
    last_name  = data.get("last_name", "")

    await add_personal_data(tg_id, first_name, last_name, normalized)
    await state.clear()

    kb_done = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]]
    )

    await bot.delete_message(chat_id=tg_id, message_id=data['msg3'])
    await message.answer(
        f"🎉 Отлично, {first_name} {last_name}!\n\n"
        "Анкета успешно заполнена. Теперь вы можете перейти в <b>Личный кабинет</b> и продолжить 🚀",
        parse_mode="HTML",
        reply_markup=kb_done
    )

@router.callback_query(F.data == 'city_map')
async def city_map(callback: CallbackQuery, bot: Bot, state: FSMContext):

    tg_id = callback.from_user.id

    msg_del = await state.get_data()

    await bot.delete_message(chat_id=tg_id, message_id=msg_del['msg_for_del'])

    file_id = await get_map()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='↩️ Назад', callback_data=f'profile')
            ]
        ]
    )

    msg_for_del = await callback.message.answer_photo(photo=file_id, caption=(
        "🚧 <b>Границы зоны</b>\n"
        "▫️ За пределами - скутер блокируется"
    ),
    parse_mode='HTML', reply_markup=keyboard)

    await state.clear()

    await state.update_data(msg_for_del=msg_for_del.message_id)


@router.callback_query(F.data == 'my_scooter')
async def my_scooter(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    tg_id = callback.from_user.id
    user = await get_user(tg_id)
    pd = await get_personal_data(tg_id)

    if user[3] is None or user[3] == 'null':

        if pd:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='🛵 Арендовать скутер', callback_data='scooter')],
                [InlineKeyboardButton(text='◀️ Назад', callback_data='profile')]
            ])
            await callback.message.edit_text(
                '🚫 <b>У вас нет активной аренды</b>\n\n'
                '💡 Вы можете арендовать скутер прямо сейчас!',
                parse_mode='HTML',
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='📝 Заполнить анкету', callback_data='action')],
                [InlineKeyboardButton(text='◀️ Назад', callback_data='profile')]
            ])
            await callback.message.edit_text(
                '📋 <b>Анкета не заполнена</b>\n\n'
                '📝 Для аренды скутера необходимо заполнить анкету',
                parse_mode='HTML',
                reply_markup=keyboard
            )

    else:

        bike = await get_bike_by_id(user[3])
        next_oil_change = f'{bike[4] + 3000}  км' if bike[4] else "не указана"
        last_oil_change = f'{bike[4]}  км' or "не указана"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📄 Документы на байк', callback_data='documents')],
            [InlineKeyboardButton(text='◀️ Назад', callback_data='profile')]
        ])

        await callback.message.edit_text(
            f'🏍 <b>ВАШ СКУТЕР</b>\n\n'
            f'<code>┌────────────────────────┐</code>\n'
            f'<b>│</b> 🏍 <b>Модель:</b> {bike[2]}\n'
            f'<b>│</b> 🔧 <b>Замена масла:</b> {last_oil_change}\n'
            f'<b>│</b> ⏰ <b>Следующая замена:</b> {next_oil_change}\n'
            f'<code>└────────────────────────┛</code>\n\n'
            f'💡 <i>Управляйте вашей арендой</i>',
            parse_mode='HTML',
            reply_markup=keyboard
        )


@router.callback_query(F.data == 'my_equips')
async def my_equips(callback: CallbackQuery):
    tg_id = callback.from_user.id
    equips = await get_equips_user(tg_id)


    available_equips = []
    if equips[2]:
        available_equips.append("🪖 Шлем")
    if equips[3]:
        available_equips.append("⛓️ Цепь")
    if equips[4]:
        available_equips.append("🎒 Сумка")
    if equips[5]:
        available_equips.append("🧳 Багажник")


    if available_equips:
        text = (
            "🛡️ <b>ВАША ЭКИПИРОВКА</b>\n\n"
            "✅ <b>Доступно:</b>\n"
            f"{chr(10).join(['▫️ ' + item for item in available_equips])}\n\n"

        )
    else:
        text = (
            "🛡️ <b>ВАША ЭКИПИРОВКА</b>\n\n"
            "🚫 <i>У вас нет доступной экипировки</i>\n\n"
            "💡 <i>Обратитесь к администратору</i>"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="profile")]
        ]
    )

    await callback.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard
    )


@router.callback_query(F.data == 'my_debts')
async def my_debts(callback: CallbackQuery):
    tg_id = callback.from_user.id
    debts = await get_debts(tg_id)

    # Форматируем текст с долгами
    if debts:
        debts_text = "📋 <b>Ваши долги:</b>\n\n"
        total_debt = 0

        for debt in debts:
            tg_id, amount, description = debt[0], debt[1], debt[2]
            debts_text += f"• {description}: <b>{amount} руб.</b>\n"
            total_debt += amount

        debts_text += f"\n💵 <b>Общая сумма долга: {total_debt} руб.</b>"
    else:
        debts_text = "✅ <b>У вас нет долгов</b>"

    # Создаем клавиатуру
    keyboard_buttons = []

    if debts:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="💳 Оплатить долги",
                callback_data="pay_debts-none"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data="main"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        text=debts_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


class PayDebtStates(StatesGroup):
    waiting_for_debt_choice = State()


@router.callback_query(F.data.split('-')[0] == 'pay_debts')
async def pay_debts_start(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    debts = await get_debts(tg_id)
    data = callback.data.split('-')[1]

    if data != 'none':
        await fail_status(data)



    if not debts:
        await callback.answer("❌ У вас нет долгов для оплаты")
        return

    await state.set_state(PayDebtStates.waiting_for_debt_choice)
    await state.update_data(debts=debts)

    # Создаем кнопки для каждого долга
    keyboard_buttons = []

    for i, debt in enumerate(debts):
        tg_id, amount, description = debt[0], debt[1], debt[2]
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"💳 {description} - {amount} руб.",
                callback_data=f"select_debt_to_pay-{i}"  # Сохраняем индекс долга
            )
        ])

    # Добавляем кнопку отмены
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="↩️ Назад к долгам",
            callback_data="my_debts"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        text="💳 <b>Выберите долг для оплаты:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.split('-')[0] == 'select_debt_to_pay')
async def select_debt_to_pay(callback: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()

        # Проверяем, что данные существуют
        if 'debts' not in data:
            await callback.answer("❌ Сессия истекла. Начните заново.")
            await state.clear()
            return

        debt_index = int(callback.data.split('-')[1])
        debts = data['debts']

        # Проверяем, что индекс в пределах диапазона
        if debt_index >= len(debts):
            await callback.answer("❌ Долг не найден")
            return

        selected_debt = debts[debt_index]
        tg_id, amount, description = selected_debt[0], selected_debt[1], selected_debt[2]

        # Здесь будет логика создания платежа
        # Пока просто покажем подтверждение
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💳 Оплатить",
                        callback_data=f"debt_pay-{amount}-{description}"
                    ),
                    InlineKeyboardButton(
                        text="↩️ Назад",
                        callback_data="pay_debts"
                    )
                ]
            ]
        )

        await callback.message.edit_text(
            text=f"💳 <b>Оплата долга:</b>\n\n"
                 f"📝 <b>Описание:</b> {description}\n"
                 f"💵 <b>Сумма:</b> {amount} руб.\n\n"
                 f"Нажмите кнопку ниже для оплаты",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в select_debt_to_pay: {e}")
        await callback.answer("❌ Произошла ошибка")
        await state.clear()


# Обработчик для кнопки "Назад к моим долгам"
@router.callback_query(F.data == 'my_debts')
async def back_to_my_debts(callback: CallbackQuery, state: FSMContext):
    # Очищаем состояние при возврате
    await state.clear()

    tg_id = callback.from_user.id
    debts = await get_debts(tg_id)

    if debts:
        debts_text = "📋 <b>Ваши долги:</b>\n\n"
        total_debt = 0

        for debt in debts:
            tg_id, amount, description = debt[0], debt[1], debt[2]
            debts_text += f"• {description}: <b>{amount} руб.</b>\n"
            total_debt += amount

        debts_text += f"\n💵 <b>Общая сумма долга: {total_debt} руб.</b>"
    else:
        debts_text = "✅ <b>У вас нет долгов</b>"

    keyboard_buttons = []

    if debts:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="💳 Оплатить долги",
                callback_data="pay_debts"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(
            text="↩️ Назад",
            callback_data="main"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        text=debts_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.split('-')[0] == 'debt_pay')
async def debt_pay(callback: CallbackQuery):
    tg_id = callback.from_user.id
    amount = callback.data.split('-')[1]
    description = callback.data.split('-')[2]

    description_for_msg = 'Долг: ' + description
    description_for_func = 'Долг_' + description


    order_id = f'order-{uuid.uuid4().hex[:8]}-debt-{tg_id}'
    create_bill: Bill = await cl.create_bill(amount=int(amount), order_id=order_id, ttl=60 * 15)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить долг", url=create_bill.link_page_url)],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f'pay_debts-{order_id}')]
        ]
    )

    msg = await callback.message.edit_text(
        text=(
            f"<code>┌────────────────────┐</code>\n"
            f"<b>  💰 ОПЛАТА ДОЛГА  </b>\n"
            f"<code>├────────────────────┤</code>\n"
            f"<b>│</b> 📋 {description_for_msg}\n"
            f"<b>│</b> 💵 Сумма: {amount} ₽\n"
            f"<code>├────────────────────┤</code>\n"
            f"<b>│</b> ⏰ 15 минут\n"
            f"<code>└────────────────────┛</code>\n\n"
            f"💳 <i>Нажмите для оплаты</i>"
        ),
        parse_mode='HTML',
        reply_markup=keyboard
    )

    await create_payment(
        tg_id=tg_id,
        order_id=order_id,
        id_=create_bill.id,
        time=0,
        price=int(amount),
        message_id=msg.message_id,
        description=description_for_func,
        status='pending_debt'
    )


@router.callback_query(F.data == 'history_my_payments')
async def history_my_payments(callback: CallbackQuery, state: FSMContext):
    try:
        user_id = callback.from_user.id

        payments = await get_user_payments(user_id)

        if not payments:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад в профиль", callback_data="profile")]
            ])

            await callback.message.edit_text(
                text="📭 <b>У вас пока нет платежей</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return

        await state.update_data(payments=payments, current_page=0)
        await show_payments_page(callback, state)

    except Exception as e:
        print(f"Ошибка в history_my_payments: {e}")
        await callback.answer("❌ Ошибка при загрузке платежей")


async def show_payments_page(update: Union[Message, CallbackQuery], state: FSMContext):
    data = await state.get_data()
    payments = data.get('payments', [])
    current_page = data.get('current_page', 0)

    start_idx = current_page * 5
    end_idx = start_idx + 5
    current_payments = payments[start_idx:end_idx]

    keyboard_buttons = []

    for i, payment in enumerate(current_payments, start=start_idx + 1):
        description = payment[3]

        if description and description.startswith('Аренда скутера'):
            button_text = f"🏍️ Аренда #{i}"
        elif description and description.startswith('Долг_'):
            button_text = f"💰 Долг #{i}"
        else:
            button_text = f"💳 Платеж #{i}"

        keyboard_buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"view_payment-{payment[0]}"
            )
        ])

    total_pages = (len(payments) + 4) // 5
    if total_pages > 1:
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data="payments_prev"))

        nav_buttons.append(InlineKeyboardButton(
            text=f"Страница {current_page + 1}/{total_pages}",
            callback_data="payments_page"
        ))

        if current_page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data="payments_next"))

        keyboard_buttons.append(nav_buttons)

    keyboard_buttons.append([
        InlineKeyboardButton(text="📊 Статистика", callback_data="payments_stats")
    ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="↩️ В профиль", callback_data="profile")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    text = "💳 <b>ВАШИ ПЛАТЕЖИ</b>\n\nВыберите платеж для просмотра подробной информации:"

    if isinstance(update, CallbackQuery):
        await update.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.answer(text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == 'payments_prev')
async def payments_previous(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get('current_page', 0)
    if current_page > 0:
        await state.update_data(current_page=current_page - 1)
        await show_payments_page(callback, state)
    await callback.answer()


@router.callback_query(F.data == 'payments_next')
async def payments_next(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payments = data.get('payments', [])
    current_page = data.get('current_page', 0)
    total_pages = (len(payments) + 4) // 5
    if current_page < total_pages - 1:
        await state.update_data(current_page=current_page + 1)
        await show_payments_page(callback, state)
    await callback.answer()


@router.callback_query(F.data.split('-')[0] == 'view_payment')
async def view_payment_detail(callback: CallbackQuery):
    payment_id = int(callback.data.split('-')[1])

    payment = await get_payment_by_id(payment_id)
    if not payment:
        await callback.answer("❌ Платеж не найден")
        return

    (id, user_id, order_id, bill_id, amount, currency, commission,
     status, created_at, updated_at, description, message_id, days, pledge) = payment

    created_str = datetime.fromisoformat(created_at).strftime('%d.%m.%Y %H:%M')
    updated_str = datetime.fromisoformat(updated_at).strftime('%d.%m.%Y %H:%M') if updated_at else "Не обновлялся"

    if description and description.startswith('Аренда скутера'):
        payment_type = "🏍️ Аренда скутера"
    elif description and description.startswith('Долг_'):
        payment_type = "💰 Погашение долга"
        description = description.replace('_', ': ')
    else:
        payment_type = "💳 Платеж"

    status_icons = {
        'success': '✅ Успешно',
        'pending': '⏳ В обработке',
        'pending_debt': '⏳ В обработке',
        'fail': '❌ Ошибка',
        'expired': '⌛️ Истек'
    }
    status_text = status_icons.get(status, status)

    payment_text = f"""
{payment_type}

💰 <b>Сумма:</b> {int(amount)} {currency}
📝 <b>Описание:</b> {description}
📊 <b>Статус:</b> {status_text}
🕐 <b>Создан:</b> {created_str}

🔢 <b>Детали:</b>
• ID: <code>{id}</code>
• Order ID: <code>{order_id}</code>
"""

    if days and pledge:
        payment_text += f"• Дней аренды: {days}\n• Залог: {pledge} {currency}\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад к списку", callback_data="history_my_payments")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")]
    ])

    await callback.message.edit_text(
        text=payment_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == 'payments_stats')
async def payments_stats(callback: CallbackQuery):
    user_id = callback.from_user.id
    payments = await get_user_payments(user_id)

    if not payments:
        await callback.answer("📭 Нет платежей для статистики")
        return

    total_spent = 0
    successful = 0
    pending = 0
    failed = 0
    expired = 0

    for payment in payments:
        amount, status = payment[4], payment[7]
        if status == 'success':
            total_spent += amount
            successful += 1
        elif status in ['pending', 'pending_debt']:
            pending += 1
        elif status == 'fail':
            failed += 1
        elif status == 'expired':
            expired += 1

    stats_text = f"""
📊 <b>СТАТИСТИКА ПЛАТЕЖЕЙ</b>

💵 <b>Всего потрачено:</b> {total_spent} RUB
📈 <b>Успешных платежей:</b> {successful}
⏳ <b>В обработке:</b> {pending}
❌ <b>Неудачных:</b> {failed}
⌛️ <b>Истекших:</b> {expired}
📋 <b>Всего transactions:</b> {len(payments)}
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Назад к платежам", callback_data="history_my_payments")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")]
    ])

    await callback.message.edit_text(
        text=stats_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()



