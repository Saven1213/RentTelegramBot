from gettext import textdomain

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message
from datetime import datetime
from aiogram.filters.callback_data import CallbackData

import json

from bot.db.crud.bike import get_bike_by_id
from bot.db.crud.equips import save_equips
from bot.db.crud.mix_conn import rent_bike
from bot.db.crud.payments.change_status import change_status_order
from bot.db.crud.payments.get_order import get_order
from bot.db.crud.photos.map import add_photo
from bot.db.crud.pledge import add_pledge
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

        await callback.message.edit_text(
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

# -------------------------------
# Хэндлер toggle-кнопок
@router.callback_query(ItemToggleCallback.filter())
async def toggle_item_callback(query: CallbackQuery, callback_data: ItemToggleCallback):
    user_id = query.from_user.id
    if user_id not in user_selections:
        user_selections[user_id] = {"шлем": False, "багажник": False, "цепь": False}

    # переключаем состояние
    user_selections[user_id][callback_data.item] = not user_selections[user_id][callback_data.item]

    # обновляем клавиатуру
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
    # сначала редактируем текущее сообщение
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

    # потом удаляем остальные сообщения админов
    for role_name, role_dict in order_msgs.items():
        for chat_id, msg_id in role_dict.items():
            if role_name == 'admin' and int(chat_id) == user_id:
                continue
            try:
                await bot.delete_message(chat_id=int(chat_id), message_id=int(msg_id))
            except Exception as e:
                print(f"Ошибка удаления {chat_id=} {msg_id=}: {e}")

    # уведомление пользователя
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


@router.callback_query(F.data == 'settings_admin')
async def settings(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Добавить/изменить фото карты', callback_data='change_map')
            ]
        ]
    )

    await callback.message.edit_text('Настройки: ', reply_markup=keyboard)


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














