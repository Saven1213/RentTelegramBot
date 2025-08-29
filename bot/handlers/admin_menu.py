
import asyncio
import aiosqlite
from typing import Union
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from datetime import datetime
from aiogram.filters.callback_data import CallbackData

from bot.db.crud.config import DB_PATH

import json

from bot.db.crud.bike import get_bike_by_id
from bot.db.crud.debts import get_debts, add_debt, remove_debt
from bot.db.crud.equips import save_equips, get_equips_user
from bot.db.crud.mix_conn import rent_bike
from bot.db.crud.names import get_personal_data
from bot.db.crud.payments.add_fail_status import fail_status
from bot.db.crud.payments.change_status import change_status_order
from bot.db.crud.payments.get_order import get_order
from bot.db.crud.photos.map import add_photo
from bot.db.crud.pledge import add_pledge
from bot.db.crud.rent_data import get_data_rents, get_current_rent, get_user_by_rent_id
from bot.db.crud.user import get_user, get_all_users, change_role, change_ban_status

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
                    InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings_admin')
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
                    InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings_admin')
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
        pd = await get_personal_data(user[1])
        builder.row(
            InlineKeyboardButton(
                text=f"👤 {pd[2]} {pd[3]}",
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
    pd = await get_personal_data(data)

    full_name = f'{pd[2]} {pd[3]}'
    user_card = f"""
    <code>┌──────────────────────────────┐</code>
    <b>  👤 ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ  </b>
    <code>├──────────────────────────────┤</code>
    <b>│</b> 🔹 ID: <code>#{user[0]}</code>
    <b>│</b> 🔹 Имя: {full_name or 'не указан'}
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
            status_icon = "🟢" if rent[6] == 'active' else "🔴"  # rent[5] - статус

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

        pd = await get_personal_data(data)

        full_name = f'{pd[2]} {pd[3]}'

        await callback.message.edit_text(
            f"📋 <b>ИСТОРИЯ АРЕНД</b>\n"
            f"👤 <i>Пользователь: {full_name or 'Неизвестный'}</i>\n\n"
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


    start_time = datetime.fromisoformat(data_rent[4]).strftime('%d.%m.%Y %H:%M')
    end_time = datetime.fromisoformat(data_rent[5]).strftime('%d.%m.%Y %H:%M') if data_rent[4] else "Не завершена"


    status_icons = {
        'active': '🟢 Активна',
        'unactive': '✅ Завершена',
        'cancelled': '❌ Отменена',
        'pending': '⏳ Ожидание'
    }
    status = status_icons.get(data_rent[6], data_rent[6])

    pd = await get_personal_data(data_rent[1])

    full_name = f'{pd[2]} {pd[3]}'

    bike = await get_bike_by_id(data_rent[2])

    rent_card = f"""
<code>┌──────────────────────────────┐</code>
<b>  📋 ДЕТАЛИ АРЕНДЫ #{data_rent[0]}  </b>
<code>├──────────────────────────────┤</code>
<b>│</b> 👤 Имя пользователя: <code>{full_name}</code>
<b>│</b> 🆔 ID аренды: <code>#{data_rent[0]}</code>
<b>│</b> 🏍 ID скутера: <code>{bike[2]} #{bike[1]}</code>
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




user_selections = {}

# -------------------------------
# CallbackData для toggle-кнопок
class ItemToggleCallback(CallbackData, prefix="toggle"):
    item: str
    order_id: str
    bike_id: str

# -------------------------------
# Генерация клавиатуры с красный/зелёный кружок
def get_items_keyboard(user_id: int, order_id: str, bike_id: str):
    items = ["шлем", "багажник", "цепь", "сумка"]  # новый предмет добавлен

    # получаем текущие выборы или создаём новый словарь
    selections = user_selections.get(user_id, {})

    # добавляем новые предметы, которых ещё нет
    for item in items:
        if item not in selections:
            selections[item] = False

    # сохраняем обновлённый словарь обратно
    user_selections[user_id] = selections

    inline_keyboard = []

    for item in items:
        state = "🟢" if selections[item] else "🔴"
        button = InlineKeyboardButton(
            text=f"{item} {state}",
            callback_data=ItemToggleCallback(item=item, order_id=order_id, bike_id=bike_id).pack()
        )
        inline_keyboard.append([button])

    # формируем строку выбранных предметов
    selected_items = [item for item, state in selections.items() if state]
    code_map = {"шлем": "h", "багажник": "b", "цепь": "c", "сумка": "s"}
    selected_items_str = "".join(code_map[item] for item in selected_items)
    callback_data = f"confirm_equipment-{order_id}-{bike_id}-{selected_items_str}"

    confirm_button = InlineKeyboardButton(
        text="✅ Подтвердить экипировку",
        callback_data=callback_data
    )
    inline_keyboard.append([confirm_button])
    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
    return keyboard


@router.callback_query(F.data.split('-')[0] == 'confirm_rent_admin')
async def confirm_but_rent(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    parts = callback.data.split('-')
    order_id = parts[1]
    bike_id = parts[2]

    # создаём словарь для хранения выбора экипировки
    user_selections[user_id] = {"шлем": False, "багажник": False, "цепь": False, "сумка": False}

    # показываем toggle-клавиатуру экипировки
    await callback.message.edit_text(
        f"Выберите экипировку:",
        reply_markup=get_items_keyboard(user_id, order_id, bike_id)
    )


@router.callback_query(ItemToggleCallback.filter())
async def toggle_item_callback(query: CallbackQuery, callback_data: ItemToggleCallback):
    user_id = query.from_user.id
    if user_id not in user_selections:
        user_selections[user_id] = {"шлем": False, "багажник": False, "цепь": False}


    user_selections[user_id][callback_data.item] = not user_selections[user_id][callback_data.item]


    await query.message.edit_reply_markup(
        reply_markup=get_items_keyboard(user_id, callback_data.order_id, callback_data.bike_id)
    )
    await query.answer()


@router.callback_query(F.data.split('-')[0] == 'confirm_equipment')
async def confirm_but_rent(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    parts = callback.data.split('-')
    order_id = parts[1]
    bike_id = parts[2]

    order = await get_order(order_id)

    selected_codes = parts[3] if len(parts) > 3 else ""
    code_to_item = {"h": "шлем", "b": "багажник", "c": "цепь", "s": "сумка"}
    selected_items = [code_to_item[c] for c in selected_codes if c in code_to_item]

    helmet = 'шлем' in selected_items
    chain = 'цепь' in selected_items
    box = 'сумка' in selected_items
    trunk = 'багажник' in selected_items

    await save_equips(order[1], helmet, chain, box, trunk)
    await change_status_order(order_id, 'success')

    order = await get_order(order_id)
    order_msgs_json = order[-3]
    order_msgs = json.loads(order_msgs_json)

    admin_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")]]
    )
    user_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="main"),
                          InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]]
    )
    pledge = 2000

    try:
        await callback.message.edit_text(
            text=(
                "✅ Подтверждено\n\n"
                f"▫️ Аренда: {int(order[4])} ₽\n"
                f"▫️ Залог: {pledge} ₽\n"
                f"▫️ Итого: {int(order[4] + pledge)} ₽\n"
                f"▫️ Экип: {', '.join(selected_items) if selected_items else 'нет'}"
            ),
            parse_mode='HTML', reply_markup=admin_keyboard
        )
    except Exception:
        pass


    for role_name, role_dict in order_msgs.items():
        for chat_id, msg_id in role_dict.items():
            if role_name == 'admin' and int(chat_id) == user_id:
                continue
            try:
                await bot.delete_message(chat_id=int(chat_id), message_id=int(msg_id))
            except Exception as e:
                print(f"Ошибка удаления {chat_id=} {msg_id=}: {e}")


    await bot.send_message(
        chat_id=order[1],
        text=(
            "🎉 <b>Аренда подтверждена!</b>\n\n"
            "Ваш скутер готов к поездке. 🚴\n"
            "Наслаждайтесь свободой и скоростью на дорогах!\n\n"
            "Желаем отличного настроения и безопасной поездки! 🌟"
        ),
        parse_mode="HTML",
        reply_markup=user_keyboard
    )

    await rent_bike(order[1], int(bike_id), order[-2])
    await add_pledge(order[1], pledge, order_id, int(bike_id))

