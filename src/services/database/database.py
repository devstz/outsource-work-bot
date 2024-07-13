from datetime import datetime

from decouple import config
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from aiogram.fsm.storage.redis import RedisStorage

from models import Admin, Finance, Request, Transaction, User, Work

from .managerdb import ManagerDB


class DataBase:

    def __init__(self, filename: str, name_db: str):
        self.filename = filename
        self.name_db = name_db
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(config('MONGODB_URL'))
        self.storage: RedisStorage = RedisStorage.from_url(config('REDIS_URL'))
        self.db: AsyncIOMotorDatabase = self.client[self.name_db]
        self.manager: ManagerDB = ManagerDB(self.db)
    
    def __getattr__(self, name: str) -> any:
        return self.db[name]
    
    def all_save_data(self) -> None: ...
    
    def ban_users(self) -> None: ...

    def create_user(self, chat_id) -> None:
        pass
