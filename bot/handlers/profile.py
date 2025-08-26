from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from bot.db.crud.user import get_user

router = Router()


@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery):

    tg_id = callback.from_user.id

    user = await get_user(tg_id)


    if user[3] != 'null' or user[3] is not None:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Мой скутер', callback_data='my_scooter')
                ],
                [
                    InlineKeyboardButton(text='Документы на байк', callback_data='documents')
                ],
                [
                    InlineKeyboardButton(text='Карта границ', callback_data='city_map')
                ],
                [
                    InlineKeyboardButton(text='Экипировка', callback_data='equips'),
                    InlineKeyboardButton(text='Долги', callback_data='depts')
                ],
                [
                    InlineKeyboardButton(text='История моих платежей', callback_data='history_my_payments')
                ],
                [
                    InlineKeyboardButton(text='Назад', callback_data='main')
                ]
            ]
        )
    else:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text='Мой скутер', callback_data='my_scooter')
                ],
                [
                    InlineKeyboardButton(text='Назад', callback_data='main')
                ]
            ]
        )

    await callback.message.edit_text(f'Мой профиль\n\nusername {user[2]}\n\n', reply_markup=keyboard)