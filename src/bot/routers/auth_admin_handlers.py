import asyncio
from decouple import config

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from models import User

from services import ManagerDB

from ..keyboards import ReplyAuthAdminKeyboards
from ..states import AdminStates, AuthAdminStates, UI_UserStates

class AuthAdminHandlersRouter(Router):
    auth_reply_keyboards: ReplyAuthAdminKeyboards = ReplyAuthAdminKeyboards()

    def __init__(self, managerdb: ManagerDB) -> None:
        self.managerdb: ManagerDB = managerdb
        super().__init__()
        self.setup()

    def setup(self):
        self.setup_middlewares()
        self.setup_handlers()
    
    def setup_middlewares(self):
        pass

    def setup_handlers(self):
        @self.message(F.text.in_(['Назад']), StateFilter(AuthAdminStates.Secret_key, AuthAdminStates.Password))
        async def exit_admin_to_main_menu(message: Message, state: FSMContext):
            await state.clear()
            keyboard = self.auth_reply_keyboards.remove
            await message.answer('Вы вышли из админки.', reply_markup=self.auth_reply_keyboards.remove)
        
        @self.message(Command("admin"))
        async def entry_admin_menu_handler(message: Message, state: FSMContext):
            admin = await self.managerdb.get_admin(chat_id=message.chat.id)

            if admin:
                keyboard = self.auth_reply_keyboards.to_admin_menu
                await state.set_state(state=AdminStates.Main_Menu)
                await message.answer(text="Подтвердите вход",
                                 reply_markup=keyboard)
            else:
                await state.set_state(state=AuthAdminStates.Secret_key)
                await secret_key_auth_admin_handler(message=message, state=state)

        @self.message(StateFilter(AuthAdminStates.Secret_key))
        async def secret_key_auth_admin_handler(message: Message, state: FSMContext):
            await state.set_state(state=AuthAdminStates.Password)

            keyboard = self. auth_reply_keyboards.secret_key

            await message.answer(text="Введи секретный ключ:",
                                 reply_markup=keyboard)
        
        @self.message(F.text == config('SECRET_KEY_ADMIN'), StateFilter(AuthAdminStates.Password))
        async def password_auth_admin_handler(message: Message, state: FSMContext):

            await state.set_state(state=AuthAdminStates.InputName)

            keyboard = self. auth_reply_keyboards.password

            await message.answer(text="Введи пароль:",
                                 reply_markup=keyboard)
        

        @self.message(F.text == config('PASSWORD'), StateFilter(AuthAdminStates.InputName))
        async def password_auth_admin_handler(message: Message, state: FSMContext):

            await state.set_state(state=AuthAdminStates.Select_admin_profile)

            keyboard = self. auth_reply_keyboards.password

            await message.answer(text="Придумай свое имя для профиля админа. Оно будет видно пользователям и другим админам:",
                                 reply_markup=keyboard)

        @self.message(StateFilter(AuthAdminStates.Select_admin_profile))
        async def main_menu_handler(message: Message, state: FSMContext):
            await state.set_state(state=AdminStates.Main_Menu)
            admin = await self.managerdb.create_admin(data=message, name=message.text)

            keyboard = self.auth_reply_keyboards.to_admin_menu

            await message.answer(
                f"Вы ({admin.name}) создали учетную запись админа, больше писать ключ и пароль не потребуется.\n\nМожете перейти в <b>Админ-панель</b>.",
                reply_markup=keyboard)