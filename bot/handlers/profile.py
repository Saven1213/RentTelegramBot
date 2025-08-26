from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.crud.names import get_personal_data
from bot.db.crud.user import get_user

router = Router()


@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery):
    tg_id = callback.from_user.id
    user = await get_user(tg_id)

    personal_data = await get_personal_data(tg_id)

    # Форматируем имя
    name = f"{personal_data[-3]} {user[-2]}" if user[-3] else "Не указано"

    # Создаем базовую клавиатуру
    keyboard_rows = []

    if user[3] != 'null' and user[3] is not None:
        # Пользователь с арендой
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

        if user[-3] is None:
            keyboard_rows.append([InlineKeyboardButton(text="📝 Анкета", callback_data="action")])

    else:
        # Пользователь без аренды
        keyboard_rows.append([InlineKeyboardButton(text="🏍️ Мой скутер", callback_data="my_scooter")])

        if user[-3] is None:
            keyboard_rows.append([InlineKeyboardButton(text="📝 Анкета", callback_data="action")])

    # Добавляем кнопку назад
    keyboard_rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)

    # Красивое сообщение профиля
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