from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from datetime import datetime

from bot.db.crud.rent_data import get_data_rents, get_current_rent
from bot.db.crud.user import get_user, get_all_users

router = Router()


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

# @router.callback_query(F.data == 'view_users')
# async def view_users_admin(callback: CallbackQuery):
#     users_list = await get_all_users()
#
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[])
#
#     for user in users_list:
#         keyboard.inline_keyboard.append(
#             [
#                 InlineKeyboardButton(text=f"@{user[2]}", callback_data=f'view_user-{user[1]}')
#             ]
#         )
#     keyboard.inline_keyboard.append(
#         [
#             InlineKeyboardButton(text='В админ меню', callback_data='admin_main')
#         ]
#     )
#
#     await callback.message.edit_text('Клиенты', reply_markup=keyboard)

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


@router.callback_query(F.data.startswith('view_users'))
async def view_users_admin(callback: CallbackQuery):
    # Правильно парсим номер страницы
    if callback.data == 'view_users':
        page = 0
    else:
        # Разделяем по нижнему подчеркиванию и берем последнюю часть
        parts = callback.data.split('_')
        page = int(parts[-1])  # Берем последний элемент

    users_list = await get_all_users()
    page_size = 8
    total_pages = max(1, (len(users_list) + page_size - 1) // page_size)

    # Защита от выхода за границы
    page = max(0, min(page, total_pages - 1))

    # Получаем пользователей для текущей страницы
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_users = users_list[start_idx:end_idx]

    builder = InlineKeyboardBuilder()

    # Добавляем кнопки пользователей
    for user in page_users:
        builder.row(
            InlineKeyboardButton(
                text=f"👤 @{user[2]}",
                callback_data=f'view_user-{user[1]}'
            )
        )

    # Добавляем кнопки навигации
    navigation_buttons = []

    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f'view_users_{page - 1}'
            )
        )

    # Индикатор страницы
    navigation_buttons.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data='current_page'
        )
    )

    if page < total_pages - 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f'view_users_{page + 1}'
            )
        )

    if navigation_buttons:
        builder.row(*navigation_buttons)

    # Кнопка возврата в админ меню
    builder.row(
        InlineKeyboardButton(
            text='В админ меню',
            callback_data='admin_main'
        )
    )

    await callback.message.edit_text(
        f'👥 Клиенты (Страница {page + 1}/{total_pages})\n\n'
        f'Всего пользователей: {len(users_list)}',
        reply_markup=builder.as_markup()
    )


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
            InlineKeyboardButton(text='🛡️ Экипировка', callback_data=f'equips-{user[1]}'),
            InlineKeyboardButton(text='💰 Долги', callback_data=f'debts-{user[1]}')
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