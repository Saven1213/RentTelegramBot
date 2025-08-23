from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from bot.db.crud.user import get_user  # импортируйте вашу функцию get_user


class BanMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message | CallbackQuery,
            data: Dict[str, Any]
    ) -> Any:

        user = await get_user(event.from_user.id)

        # Вариант 1: Проверяем на 1 (число)
        if user and user[-2] == 1:
            if isinstance(event, Message):
                await event.answer(
                    text="❌ <b>Доступ запрещен</b>\n\nВаш аккаунт заблокирован в системе.",
                    parse_mode="HTML"
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ Ваш аккаунт заблокирован", show_alert=True)
            return

        return await handler(event, data)