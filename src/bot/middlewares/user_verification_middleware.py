import asyncio
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, TelegramObject

from models import User
from services import ManagerDB

from bot.states import Reg_UserStates, UI_UserStates



class UserVerificationMiddleware(BaseMiddleware):
    def __init__(self, managerdb: ManagerDB) -> None:
        self.managerdb: ManagerDB = managerdb

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        user = await self.managerdb.get_user(chat_id=event.chat.id)
        if user:
                await self.managerdb.update_user_data(chat_id=event.chat.id, update=dict(username=event.chat.username))
        else:
            await data['state'].clear()

        if isinstance(event, Message):
            event: Message

            param = await event.get_args()
            print(param)
            if param:
                if 'with_channel_reg' in param:
                    param = None
                else:
                    data['ref_link'] = param
            
            if event.text == 'Зарегистрироваться' and user.ready_profile == 'not_ready':
                await self.managerdb.update_user_data(chat_id=event.chat.id, update=dict(ready_profile='in_progress'))

            
        data['user'] = user
        
        result = await handler(event, data)
        return result