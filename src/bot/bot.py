from asyncio import run as asrun
from datetime import datetime

from decouple import config

import aiogram
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from models import Admin, Finance, Request, Transaction, User, Work
from services import DataBase, ManagerDB, setup_logging

from bot.routers import AdminHandlersRouter, UserHandlersRouter


class GKBot:
    def __init__(self, db: DataBase, token=config('API_TOKEN'), admin_token=config('ADMIN_API_TOKEN')) -> None:
        self.db: DataBase = db
        self.managerdb: ManagerDB = self.db.manager
        self.storage = db.storage
        
        self.token: int = token

        self.routers = [UserHandlersRouter(managerdb=self.managerdb),
                        AdminHandlersRouter(managerdb=self.managerdb)]

        self.bot: Bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.admin_bot: Bot = Bot(token=admin_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        self.dp: Dispatcher = Dispatcher(storage=self.storage)
    
    async def settings_polling(self):
        
        self.dp.include_routers(*self.routers)

        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.dp.start_polling(self.bot)

    def run(self):
        asrun(self.settings_polling())
    
    def close(self):
        self.db.all_save_data()
        asrun(self.dp.storage.close())
        asrun(self.dp.stop_polling())