@router.callback_query(F.data.split('-')[0] == 'cancel_rent_admin')
async def cancel_rent_admin(callback: CallbackQuery, bot: Bot):
    data = callback.data.split('-')[1]
    order = await get_order(data)
    msg_dict = json.loads(order[-3])


    for role_name, role_dict in msg_dict.items():
        for chat_id, msg_id in role_dict.items():
            try:
                if role_name == 'admin':
                    await bot.delete_message(chat_id=int(chat_id), message_id=int(msg_id))
                elif role_name == 'user':
                    await bot.delete_message(chat_id=int(chat_id), message_id=int(msg_id))
            except Exception as e:
                print(f"Ошибка удаления {chat_id=} {msg_id=}: {e}")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main")]
        ]
    )


    await bot.send_message(
        chat_id=order[1],
        text="❌ <i>Администратор отменил ваш запрос на аренду</i>\n\n",
        parse_mode='HTML',
        reply_markup=keyboard
    )

    await fail_status(order[2])












@router.callback_query(F.data == 'settings_admin')
async def settings(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='📍 Обновить карту', callback_data='change_map')
            ],
            [
                InlineKeyboardButton(text='🏍️ Управление скутерами', callback_data='settings_bikes')
            ],
            [
                InlineKeyboardButton(text='↩️ Назад в админ-панель', callback_data='admin_main')
            ]
        ]
    )

    await callback.message.edit_text('⚙️ Настройки ⚙️ ', reply_markup=keyboard)


class ChangeMap(StatesGroup):
    change_new_map = State()


def back_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="↩️ Назад", callback_data="settings_admin")]
        ]
    )


@router.callback_query(F.data == 'change_map')
async def change_map(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeMap.change_new_map)

    await callback.answer()

    msg = await callback.message.edit_text(
        "Пришлите фото новой карты:",
        reply_markup=back_kb()
    )

    await state.update_data(msg=msg.message_id)


@router.message(ChangeMap.change_new_map, F.photo)
async def update_map(message: Message, state: FSMContext, bot: Bot):

    tg_id = message.from_user.id

    user = await get_user(tg_id)

    file_id = message.photo[-1].file_id
    msg_id_del = message.message_id

    await add_photo(file_id)
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
                    InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings_admin')
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
                    InlineKeyboardButton(text='⚙️ Настройки', callback_data='settings_admin')
                ],
                [
                    InlineKeyboardButton(text="🏠 Главное меню", callback_data="main")
                ]
            ]
        )


    data = await state.get_data()
    await bot.delete_message(chat_id=tg_id, message_id=data['msg'])

    await bot.send_message(
        chat_id=tg_id,
        text='✅ Фото карты успешно обновлено!'
    )
    await bot.delete_message(chat_id=tg_id, message_id=msg_id_del)

    await bot.send_message(
        chat_id=tg_id,
        text="🛠 Добро пожаловать в админ-панель!\nВыберите действие ниже:",
        reply_markup=keyboard
    )

    await state.clear()


@router.callback_query(F.data.split('-')[0] == 'debts')
async def debts_admin(callback: CallbackQuery):
    user_id = callback.data.split('-')[1]
    user_debts = await get_debts(user_id)


    if user_debts:
        debts_text = "📋 <b>Список долгов:</b>\n\n"
        total_debt = 0

        for debt in user_debts:
            tg_id, amount, description = debt
            debts_text += f"• {description}: <b>{amount} руб.</b>\n"
            total_debt += amount

        debts_text += f"\n💵 <b>Общая сумма долга: {total_debt} руб.</b>"
    else:
        debts_text = "✅ <b>Долгов нет</b>"


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Добавить долг",
                    callback_data=f"add_debt-{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➖ Снять долг",
                    callback_data=f"remove_debt-{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад к пользователю",
                    callback_data=f"view_user-{user_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text=debts_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


class AddDebtStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()


