import asyncio
from contextlib import suppress
from sys import modules
from time import monotonic

from decouple import config

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.middlewares import CheckBanMiddleware, UserVerificationMiddleware
from models import User
from services import ManagerDB

from ..keyboards import AuthInlineUserKeyboards, AuthReplyUserKeyboards, Pagination
from ..states import Reg_UserStates, UI_UserStates


class AuthUserHandlersRouter(Router):
    reply_keyboards: AuthReplyUserKeyboards = AuthReplyUserKeyboards()
    inline_keyboards: AuthInlineUserKeyboards = AuthInlineUserKeyboards()

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

        @self.message(CommandStart())
        async def auth_handler(message: Message, state: FSMContext, user: User, ref_link: str = None):
            if not user or user.ready_profile != 'ready':
                if not user:
                    user = await self.managerdb.create_user(data=message, invited_ref_id=ref_link)


                await state.set_state(state=Reg_UserStates.Gender)
                keyboard = self.reply_keyboards.auth
                await message.answer(
                    text=f"<b>Привет! Тебе нужно пройти регистрацию в боте.</b>",
                    reply_markup=keyboard
                )
            else:
                await state.set_state(state=UI_UserStates.Ready_auth)
                keyboard = self.reply_keyboards.menu_path
                await message.answer(text='Нажмите, чтобы перейти в главное меню:', reply_markup=keyboard)
        
        @self.message(F.text == 'Зарегистрироваться', StateFilter(Reg_UserStates.Gender))
        async def select_gender_handler(message: Message, state: FSMContext):
            await state.set_state(state=Reg_UserStates.Age)
            await message.answer(
                text=f"<b>Выберите пол:</b>",
                reply_markup=self.reply_keyboards.genders
            )
        
        @self.message(F.text.in_(['Мужчина', 'Женщина']), StateFilter(Reg_UserStates.Age))
        async def select_age_handler(message: Message, state: FSMContext):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(gender=message.text))
            await state.set_state(state=Reg_UserStates.First_name)
            await message.answer(
                text=f"<b>Введите возраст:</b>",
                reply_markup=self.reply_keyboards.remove
            )
        
        @self.message(F.text.isdigit(), StateFilter(Reg_UserStates.First_name))
        async def select_first_name_handler(message: Message, state: FSMContext):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(age=int(message.text)))
            await state.set_state(state=Reg_UserStates.Last_name)
            await message.answer(
                text=f"<b>Введите фамилию:</b>",
                reply_markup=self.reply_keyboards.remove
            )
        
        @self.message(F.text.split(' ').len() == 1, StateFilter(Reg_UserStates.Last_name))
        async def select_last_name_handler(message: Message, state: FSMContext):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(first_name=message.text))
            await state.set_state(state=Reg_UserStates.start_Bus_stop_id)
            await message.answer(
                text=f"<b>Введите имя:</b>",
                reply_markup=self.reply_keyboards.remove
            )
        
        @self.message(F.text.split(' ').len() == 1, StateFilter(Reg_UserStates.start_Bus_stop_id))
        async def to_navigation_bus_stop_id_handler(message: Message, state: FSMContext, callback_data: Pagination = None):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(last_name=message.text))
            await state.set_state(state=Reg_UserStates.Bus_stop_id)

            len_list = await self.managerdb.get_const(document_id=config('ID_CONSTS'), key='len_bus_stop_list')
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')

            keyboard, page = self.inline_keyboards.bus_stop_list(
                                                                len_list=len_list,
                                                                bus_stop_list=bus_stop_list
                                                                )

            await message.answer(
                text=f"<b>Выберите остановку:</b>\n\nСтраница 1",
                reply_markup=keyboard
            )
        
        @self.callback_query(Pagination.filter(F.action.in_(['prev', 'next'])), StateFilter(Reg_UserStates.Bus_stop_id))
        async def navigation_bus_stop_id_handler(call: CallbackQuery, state:FSMContext, callback_data: Pagination = None):
            len_list = await self.managerdb.get_const(document_id=config('ID_CONSTS'), key='len_bus_stop_list')
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')

            keyboard, page = self.inline_keyboards.bus_stop_list(page_num=int(callback_data.page),
                                                           action=callback_data.action, 
                                                           len_list=len_list,
                                                           bus_stop_list=bus_stop_list)

            with suppress(TelegramBadRequest):
                await call.message.edit_text(
                    text=f"<b>Выберите остановку:</b>\n\nСтраница {page+1}",
                    reply_markup=keyboard
                )
            await call.answer()

        @self.callback_query(Pagination.filter(F.action == 'select'), StateFilter(Reg_UserStates.Bus_stop_id))
        async def navigation_bus_stop_id_handler(call: CallbackQuery, state:FSMContext, callback_data: Pagination):

            bus_stop_id = int(callback_data.page)
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')
            await self.managerdb.update_user_data(chat_id=call.message.chat.id, update=dict(bus_stop_id=bus_stop_id))
            
            with suppress(TelegramBadRequest):
                await call.message.edit_text(
                    text=f"Вы выбрали остановку - <b>{bus_stop_list[bus_stop_id]}</b>",
                )
            await call.answer()
            
            await state.set_state(Reg_UserStates.Phone)
            await select_phone_handler(message=call.message, state=state)

        @self.message(StateFilter(Reg_UserStates.Phone))
        async def select_phone_handler(message: Message, state: FSMContext):
            await state.set_state(state=Reg_UserStates.Ref)
            await message.answer(
                text=f"<b>Введите номер телефона для вашего СБП(начиная с 7 без +):</b>",
                reply_markup=self.reply_keyboards.remove
            )
        

        @self.message(F.text.len() == 11, F.text.isdigit(), StateFilter(Reg_UserStates.Ref))
        async def ref_handler(message: Message, state: FSMContext):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(phone=message.text))
            user = await self.managerdb.get_user(chat_id=message.chat.id)
            if user.invited_ref_id:
                await state.set_state(state=Reg_UserStates.Finish)
                await finish_auth_handler(message=message, state=state)
            else:
                await state.set_state(state=Reg_UserStates.select_Card_ID)
                await message.answer(
                    text=f"<b>Введите ваш номер карты:</b>",
                    reply_markup=self.reply_keyboards.remove
                )
        

        @self.message(F.text.len() == 16, F.text.isdigit(), StateFilter(Reg_UserStates.select_Card_ID))
        async def ref_handler(message: Message, state: FSMContext):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(card_id=message.text))
            user = await self.managerdb.get_user(chat_id=message.chat.id)
            if user.invited_ref_id:
                await state.set_state(state=Reg_UserStates.Finish)
                await finish_auth_handler(message=message, state=state)
            else:
                await state.set_state(state=Reg_UserStates.select_Ref)
                await message.answer(
                    text=f"<b>Введите реферальный 5-значный код друга, если он есть:</b>",
                    reply_markup=self.reply_keyboards.ref
                )


        @self.message(F.text == 'Пропустить', StateFilter(Reg_UserStates.select_Ref))
        async def pass_select_ref_handler(message: Message, state: FSMContext):
            await state.set_state(state=Reg_UserStates.Finish)
            await finish_auth_handler(message=message, state=state)

        @self.message(F.text.len() == 5, StateFilter(Reg_UserStates.select_Ref))
        async def select_ref_handler(message: Message, state: FSMContext):
            invited_user = await self.managerdb.get_user(ref_id=message.text)
            if not invited_user:
                await message.answer(
                text=f"<b>Код не действителен.</b>",
                reply_markup=self.reply_keyboards.ref
            )
            else:
                await self.managerdb.update_user_data(chat_id=message.chat.id,
                                                      update=dict(invited_ref_id=invited_user.ref_id,
                                                                  invited_user_id=invited_user.chat_id))
                await self.managerdb.add_user_data(chat_id=invited_user.chat_id,
                                                   update=dict(invite_users=int(message.chat.id)))
                
                await message.answer(
                text=f"<b>Вы зарегистрировались по рефералке {invited_user.get_names}</b>",
                reply_markup=self.reply_keyboards.remove
                )

                await state.set_state(state=Reg_UserStates.Finish)
                await finish_auth_handler(message=message, state=state)
        
        @self.message(StateFilter(Reg_UserStates.Finish))
        async def finish_auth_handler(message: Message, state: FSMContext):
            await message.answer(text='Вы прошли регистрацию!', reply_markup=self.reply_keyboards.menu_path)
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(ready_profile='ready'))
            await state.set_state(state=UI_UserStates.Ready_auth)
