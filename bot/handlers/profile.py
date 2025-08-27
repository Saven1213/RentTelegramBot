import re
from gettext import textdomain

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.crud.bike import get_bike_by_id
from bot.db.crud.mix_conn import get_user_and_data
from bot.db.crud.names import get_personal_data, add_personal_data
from bot.db.crud.photos.map import get_map
from bot.db.crud.user import get_user

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
            [InlineKeyboardButton(text="📄 Документы на байк", callback_data="documents")],
            [InlineKeyboardButton(text="🗺️ Карта границ", callback_data="city_map")],
            [
                InlineKeyboardButton(text="🛡️ Экипировка", callback_data="equips"),
                InlineKeyboardButton(text="💰 Долги", callback_data="depts")
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
            [InlineKeyboardButton(text='📄 Документы', callback_data='documents')],
            [InlineKeyboardButton(text='◀️ Назад', callback_data='profile')]
        ])

        await callback.message.edit_text(
            f'🏍 <b>ВАШ СКУТЕР</b>\n\n'
            f'<code>┌────────────────────────┐</code>\n'
            f'<b>│</b> 🏍 <b>Модель:</b> {bike[2]}\n'
            f'<b>│</b> 🔧 <b>Замена масла:</b> {last_oil_change}\n'
            f'<b>│</b> ⏰ <b>Следующая замена:</b> {next_oil_change[0], next_oil_change[1]}\n'
            f'<code>└────────────────────────┛</code>\n\n'
            f'💡 <i>Управляйте вашей арендой</i>',
            parse_mode='HTML',
            reply_markup=keyboard
        )