@router.callback_query(F.data.split('-')[0] == 'add_debt')
async def add_debt_start(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = callback.data.split('-')[1]

    await state.set_state(AddDebtStates.waiting_for_amount)
    await state.update_data(
        user_id=user_id,
        bot_messages=[callback.message.message_id]  # Сохраняем message_id первого сообщения
    )


    sent_message = await callback.message.answer(
        text="💸 <b>Добавление долга</b>\n\n"
             "Введите сумму долга (только цифры):",
        parse_mode="HTML"
    )


    data = await state.get_data()
    bot_messages = data.get('bot_messages', [])
    bot_messages.append(sent_message.message_id)
    await state.update_data(bot_messages=bot_messages)

    await callback.answer()


@router.message(AddDebtStates.waiting_for_amount)
async def process_debt_amount(message: Message, state: FSMContext, bot: Bot):

    data = await state.get_data()
    user_messages = data.get('user_messages', [])
    user_messages.append(message.message_id)
    await state.update_data(user_messages=user_messages)

    try:
        amount = int(message.text)
        if amount <= 0:

            sent_message = await message.answer("❌ Сумма должна быть положительным числом. Попробуйте снова:")
            data = await state.get_data()
            bot_messages = data.get('bot_messages', [])
            bot_messages.append(sent_message.message_id)
            await state.update_data(bot_messages=bot_messages)
            return

        await state.update_data(amount=amount)
        await state.set_state(AddDebtStates.waiting_for_description)


        sent_message = await message.answer(
            "📝 Теперь введите описание долга:\n"
            "Например: 'За повреждение скутера'"
        )

        data = await state.get_data()
        bot_messages = data.get('bot_messages', [])
        bot_messages.append(sent_message.message_id)
        await state.update_data(bot_messages=bot_messages)

    except ValueError:

        sent_message = await message.answer("❌ Пожалуйста, введите корректную сумму (только цифры):")
        data = await state.get_data()
        bot_messages = data.get('bot_messages', [])
        bot_messages.append(sent_message.message_id)
        await state.update_data(bot_messages=bot_messages)


@router.message(AddDebtStates.waiting_for_description)
async def process_debt_description(message: Message, state: FSMContext, bot: Bot):

    data = await state.get_data()
    user_messages = data.get('user_messages', [])
    user_messages.append(message.message_id)
    await state.update_data(user_messages=user_messages)

    description = message.text.strip()

    if len(description) < 3:

        sent_message = await message.answer("❌ Описание слишком короткое. Введите более подробное описание:")
        data = await state.get_data()
        bot_messages = data.get('bot_messages', [])
        bot_messages.append(sent_message.message_id)
        await state.update_data(bot_messages=bot_messages)
        return

    data = await state.get_data()
    user_id = data['user_id']
    amount = data['amount']
    bot_messages = data.get('bot_messages', [])
    user_messages = data.get('user_messages', [])


    await add_debt(tg_id=user_id, amount=amount, description=description)


    chat_id = message.chat.id


    for msg_id in bot_messages:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            pass


    for msg_id in user_messages:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения пользователя {msg_id}: {e}")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Вернуться к долгам",
                    callback_data=f"debts-{user_id}"
                )
            ]
        ]
    )

    pd = await get_personal_data(user_id)

    await message.answer(
        f"✅ <b>Долг добавлен!</b>\n\n"
        f"👤 Клиент: {pd[2]} {pd[3]}\n"
        f"💵 Сумма: {amount} руб.\n"
        f"📝 Описание: {description}",
        parse_mode="HTML",
        reply_markup=keyboard
    )

class RemoveDebtStates(StatesGroup):
    waiting_for_debt_choice = State()
    waiting_for_confirmation = State()

@router.callback_query(F.data.split('-')[0] == 'remove_debt')
async def remove_debt_start(callback: CallbackQuery, state: FSMContext):
    user_id = callback.data.split('-')[1]
    user_debts = await get_debts(user_id)

    if not user_debts:
        await callback.answer("❌ У пользователя нет долгов для удаления")
        return

    await state.set_state(RemoveDebtStates.waiting_for_debt_choice)
    await state.update_data(user_id=user_id, debts=user_debts)


    keyboard_buttons = []

    for i, debt in enumerate(user_debts):
        tg_id, amount, description = debt[0], debt[1], debt[2]
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"❌ {description} - {amount} руб.",
                callback_data=f"select_debt-{i}"  # Сохраняем индекс долга
            )
        ])


    keyboard_buttons.append([
        InlineKeyboardButton(
            text="↩️ Назад к долгам",
            callback_data=f"debts-{user_id}"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        text="🗑️ <b>Выберите долг для удаления:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()



@router.callback_query(F.data == 'cancel_add_debt')
async def cancel_add_debt(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = data.get('user_id')
    bot_messages = data.get('bot_messages', [])
    user_messages = data.get('user_messages', [])

    chat_id = callback.message.chat.id


    for msg_id in bot_messages:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения бота {msg_id}: {e}")


    for msg_id in user_messages:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            print(f"Ошибка удаления сообщения пользователя {msg_id}: {e}")

    await state.clear()

    if user_id:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="↩️ Вернуться к долгам",
                        callback_data=f"debts-{user_id}"
                    )
                ]
            ]
        )
        await callback.message.answer("❌ Добавление долга отменено", reply_markup=keyboard)
    else:
        await callback.message.answer("❌ Добавление долга отменено")

    await callback.answer()


@router.callback_query(F.data.split('-')[0] == 'select_debt')
async def select_debt_for_removal(callback: CallbackQuery, state: FSMContext):
    debt_index = int(callback.data.split('-')[1])
    data = await state.get_data()
    user_id = data['user_id']
    debts = data['debts']

    selected_debt = debts[debt_index]
    tg_id, amount, description = selected_debt[0], selected_debt[1], selected_debt[2]

    await state.update_data(selected_debt_index=debt_index)
    await state.set_state(RemoveDebtStates.waiting_for_confirmation)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить",
                    callback_data="confirm_remove_debt"
                ),
                InlineKeyboardButton(
                    text="❌ Нет, отменить",
                    callback_data=f"debts-{user_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text=f"⚠️ <b>Подтвердите удаление долга:</b>\n\n"
             f"📝 <b>Описание:</b> {description}\n"
             f"💵 <b>Сумма:</b> {amount} руб.\n\n"
             f"Вы уверены, что хотите удалить этот долг?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == 'confirm_remove_debt')
async def confirm_remove_debt(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = data['user_id']
    debts = data['debts']
    debt_index = data['selected_debt_index']

    selected_debt = debts[debt_index]
    tg_id, amount, description = selected_debt[0], selected_debt[1], selected_debt[2]


    success = await remove_debt(tg_id, amount, description)

    if success:

        await callback.message.edit_text(
            text=f"✅ <b>Долг удален!</b>\n\n"
                 f"📝 <b>Описание:</b> {description}\n"
                 f"💵 <b>Сумма:</b> {amount} руб.\n\n"
                 f"Долг успешно удален из системы.",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            text="❌ <b>Ошибка при удалении долга</b>\n\n"
                 "Не удалось удалить долг. Попробуйте снова.",
            parse_mode="HTML"
        )


    await asyncio.sleep(2)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Вернуться к долгам",
                    callback_data=f"debts-{user_id}"
                )
            ]
        ]
    )

    await callback.message.edit_text(
        text="Выберите дальнейшее действие:",
        reply_markup=keyboard
    )

    await state.clear()
    await callback.answer()


