from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message


class MessageNumFilter(BaseFilter): 
    def __init__(self):
        ...

    async def __call__(self, message: Message) -> bool:
        if message.isdigit():
            return True
        return False