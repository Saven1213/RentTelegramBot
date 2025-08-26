import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.db.crud.mix_conn import get_user_and_data
from bot.db.crud.names import get_personal_data, add_personal_data
from bot.db.crud.user import get_user

router = Router()


@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery):
    tg_id = callback.from_user.id

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
├ 🔹 Username: @{user[2] or 'Не указан'}
├ 🔹 Имя: {name}
└ 🔹 ID: <code>{tg_id}</code>

💎 <i>Управляйте своими арендами и настройками</i>
"""

    await callback.message.edit_text(
        text=profile_text,
        parse_mode='HTML',
        reply_markup=keyboard
    )

class Action(StatesGroup):
    first_name = State()
    last_name = State()
    number = State()


def back_kb():

    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔄 Начать сначала", callback_data="action")]]
    )

@router.callback_query(F.data == "action")
async def action_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Action.first_name)
    await callback.message.edit_text(
        "Давай познакомимся! ✍️\n\nВведите ваше <b>имя</b> (только буквы):",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё\-]+$")  # буквы + дефис

@router.message(Action.first_name)
async def action_fn(message: Message, state: FSMContext):
    msg = (message.text or "").strip()

    if not NAME_RE.fullmatch(msg):
        await message.answer(
            "Имя может содержать только буквы и дефис. Попробуйте ещё раз:",
            reply_markup=back_kb()
        )
        return

    await state.update_data(first_name=msg.capitalize())
    await state.set_state(Action.last_name)
    await message.answer(
        "Отлично! Теперь введите вашу <b>фамилию</b> (только буквы):",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

@router.message(Action.last_name)
async def action_ln(message: Message, state: FSMContext):
    msg = (message.text or "").strip()

    if not NAME_RE.fullmatch(msg):
        await message.answer(
            "Фамилия может содержать только буквы и дефис. Попробуйте ещё раз:",
            reply_markup=back_kb()
        )
        return

    await state.update_data(last_name=msg.capitalize())
    await state.set_state(Action.number)
    await message.answer(
        "Хорошо! Теперь введите ваш <b>номер телефона</b>.\n\n"
        "Примеры: <code>89182223455</code>, <code>+79284569475</code>, <code>+7-918-037-84-28</code>",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

def normalize_phone(raw: str) -> str | None:
    # Убираем все пробелы/скобки/дефисы
    s = (raw or "").strip()
    s = s.replace("(", "").replace(")", "").replace(" ", "").replace("-", "")
    # Допускаем форматы: 8XXXXXXXXXX, +7XXXXXXXXXX, 7XXXXXXXXXX
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

@router.message(Action.number)
async def action_number(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    normalized = normalize_phone(message.text)

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
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Личный кабинет", callback_data="profile")]]
    )
    await message.answer(
        f"🎉 Отлично, {first_name}!\n\n"
        "Анкета успешно заполнена. Теперь вы можете перейти в <b>Личный кабинет</b> и продолжить 🚀",
        parse_mode="HTML",
        reply_markup=kb_done
    )