@router.callback_query(F.data.split('-')[0] == 'equips')
async def equipment_user(callback: CallbackQuery):
    user_id = callback.data.split('-')[1]
    equip_user = await get_equips_user(user_id)
    pd = await get_personal_data(user_id)

    # Форматируем имя
    first_name = pd[2] or ""
    last_name = pd[3] or ""
    full_name = f"{first_name} {last_name}".strip()

    # Собираем доступную экипировку
    available_equips = []
    if equip_user[2]:  # helmet
        available_equips.append("🪖 Шлем")
    if equip_user[3]:  # chain
        available_equips.append("⛓️ Цепь")
    if equip_user[4]:  # box
        available_equips.append("🎒 Сумка/кофр")
    if equip_user[5]:  # trunk
        available_equips.append("🧳 Багажник")

    # Формируем текст
    if available_equips:
        text = (
            f"🛡️ <b>ЭКИПИРОВКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
            f"👤 <b>Владелец:</b> {full_name or 'Не указано'}\n\n"
            f"✅ <b>Доступная экипировка:</b>\n"
            f"{chr(10).join(['▫️ ' + item for item in available_equips])}\n\n"
        )
    else:
        text = (
            f"🛡️ <b>ЭКИПИРОВКА ПОЛЬЗОВАТЕЛЯ</b>\n\n"
            f"👤 <b>Владелец:</b> {full_name or 'Не указано'}\n\n"
            f"🚫 <i>У пользователя нет доступной экипировки</i>\n\n"
            f"💡 <i>Можно выдать через админ-панель</i>"
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f'view_user-{user_id}')]
        ]
    )

    await callback.message.edit_text(
        text=text,
        parse_mode='HTML',
        reply_markup=keyboard
    )


@router.callback_query(F.data == 'toggle_admin')
async def toggle_admin(callback: CallbackQuery):
    try:
        users = await get_all_users()

        keyboard_buttons = []

        for user in users:
            if user[-1] == 'moderator':
                continue

            pd = await get_personal_data(user[1])
            if pd and len(pd) >= 4:
                full_name = f'{pd[2]} {pd[3]}'
            else:
                full_name = f'Пользователь #{user[1]}'

            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"👤 {full_name}",
                    callback_data=f'toggle_current_user-{user[1]}'
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(
                text="↩️ Назад в админ-панель",
                callback_data="admin_main"
            )
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        admin_text = """
🎛️ <b>Управление администраторами</b>

👥 <b>Список пользователей:</b>
Выберите пользователя, чтобы назначить/снять права администратора.

⚠️ <i>Модераторы не отображаются в этом списке</i>
"""

        await callback.message.edit_text(
            text=admin_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в toggle_admin: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке пользователей")


@router.callback_query(F.data.split('-')[0] == 'toggle_current_user')
async def toggle_current_user_admin(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split('-')[1])

        user = await get_user(user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return

        current_role = user[-1]

        pd = await get_personal_data(user_id)
        if pd and len(pd) >= 4:
            full_name = f'{pd[2]} {pd[3]}'
        else:
            full_name = f'Пользователь #{user_id}'

        if current_role == 'user':
            button_text = "🔼 Сделать администратором"
            new_role = 'admin'
            action_text = "назначить администратором"
        else:
            button_text = "🔽 Снять права администратора"
            new_role = 'user'
            action_text = "снять права администратора"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"confirm_toggle-{user_id}-{new_role}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад к списку",
                    callback_data="toggle_admin"
                )
            ]
        ])

        role_icons = {
            'user': '👤 Обычный пользователь',
            'admin': '🛡️ Администратор',
            'moderator': '🎛️ Модератор'
        }
        current_role_text = role_icons.get(current_role, current_role)

        confirm_text = f"""
🎛️ <b>Изменение прав пользователя</b>

👤 <b>Пользователь:</b> {full_name}
📊 <b>Текущая роль:</b> {current_role_text}

⚠️ <b>Вы уверены, что хотите {action_text}?</b>
"""

        await callback.message.edit_text(
            text=confirm_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в toggle_current_user: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.split('-')[0] == 'confirm_toggle')
async def confirm_toggle_admin(callback: CallbackQuery):
    try:
        data_parts = callback.data.split('-')
        user_id = int(data_parts[1])
        new_role = data_parts[2]

        await change_role(user_id)

        user = await get_user(user_id)
        pd = await get_personal_data(user_id)

        if pd and len(pd) >= 4:
            full_name = f'{pd[2]} {pd[3]}'
        else:
            full_name = f'Пользователь #{user_id}'

        role_icons = {
            'user': '👤 Обычный пользователь',
            'admin': '🛡️ Администратор',
            'moderator': '🎛️ Модератор'
        }
        new_role_text = role_icons.get(new_role, new_role)

        result_text = f"""
✅ <b>Права пользователя изменены!</b>

👤 <b>Пользователь:</b> {full_name}
🎛️ <b>Новая роль:</b> {new_role_text}

💡 Изменения применены успешно.
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Вернуться к списку",
                    callback_data="toggle_admin"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В главное меню",
                    callback_data="main"
                )
            ]
        ])

        await callback.message.edit_text(
            text=result_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в confirm_toggle: {e}")
        await callback.answer("❌ Произошла ошибка при изменении прав")


@router.callback_query(F.data == 'toggle_ban')
async def toggle_ban(callback: CallbackQuery):
    try:
        users = await get_all_users()

        keyboard_buttons = []

        for user in users:
            if user[-1] == 'moderator':
                continue
            pd = await get_personal_data(user[1])
            if pd and len(pd) >= 4:
                full_name = f'{pd[2]} {pd[3]}'
            else:
                full_name = f'Пользователь #{user[1]}'

            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"👤 {full_name}",
                    callback_data=f'toggle_ban_user-{user[1]}'
                )
            ])

        keyboard_buttons.append([
            InlineKeyboardButton(
                text="↩️ Назад в админ-панель",
                callback_data="admin_main"
            )
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        ban_text = """
🚫 <b>Управление блокировками</b>

