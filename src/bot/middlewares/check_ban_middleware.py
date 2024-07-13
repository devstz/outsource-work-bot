import asyncio
from typing import Any, Awaitable, Callable, Dict

from decouple import config

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, TelegramObject

from models import User
from services import ManagerDB


class CheckBanMiddleware(BaseMiddleware):
    def __init__(self, managerdb: ManagerDB) -> None:
        self.managerdb: ManagerDB = managerdb

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        if isinstance(event, Message):
            event: Message
            user = await self.managerdb.get_user(chat_id=event.chat.id)
            if user and user.ban:
                username_contacts = await self.managerdb.get_const(document_id=config('ID_CONTACTS'), key='support_account')
                await event.answer(text=f'Вы забанены. Все вопросы - @{username_contacts}')
                return
        elif isinstance(event, CallbackQuery):
            event: CallbackQuery
            user = await self.managerdb.get_user(chat_id=event.message.chat.id)
            if user and user.ban:
                username_contacts = await self.managerdb.get_const(document_id=config('ID_CONTACTS'), key='support_account')
                await event.edit_text(text=f'Вы забанены. Все вопросы - @{username_contacts}')
                return

        result = await handler(event, data)
        return result