👥 <b>Список пользователей:</b>
Выберите пользователя, чтобы заблокировать/разблокировать.
"""

        await callback.message.edit_text(
            text=ban_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в toggle_ban: {e}")
        await callback.answer("❌ Произошла ошибка при загрузке пользователей")


@router.callback_query(F.data.split('-')[0] == 'toggle_ban_user')
async def toggle_ban_user(callback: CallbackQuery):
    try:
        user_id = int(callback.data.split('-')[1])

        user = await get_user(user_id)
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return

        current_ban_status = user[-2]  # 1 или 0

        pd = await get_personal_data(user_id)
        if pd and len(pd) >= 4:
            full_name = f'{pd[2]} {pd[3]}'
        else:
            full_name = f'Пользователь #{user_id}'

        if current_ban_status == 0:
            button_text = "🔒 Заблокировать"
            new_ban_status = 1
            action_text = "заблокировать"
            current_status_text = "✅ Активный"
        else:
            button_text = "🔓 Разблокировать"
            new_ban_status = 0
            action_text = "разблокировать"
            current_status_text = "🔒 Заблокирован"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"confirm_ban-{user_id}-{new_ban_status}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ Назад в админ-панель",
                    callback_data="admin_main"
                )
            ]
        ])

        confirm_text = f"""
🚫 <b>Изменение статуса блокировки</b>

👤 <b>Пользователь:</b> {full_name}
📊 <b>Текущий статус:</b> {current_status_text}

⚠️ <b>Вы уверены, что хотите {action_text} пользователя?</b>
"""

        await callback.message.edit_text(
            text=confirm_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в toggle_ban_user: {e}")
        await callback.answer("❌ Произошла ошибка")


@router.callback_query(F.data.split('-')[0] == 'confirm_ban')
async def confirm_ban_user(callback: CallbackQuery):
    try:
        data_parts = callback.data.split('-')
        user_id = int(data_parts[1])
        new_ban_status = int(data_parts[2])

        await change_ban_status(user_id)

        user = await get_user(user_id)
        pd = await get_personal_data(user_id)

        if pd and len(pd) >= 4:
            full_name = f'{pd[2]} {pd[3]}'
        else:
            full_name = f'Пользователь #{user_id}'

        if new_ban_status == 1:
            new_status_text = "🔒 Заблокирован"
            action_result = "заблокирован"
        else:
            new_status_text = "✅ Активный"
            action_result = "разблокирован"

        result_text = f"""
✅ <b>Статус блокировки изменен!</b>

👤 <b>Пользователь:</b> {full_name}
🚫 <b>Новый статус:</b> {new_status_text}

💡 Пользователь успешно {action_result}.
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Вернуться к списку",
                    callback_data="toggle_ban"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 В главное меню",
                    callback_data="main"
                )
            ]
        ])

        await callback.message.edit_text(
            text=result_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await callback.answer()

    except Exception as e:
        print(f"Ошибка в confirm_ban: {e}")
        await callback.answer("❌ Произошла ошибка при изменении статуса блокировки")


@router.callback_query(F.data == 'active_rents')
async def active_rents_admin(callback: CallbackQuery, state: FSMContext):
    try:
        async with aiosqlite.connect('rent-bike.db') as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM rent_details WHERE status = 'active'")
            active_rents = await cursor.fetchall()

        if not active_rents:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_main")]
            ])
            await callback.message.edit_text(
                text="📭 <b>Активных аренд нет</b>\n\nНа данный момент нет активных аренд.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return

        await state.update_data(active_rents=active_rents, current_page=0)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Поиск по имени", callback_data="search_rents")],
            [InlineKeyboardButton(text="📋 Список всех аренд", callback_data="show_all_rents")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="admin_main")]
        ])

        await callback.message.edit_text(
            text="🏍 <b>Активные аренды</b>\n\nВыберите действие:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    except Exception as e:
        print(f"Ошибка в active_rents_admin: {e}")
        await callback.answer("❌ Ошибка при загрузке аренд")


@router.callback_query(F.data == 'show_all_rents')
async def show_all_rents(callback: CallbackQuery, state: FSMContext):
    async with aiosqlite.connect('rent-bike.db') as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT * FROM rent_details WHERE status = 'active'")
        all_rents = await cursor.fetchall()

    await state.update_data(
        active_rents=all_rents,
        current_page=0,
        search_query=None,
        is_search=False,
        all_rents=all_rents
    )
    await show_rent_page(callback, state)


@router.callback_query(F.data == 'search_rents')
async def search_rents_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SearchRentStates.waiting_for_name)

    data = await state.get_data()
    if 'all_rents' not in data:
        async with aiosqlite.connect('rent-bike.db') as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM rent_details WHERE status = 'active'")
            all_rents = await cursor.fetchall()
        await state.update_data(all_rents=all_rents)

    await callback.message.edit_text(
        text="🔍 <b>Поиск аренд по имени</b>\n\nВведите имя или фамилию арендатора:",
        parse_mode="HTML"
    )
    await callback.answer()


class SearchRentStates(StatesGroup):
    waiting_for_name = State()


@router.message(SearchRentStates.waiting_for_name)
async def process_search_name(message: Message, state: FSMContext):
    search_query = message.text.strip().lower()

    data = await state.get_data()
    all_rents = data.get('all_rents', [])

    found_rents = []

    for rent in all_rents:
        user_id = rent[1]
        pd = await get_personal_data(user_id)

        if pd and len(pd) >= 4:
            first_name = pd[2].lower() if pd[2] else ""
            last_name = pd[3].lower() if pd[3] else ""
            full_name = f"{first_name} {last_name}"

            if (search_query in first_name or
                    search_query in last_name or
                    search_query in full_name or
                    first_name in search_query or
                    last_name in search_query):
                found_rents.append(rent)

    if found_rents:
        await state.update_data(
            active_rents=found_rents,
            current_page=0,
            search_query=search_query,
            is_search=True
        )
        await show_rent_page(message, state)
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Попробовать снова", callback_data="search_rents")],
            [InlineKeyboardButton(text="↩️ Назад", callback_data="active_rents")]
        ])

        await message.answer(
            text=f"❌ <b>Аренды не найдены</b>\n\nПо запросу \"{message.text}\" активных аренд не найдено.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

    await state.set_state(None)


async def show_rent_page(update: Union[Message, CallbackQuery], state: FSMContext):
    data = await state.get_data()
    active_rents = data.get('active_rents', [])
    current_page = data.get('current_page', 0)
    search_query = data.get('search_query')
    is_search = data.get('is_search', False)

    if not active_rents:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="↩️ В админку", callback_data="admin_main")]
        ])

        if isinstance(update, CallbackQuery):
            await update.message.edit_text(
                text="📭 <b>Аренды не найдены</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await update.answer(
                text="📭 <b>Аренды не найдены</b>",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        return

    rent = active_rents[current_page]
    rent_id, user_id, bike_id, notified, start_time, end_time, status, days, pledge = rent

    pd = await get_personal_data(user_id)
    user_name = f"{pd[2]} {pd[3]}" if pd and len(pd) >= 4 else f"Пользователь #{user_id}"

    bike = await get_bike_by_id(bike_id)
    bike_name = bike[2] if bike else "Неизвестный байк"
    display_bike_id = bike[1] if bike else bike_id

    start_str = datetime.fromisoformat(start_time).strftime('%d.%m.%Y %H:%M')
    end_str = datetime.fromisoformat(end_time).strftime('%d.%m.%Y %H:%M') if end_time else "Не указано"

    search_info = f"🔍 Поиск: \"{search_query}\"\n\n" if is_search and search_query else ""

    rent_card = f"""
{search_info}🏍 <b>АКТИВНАЯ АРЕНДА #{rent_id}</b>

👤 <b>Арендатор:</b> {user_name}
📞 <b>ID пользователя:</b> <code>{user_id}</code>

🚲 <b>Байк:</b> {bike_name}
🔢 <b>Номер байка:</b> <code>{display_bike_id}</code>

🕐 <b>Начало:</b> {start_str}
🕔 <b>Окончание:</b> {end_str}
📅 <b>Дней аренды:</b> {days}
💰 <b>Залог:</b> {pledge} руб.

📊 <b>Статус:</b> 🟢 Активна
"""

    keyboard_buttons = []

    if len(active_rents) > 1:
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data="rent_prev"))

        nav_buttons.append(InlineKeyboardButton(
            text=f"{current_page + 1}/{len(active_rents)}",
            callback_data="rent_page"
        ))

        if current_page < len(active_rents) - 1:
            nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data="rent_next"))

        keyboard_buttons.append(nav_buttons)

    # ДОБАВЛЯЕМ КНОПКУ УПРАВЛЕНИЯ АРЕНДОЙ
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="⚙️ Управление арендой",
            callback_data=f"manage_rent-{rent_id}"
        )
    ])

    nav_buttons = []
    if is_search:
        nav_buttons.append(InlineKeyboardButton(text="🔍 Новый поиск", callback_data="search_rents"))
    keyboard_buttons.append(nav_buttons)

    keyboard_buttons.append([
        InlineKeyboardButton(text="↩️ В админку", callback_data="admin_main")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    if isinstance(update, CallbackQuery):
        await update.message.edit_text(text=rent_card, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.answer(text=rent_card, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == 'rent_prev')
async def rent_previous(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get('current_page', 0)
    if current_page > 0:
        await state.update_data(current_page=current_page - 1)
        await show_rent_page(callback, state)
    await callback.answer()


@router.callback_query(F.data == 'rent_next')
async def rent_next(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    active_rents = data.get('active_rents', [])
    current_page = data.get('current_page', 0)
    if current_page < len(active_rents) - 1:
        await state.update_data(current_page=current_page + 1)
        await show_rent_page(callback, state)
    await callback.answer()


# ДОБАВЛЯЕМ ОБРАБОТЧИК ДЛЯ УПРАВЛЕНИЯ АРЕНДОЙ
@router.callback_query(F.data.split('-')[0] == 'manage_rent')
async def manage_rent_handler(callback: CallbackQuery):
    rent_id = callback.data.split('-')[1]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Завершить аренду", callback_data=f"end_rent_admin-{rent_id}"),
            InlineKeyboardButton(text="❌ Отменить аренду", callback_data=f"cancel_rent_admin-{rent_id}")
        ],
        [
            InlineKeyboardButton(text="📞 Связаться с арендатором", callback_data=f"contact_renter-{rent_id}")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад к арендам", callback_data="active_rents")
        ]
    ])

    await callback.message.edit_text(
        text=f"⚙️ <b>Управление арендой #{rent_id}</b>\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()



@router.callback_query(F.data.split('-')[0] == 'end_rent_admin')
async def end_rent_admin(callback: CallbackQuery):
    rent_id = callback.data.split('-')[1]

    await callback.answer(f"Завершение аренды #{rent_id}")


@router.callback_query(F.data.split('-')[0] == 'cancel_rent_admin')
async def cancel_rent_admin(callback: CallbackQuery):
    rent_id = callback.data.split('-')[1]

    await callback.answer(f"Отмена аренды #{rent_id}")


@router.callback_query(F.data.split('-')[0] == 'contact_renter')
async def contact_renter(callback: CallbackQuery):
    rent_id = callback.data.split('-')[1]

    user_id = await get_user_by_rent_id(rent_id)
    pd = await get_personal_data(user_id)

    first_name = pd[2] if pd and len(pd) > 2 else "Неизвестно"
    last_name = pd[3] if pd and len(pd) > 3 else "Неизвестно"
    number = pd[4] if pd and len(pd) > 4 else "Не указан"

    contact_text = f"""
📞 <b>Контактная информация арендатора</b>

🏍 <b>Аренда:</b> #{rent_id}
👤 <b>Арендатор:</b> {first_name} {last_name}
📱 <b>Телефон:</b> <code>{number}</code>
🆔 <b>ID пользователя:</b> <code>{user_id}</code>

💬 <b>Способы связи:</b>
• Скопируйте номер телефона 📋
• Напишите в Telegram 👇
• Отправьте сообщение через бота 💬
"""
    user = await get_user(tg_id=user_id)
    username = user[2]


    keyboard_buttons = []

    # Кнопка для написания в Telegram
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="✉️ Написать в Telegram",
            url=f"https://t.me/{username}"
        )
    ])

    # Кнопка для отправки сообщения через бота
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="💬 Отправить сообщение",
            callback_data=f"send_message-{user_id}"
        )
    ])

    # Кнопка копирования номера (если номер есть)
    if number != "Не указан":
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="📋 Скопировать номер",
                callback_data=f"copy_number-{number}"
            )
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(
            text="↩️ Назад к управлению",
            callback_data=f"manage_rent-{rent_id}"
        )
    ])

    keyboard_buttons.append([
        InlineKeyboardButton(
            text="🏠 В админ-панель",
            callback_data="admin_main"
        )
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        text=contact_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.split('-')[0] == 'copy_number')
async def copy_number_handler(callback: CallbackQuery):
    number = callback.data.split('-')[1]
    await callback.answer(f"📋 Номер {number} добавлен в буфер обмена", show_alert=False)




@router.callback_query(F.data == 'settings_bikes')
async def sett_bikes(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='🚀 Добавить скутер', callback_data='add_bike'),
            InlineKeyboardButton(text='✏️ Редактировать', callback_data='edit_bike_list')
        ],
        [

            InlineKeyboardButton(text='🏷️ Изменить цены', callback_data='change_prices')
        ],
        [
            InlineKeyboardButton(text='🛑 Вывести из аренды', callback_data='delete_scoot')
        ],
        [
            InlineKeyboardButton(text='↩️ В админку', callback_data='admin_main'),
            InlineKeyboardButton(text='🏠 В главное меню', callback_data='main')
        ]
    ])

    text = """
🏍️ <b>УПРАВЛЕНИЕ ПАРКОМ СКУТЕРОВ</b>

<code>┌─────────────────────────────┐</code>
<b>│  🚀  КОМПЛЕКСНЫЙ КОНТРОЛЬ  │</b>
<code>└─────────────────────────────┘</code>

<code>├───────</code> <b>Основные операции:</b>
<code>│</code>   🚀 <b>Добавить скутер</b> - новый в систему
<code>│</code>   ✏️ <b>Редактировать</b> - изменение данных
<code>│</code>   🏷️ <b>Изменить цены</b> - арендные тарифы
<code>│</code>   🛑 <b>Удалить из базы</b> - Удаление скутера


<code>└───────</code> <i>Выберите нужный раздел ↓</i>
"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    except TelegramBadRequest:
        try:
            await callback.message.delete()
        except:
            pass
        await callback.message.answer(
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
    await callback.answer()


class AddBikeStates(StatesGroup):
    waiting_name = State()
    waiting_number = State()
    waiting_photo = State()
    waiting_oil = State()
    waiting_description = State()
    confirmation = State()


@router.callback_query(F.data == 'add_bike')
async def add_bike_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddBikeStates.waiting_name)
    await state.update_data(messages_to_delete=[callback.message.message_id])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отменить', callback_data='cancel_add_bike')]
    ])

    text = "🚀 <b>ДОБАВЛЕНИЕ НОВОГО СКУТЕРА</b>\n\n📝 Выберите модель скутера:\n• 🔵 <b>dio</b> - Honda Dio\n• 🟢 <b>jog</b> - Yamaha Jog  \n• 🔴 <b>gear</b> - Yamaha Gear\n\n💡 <i>Введите название модели:</i>"

    sent_message = await callback.message.answer(text=text, parse_mode='HTML', reply_markup=keyboard)
    await state.update_data(messages_to_delete=[sent_message.message_id])
    await callback.answer()


@router.message(AddBikeStates.waiting_name)
async def process_bike_name(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])
    messages_to_delete.append(message.message_id)

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except:
            pass

    model = message.text.strip().lower()
    if model not in ['dio', 'jog', 'gear']:
        sent_message = await message.answer("❌ Пожалуйста, выберите из предложенных моделей: dio, jog, gear")
        await state.update_data(messages_to_delete=[sent_message.message_id])
        return

    await state.update_data(model=model)
    await state.set_state(AddBikeStates.waiting_number)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отменить', callback_data='settings_bikes')]
    ])

    sent_message = await message.answer("🔢 <b>Введите номер скутера:</b>\n\n<i>Только цифры, например: 56</i>",
                                        parse_mode='HTML', reply_markup=keyboard)
    await state.update_data(messages_to_delete=[sent_message.message_id])


@router.message(AddBikeStates.waiting_number)
async def process_bike_number(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])
    messages_to_delete.append(message.message_id)

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except:
            pass

    try:
        bike_number = int(message.text.strip())
        if bike_number <= 0:
            sent_message = await message.answer("❌ Номер должен быть положительным числом")
            await state.update_data(messages_to_delete=[sent_message.message_id])
            return
    except ValueError:
        sent_message = await message.answer("❌ Пожалуйста, введите корректный номер (только цифры)")
        await state.update_data(messages_to_delete=[sent_message.message_id])
        return

    await state.update_data(bike_number=bike_number)
    await state.set_state(AddBikeStates.waiting_photo)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отменить', callback_data='settings_bikes')]
    ])

    sent_message = await message.answer(
        "📸 <b>Отправьте фото скутера:</b>\n\n<i>Лучшее качество будет использовано в карточке</i>", parse_mode='HTML',
        reply_markup=keyboard)
    await state.update_data(messages_to_delete=[sent_message.message_id])


@router.message(AddBikeStates.waiting_photo, F.photo)
async def process_bike_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])
    messages_to_delete.append(message.message_id)

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except:
            pass

    best_photo = message.photo[-1]
    await state.update_data(photo_id=best_photo.file_id)

    # Проверяем, откуда пришли - из процесса добавления или из изменения
    current_state = await state.get_state()
    if current_state == AddBikeStates.waiting_photo.state:
        # Продолжаем обычный процесс
        await state.set_state(AddBikeStates.waiting_oil)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='❌ Отменить', callback_data='settings_bikes')]
        ])
        sent_message = await message.answer(
            "🛢️ <b>Введите пробег последней замены масла:</b>\n\n<i>Только цифры, например: 23800</i>",
            parse_mode='HTML',
            reply_markup=keyboard)
        await state.update_data(messages_to_delete=[sent_message.message_id])
    else:
        # Возвращаемся к превью
        data = await state.get_data()
        await show_bike_preview(message, data, state, bot)


@router.message(AddBikeStates.waiting_oil)
async def process_bike_oil(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])
    messages_to_delete.append(message.message_id)

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except:
            pass

    try:
        oil_change = int(message.text.strip())
        if oil_change < 0:
            sent_message = await message.answer("❌ Пробег не может быть отрицательным")
            await state.update_data(messages_to_delete=[sent_message.message_id])
            return
    except ValueError:
        sent_message = await message.answer("❌ Пожалуйста, введите корректный пробег (только цифры)")
        await state.update_data(messages_to_delete=[sent_message.message_id])
        return

    await state.update_data(oil_change=oil_change)
    await state.set_state(AddBikeStates.waiting_description)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отменить', callback_data='settings_bikes')]
    ])

    sent_message = await message.answer(
        "📝 <b>Введите описание скутера:</b>\n\n<i>Максимум 30 символов. Например: 'Крутой черный скутер'</i>",
        parse_mode='HTML', reply_markup=keyboard)
    await state.update_data(messages_to_delete=[sent_message.message_id])


@router.message(AddBikeStates.waiting_description)
async def process_bike_description(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])
    messages_to_delete.append(message.message_id)

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except:
            pass

    description = message.text.strip()
    if len(description) > 30:
        sent_message = await message.answer("❌ Описание слишком длинное. Максимум 30 символов")
        await state.update_data(messages_to_delete=[sent_message.message_id])
        return

    await state.update_data(description=description)

    # Всегда показываем превью после ввода описания
    data = await state.get_data()
    await show_bike_preview(message, data, state, bot)


async def show_bike_preview(message: Message, data: dict, state: FSMContext, bot: Bot):
    model_icons = {'dio': '🔵 DIO', 'jog': '🟢 JOG', 'gear': '🔴 GEAR'}
    model_display = model_icons.get(data['model'], f'🏍 {data["model"].upper()}')

    preview_text = f"🏍️ <b>ПРЕВЬЮ СКУТЕРА</b>\n\n<code>┏━━━━━━━━━━━━━━━━━━━━━━━━┓</code>\n<b>  СКУТЕР #{data['bike_number']}  </b>\n<code>┣━━━━━━━━━━━━━━━━━━━━━━━━┫</code>\n<b>│  🚀 Модель:</b> {model_display}\n<b>│  🔧 Последнее ТО в :</b> {data['oil_change']} км\n<b>│  ✅ Статус:</b> СВОБОДЕН\n<code>┗━━━━━━━━━━━━━━━━━━━━━━━━┛</code>\n\n<blockquote><code>📝 {data['description']}</code></blockquote>\n\n<i>Всё верно?</i>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📸 Изменить фото', callback_data='change_photo'),
         InlineKeyboardButton(text='📝 Изменить описание', callback_data='change_description')],
        [InlineKeyboardButton(text='✅ Подтвердить', callback_data='confirm_bike'),
         InlineKeyboardButton(text='🔄 Начать заново', callback_data='restart_bike')],
        [InlineKeyboardButton(text='❌ Отменить', callback_data='settings_bikes')]
    ])

    # Удаляем предыдущие сообщения
    messages_to_delete = data.get('messages_to_delete', [])
    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except:
            pass

    sent_message = await message.answer_photo(photo=data['photo_id'], caption=preview_text, parse_mode='HTML',
                                              reply_markup=keyboard)
    await state.update_data(messages_to_delete=[sent_message.message_id])
    await state.set_state(AddBikeStates.confirmation)


@router.callback_query(F.data == 'change_photo', AddBikeStates.confirmation)
async def change_bike_photo(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except:
            pass

    # Переходим к ожиданию фото, но с флагом что это изменение
    await state.set_state(AddBikeStates.waiting_photo)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отменить', callback_data='settings_bikes')]
    ])
    sent_message = await callback.message.answer("📸 <b>Отправьте новое фото:</b>", parse_mode='HTML',
                                                 reply_markup=keyboard)
    await state.update_data(messages_to_delete=[sent_message.message_id])
    await callback.answer()


@router.callback_query(F.data == 'change_description', AddBikeStates.confirmation)
async def change_bike_description(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except:
            pass

    # Переходим к ожиданию описания
    await state.set_state(AddBikeStates.waiting_description)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отменить', callback_data='settings_bikes')]
    ])
    sent_message = await callback.message.answer("📝 <b>Введите новое описание:</b>", parse_mode='HTML',
                                                 reply_markup=keyboard)
    await state.update_data(messages_to_delete=[sent_message.message_id])
    await callback.answer()


@router.callback_query(F.data == 'confirm_bike', AddBikeStates.confirmation)
async def confirm_bike_add(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except:
            pass

    # Определяем цены в зависимости от модели
    model = data['model']
    if model == 'dio':
        price_day = 500
        price_week = 400
        price_month = 300
    elif model == 'jog':
        price_day = 600
        price_week = 500
        price_month = 400
    elif model == 'gear':
        price_day = 700
        price_week = 600
        price_month = 500

    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        await cursor.execute("""
            INSERT INTO bikes (bike_id, bike_type, change_oil_at, gas, is_free, price_day, price_week, price_month) 
            VALUES (?, ?, ?, ?, 1, ?, ?, ?)
        """, (data['bike_number'], data['model'], data['oil_change'], 95, price_day, price_week, price_month))

        await cursor.execute("""
            INSERT INTO photos_rent_bikes (bike_id, file_id, description) 
            VALUES (?, ?, ?)
        """, (data['bike_number'], data['photo_id'], data['description']))

        await conn.commit()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='↩️ К настройкам', callback_data='settings_bikes')
            ]
        ]
    )

    sent_message = await callback.message.answer(
        "✅ <b>СКУТЕР УСПЕШНО ДОБАВЛЕН!</b>\n\nСкутер добавлен в систему и готов к аренде.", reply_markup=keyboard, parse_mode='HTML')
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == 'restart_bike', AddBikeStates.confirmation)
async def restart_bike_add(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    messages_to_delete = data.get('messages_to_delete', [])

    for msg_id in messages_to_delete:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except:
            pass

    await state.clear()
    await add_bike_start(callback, state)
    await callback.answer()













