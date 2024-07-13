import asyncio
from contextlib import suppress
from datetime import datetime
from sys import modules

from decouple import config

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.middlewares import CheckBanMiddleware, UserVerificationMiddleware
from models import Transaction, User, Work
from services import ManagerDB

from ..keyboards import InlineUserKeyboards, Pagination, ReplyUserKeyboards
from ..routers.auth_user_handlers import AuthUserHandlersRouter
from ..states import Reg_UserStates, UI_UserStates


class UserHandlersRouter(Router):
    reply_keyboards: ReplyUserKeyboards = ReplyUserKeyboards()
    inline_keyboards: InlineUserKeyboards = InlineUserKeyboards()

    def __init__(self, managerdb: ManagerDB) -> None:
        self.managerdb: ManagerDB = managerdb
        super().__init__()
        self.setup()

    def setup(self):
        self.include_router(AuthUserHandlersRouter(managerdb=self.managerdb))
        self.setup_middlewares()
        self.setup_handlers()

    def setup_middlewares(self):
        self.message.middleware(middleware=UserVerificationMiddleware(managerdb=self.managerdb))
        self.message.middleware(middleware=CheckBanMiddleware(managerdb=self.managerdb))

    def setup_handlers(self):
            
        @self.message(F.text == 'Главное меню', StateFilter(UI_UserStates.Ready_auth))
        async def transition_handler(message: Message, state: FSMContext):
            await state.set_state(state=UI_UserStates.Main_Menu)
            await main_menu_handler(message=message, state=state)
        
        @self.message(F.text.split(' ')[1].split('-')[0] == 'with_channel_reg', CommandStart(), StateFilter(UI_UserStates.Main_Menu))
        async def with_channel_registration_to_work_handler(message: Message, state: FSMContext, user: User):
            work_id = message.text.split(' ')[1].split('-')[1]
            work = await self.managerdb.get_work(work_id=work_id)
            if work.finish_work:
                await message.answer(text='Работа устарела.')
                return
            if not work.set_workers:
                await message.answer(text='Набор закрыт.')
                return
            if message.chat.id not in work.workers:
                await message.answer(text='Вы записались на работу.', reply_markup=self.reply_keyboards.remove)
                await self.managerdb.add_to_work(work_id=work_id, workers=message.chat.id)
            else:
                await message.answer(text='Вы уже записаны.')
            if work.public_message_id:
                work = await self.managerdb.get_work(work_id=work_id)
                bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')

                users = []
                if work.workers:
                    users = await self.managerdb.get_users(user_id_list=work.workers)
                text = work.info_for_channel(users=users, bus_stop_list=bus_stop_list)

                public_channel_id = await self.managerdb.get_const(document_id=config('ID_PUBLIC_CHANNEL_ID'), key='public_channel_id')
                msg = None
                bot_info = await message.bot.get_me()
                url = f"https://t.me/{bot_info.username}?start=with_channel_reg-{work_id}"
                keyboard_for_public_message = self.inline_keyboards.keyboard_for_public_message(work_id=work_id, url=url)

                with suppress(TelegramBadRequest):
                    await message.bot.edit_message_text(
                        chat_id=public_channel_id,
                        message_id=work.public_message_id,
                        text=text,
                        reply_markup=keyboard_for_public_message)
                    
                already_registration_work_id = await self.managerdb.check_registration_user(chat_id=message.chat.id, date=work.date)
                    
                text = work.info_for_user(users=users, bus_stop_list=bus_stop_list)
                inline_keyboard = self.inline_keyboards.work(work=work, chat_id=message.chat.id,
                                                            already_registration_work_id=already_registration_work_id)

                await message.answer(text=text, reply_markup=inline_keyboard)

                    
        
        @self.message(StateFilter(UI_UserStates.Main_Menu), CommandStart())
        async def main_menu_handler(message: Message, state: FSMContext, message_id: int = None):

            await message.answer(
                text='Главное меню:',
                reply_markup=self.reply_keyboards.main_menu)
        
        @self.message(F.text == '📜Правила', StateFilter(UI_UserStates.Main_Menu))
        async def list_rules_handler(message: Message, state: FSMContext):
            list_rules = await self.managerdb.get_const(document_id=config('ID_RULES'), key='rules_for_workers')

            text = '<b>Правила для работников</b>:\n\n'

            for rule in list_rules:
                text += f'<b>{rule["title"]}:</b> {rule["description"]}\n\n'
            
            await message.answer(text=text)
    
        
        @self.message(F.text == 'ℹИнформация', StateFilter(UI_UserStates.Main_Menu))
        async def info_project_handler(message: Message, state: FSMContext):
            text = await self.managerdb.get_const(document_id=config('ID_CONTACTS'), key='info_project')
            link_public_channel = await self.managerdb.get_const(document_id=config('ID_CONTACTS'), key='link_public_channel_for_info')
            link_trans_channel = await self.managerdb.get_const(document_id=config('ID_CONTACTS'), key='link_trans_channel_for_info')
            inline_keyboard = self.inline_keyboards.info_project(link_public_channel=link_public_channel, link_trans_channel=link_trans_channel)
            await message.answer(text=text, reply_markup=inline_keyboard)

        @self.message(F.text == '💼Работа', StateFilter(UI_UserStates.Main_Menu))
        async def job_list_handler(message: Message, state: FSMContext, message_id: int = None):

            text = '<b>Выбери категорию</b>:\n\n'
            inline_keyboard = self.inline_keyboards.job_list
            if message_id:
                with suppress(TelegramBadRequest):
                    await message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await message.answer(text='Открываю список категорий работы...', reply_markup=self.reply_keyboards.remove)
                await message.answer(text=text, reply_markup=inline_keyboard)
            
        @self.callback_query(F.data == 'vacancies', StateFilter(UI_UserStates.Main_Menu))
        async def vacancies_handler(call: CallbackQuery, state: FSMContext):
            
            inline_keyboard = self.inline_keyboards.vacancies

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text='<b>Меню в разработке...</b>', reply_markup=inline_keyboard)
        
        @self.callback_query(F.data == 'active_work_days', StateFilter(UI_UserStates.Main_Menu))
        async def work_days_handler(call: CallbackQuery, state: FSMContext):

            workdays = await self.managerdb.get_active_workdays()
            
            inline_keyboard = self.inline_keyboards.work_days(workdays=workdays)

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text='Актуальные дни работы:', reply_markup=inline_keyboard)
        
        @self.callback_query(Pagination.filter(F.action.in_(['select_day_work'])), StateFilter(UI_UserStates.Main_Menu))
        async def works_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):

            date = int(callback_data.page)
            works = await self.managerdb.get_works(date=date)

            text, inline_keyboard = self.inline_keyboards.works(works=works)

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            
        @self.callback_query(Pagination.filter(F.action.in_(['select_work'])), StateFilter(UI_UserStates.Main_Menu))
        async def work_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):

            work_id = callback_data.page
            work = await self.managerdb.get_work(work_id=work_id)
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')

            already_registration_work_id = await self.managerdb.check_registration_user(chat_id=call.message.chat.id, date=work.date)

            users = []
            if work.workers:
                users = await self.managerdb.get_users(user_id_list=work.workers)
            

            text = work.info_for_user(users=users, bus_stop_list=bus_stop_list)
            inline_keyboard = self.inline_keyboards.work(work=work, chat_id=call.message.chat.id,
                                                         already_registration_work_id=already_registration_work_id)

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(Pagination.filter(F.action.in_(['unregistration_work', 'registration_work'])), StateFilter(UI_UserStates.Main_Menu))
        async def registration_work_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            work_id = callback_data.page
            work = await self.managerdb.get_work(work_id=work_id)

            if work.set_workers and not work.finish_work:
                if callback_data.action == 'registration_work':
                    await self.managerdb.add_to_work(work_id=work_id, workers=call.message.chat.id)
                else:
                    await self.managerdb.del_to_work(work_id=work_id, workers=call.message.chat.id)
                if work.public_message_id:
                    work = await self.managerdb.get_work(work_id=work_id)
                    bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')

                    users = []
                    if work.workers:
                        users = await self.managerdb.get_users(user_id_list=work.workers)

                    text = work.info_for_channel(users=users, bus_stop_list=bus_stop_list)

                    public_channel_id = await self.managerdb.get_const(document_id=config('ID_PUBLIC_CHANNEL_ID'), key='public_channel_id')
                    msg = None
                    bot_info = await call.bot.get_me()
                    url = f"https://t.me/{bot_info.username}?start=with_channel_reg-{work_id}"
                    keyboard_for_public_message = self.inline_keyboards.keyboard_for_public_message(work_id=work_id, url=url)

                    with suppress(TelegramBadRequest):
                        await call.message.bot.edit_message_text(
                            chat_id=public_channel_id,
                            message_id=work.public_message_id,
                            text=text,
                            reply_markup=keyboard_for_public_message)

                await call.answer()
                await work_handler(call=call, state=state, callback_data=callback_data)
            else:
                await call.answer(text='Запись уже закрыта')
                await work_handler(call=call, state=state, callback_data=callback_data)
        
        @self.callback_query(Pagination.filter(F.action == 'back_to_works'), StateFilter(UI_UserStates.Main_Menu))
        async def back_to_works_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            await call.answer()
            await works_handler(call=call, state=state, callback_data=callback_data)
        
        @self.callback_query(F.data == 'back_to_workdays', StateFilter(UI_UserStates.Main_Menu))
        async def back_to_workdays_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            await work_days_handler(call=call, state=state)
        
        @self.callback_query(F.data == 'back_to_job_list', StateFilter(UI_UserStates.Main_Menu))
        async def back_to_job_list_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            await job_list_handler(message=call.message, state=state, message_id=call.message.message_id)
        
        @self.callback_query(F.data == 'close_job_list', StateFilter(UI_UserStates.Main_Menu))
        async def close_profile_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text='Список работы закрыт', reply_markup=None)
            await main_menu_handler(message=call.message, state=state)


        

        @self.message(F.text.in_('📋Профиль'), StateFilter(UI_UserStates.Main_Menu))
        async def profile_handler(message: Message, state: FSMContext, user: User, message_id: int = None):
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')
            text = user.profile(bus_stop_list)
            inline_keyboard = self.inline_keyboards.profile
            if message_id:
                with suppress(TelegramBadRequest):
                    await message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await message.answer(text='Открываю профиль...', reply_markup=self.reply_keyboards.remove)
                await message.answer(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(F.data == 'edit_profile', StateFilter(UI_UserStates.Main_Menu))
        async def edit_profile_handler(call: CallbackQuery, state: FSMContext, old_message: bool = True):

            inline_keyboard = self.inline_keyboards.edit_profile

            if old_message:
                await call.answer()
                with suppress(TelegramBadRequest):
                    await call.message.edit_text(
                        text=f"Что желаете изменить:",
                        reply_markup=inline_keyboard
                    )
            else:
                await call.message.answer(
                        text=f"Что желаете изменить:",
                        reply_markup=inline_keyboard
                    )

        @self.callback_query(or_f(Pagination.filter(F.action == 'back'), F.data == 'cancel_edit_profile'), StateFilter(UI_UserStates.Edit_Firstname,
                                                                          UI_UserStates.Edit_Lastname,
                                                                          UI_UserStates.Edit_Age,
                                                                          UI_UserStates.Edit_Gender,
                                                                          UI_UserStates.Edit_Phone,
                                                                          UI_UserStates.Edit_Card_ID,
                                                                          UI_UserStates.Edit_BusStop,
                                                                          ))
        async def edit_first_name_profile_handler(call: CallbackQuery, state: FSMContext):
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text='<b>Вы отменили изменения.</b>')
            await state.set_state(state=UI_UserStates.Main_Menu)
            await edit_profile_handler(call=call, state=state, old_message=False)

        @self.callback_query(Pagination.filter(F.action.in_(['prev', 'next', 'start'])), StateFilter(UI_UserStates.Main_Menu,
                                                                                                     UI_UserStates.Edit_BusStop))
        async def edit_bus_stop_id_handler(call: CallbackQuery, state:FSMContext, callback_data: Pagination):
            len_list = await self.managerdb.get_const(document_id=config('ID_CONSTS'), key='len_bus_stop_list')
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')
            page = int(callback_data.page)

            keyboard, page = self.inline_keyboards.bus_stop_list(page_num=page,
                                                           action=callback_data.action, 
                                                           len_list=len_list,
                                                           bus_stop_list=bus_stop_list,
                                                           max_page=len(bus_stop_list))

            await state.set_state(state=UI_UserStates.Edit_BusStop)
            
            await call.answer()
            with suppress(TelegramBadRequest):
                await call.message.edit_text(
                    text=f"<b>Выберите остановку:</b>\n\nСтраница {page+1}",
                    reply_markup=keyboard
                )

        @self.callback_query(Pagination.filter(F.action == 'select'), StateFilter(UI_UserStates.Edit_BusStop))
        async def select_edit_bus_stop_id_handler(call: CallbackQuery, state:FSMContext, callback_data: Pagination):

            bus_stop_id = int(callback_data.page)
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')
            await self.managerdb.update_user_data(chat_id=call.message.chat.id, update=dict(bus_stop_id=bus_stop_id))
            
            with suppress(TelegramBadRequest):
                await call.message.edit_text(
                    text=f"Вы выбрали остановку - <b>{bus_stop_list[bus_stop_id]}</b>",
                )

            await state.set_state(UI_UserStates.Main_Menu)

            user = await self.managerdb.get_user(chat_id=call.message.chat.id)

            await call.answer()
            await profile_handler(message=call.message, state=state, user=user)
        
        @self.callback_query(F.data == 'edit_card_id', StateFilter(UI_UserStates.Main_Menu))
        async def edit_card_id_profile_handler(call: CallbackQuery, state: FSMContext):
            inline_keyboard = self.inline_keyboards.cancel_edit_profile
            
            await state.set_state(UI_UserStates.Edit_Card_ID)
            await call.answer()
            with suppress(TelegramBadRequest):
                msg = await call.message.edit_text(text='Введите 16-значный номер вашей банковской карты:', reply_markup=inline_keyboard)
            await state.update_data(data={'msg_id_edit_profile': msg.message_id})
        
        @self.message(F.text.isdigit(), F.text.len() == 16, StateFilter(UI_UserStates.Edit_Card_ID))
        async def select_card_id_phone_profile_handler(message: Message, state: FSMContext, user: User):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(card_id=message.text))

            data = await state.get_data()
            edit_msg_id = data.get('msg_id_edit_profile')

            user.card_id = message.text

            with suppress(TelegramBadRequest):
                msg = await message.bot.edit_message_text(
                    chat_id=message.chat.id, message_id=edit_msg_id,
                    text=f'Изменения применены. Теперь ваш номер карты - {user.card_id}')
            
            await state.set_state(state=UI_UserStates.Main_Menu)
            await profile_handler(message=message, state=state, user=user)
        
        @self.callback_query(F.data == 'edit_phone', StateFilter(UI_UserStates.Main_Menu))
        async def edit_phone_profile_handler(call: CallbackQuery, state: FSMContext):
            inline_keyboard = self.inline_keyboards.cancel_edit_profile
            
            await state.set_state(UI_UserStates.Edit_Phone)
            await call.answer()
            with suppress(TelegramBadRequest):
                msg = await call.message.edit_text(text='Введите номер телефона для вашего СБП(начиная с 7 без +):', reply_markup=inline_keyboard)
            await state.update_data(data={'msg_id_edit_profile': msg.message_id})
        
        @self.message(F.text.isdigit(), F.text.len() == 11, StateFilter(UI_UserStates.Edit_Phone))
        async def select_edit_phone_profile_handler(message: Message, state: FSMContext, user: User):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(phone=message.text))

            data = await state.get_data()
            edit_msg_id = data.get('msg_id_edit_profile')

            user.phone = message.text

            with suppress(TelegramBadRequest):
                msg = await message.bot.edit_message_text(
                    chat_id=message.chat.id, message_id=edit_msg_id,
                    text=f'Изменения применены. Теперь ваш телефон для СБП - {user.phone}')
            
            await state.set_state(state=UI_UserStates.Main_Menu)
            await profile_handler(message=message, state=state, user=user)
        
        @self.callback_query(F.data == 'edit_gender', StateFilter(UI_UserStates.Main_Menu))
        async def edit_gender_profile_handler(call: CallbackQuery, state: FSMContext):
            inline_keyboard = self.inline_keyboards.edit_gender_profile
            
            await state.set_state(UI_UserStates.Edit_Gender)
            await call.answer()
            with suppress(TelegramBadRequest):
                msg = await call.message.edit_text(text='Выберите пол:', reply_markup=inline_keyboard)
            await state.update_data(data={'msg_id_edit_profile': msg.message_id})
        
        @self.callback_query(F.data.in_(['select_men_gender', 'select_women_gender']), StateFilter(UI_UserStates.Edit_Gender))
        async def select_gender_age_profile_handler(call: CallbackQuery, state: FSMContext):
            if call.data == 'select_men_gender':
                await self.managerdb.update_user_data(chat_id=call.message.chat.id, update=dict(gender='Мужчина'))
            else:
                await self.managerdb.update_user_data(chat_id=call.message.chat.id, update=dict(gender='Женщина'))

            data = await state.get_data()
            edit_msg_id = data.get('msg_id_edit_profile')

            user = await self.managerdb.get_user(chat_id=call.message.chat.id)
            
            await state.set_state(state=UI_UserStates.Main_Menu)
            await profile_handler(message=call.message, state=state, user=user, message_id=edit_msg_id)
        
        @self.callback_query(F.data == 'edit_age', StateFilter(UI_UserStates.Main_Menu))
        async def edit_age_profile_handler(call: CallbackQuery, state: FSMContext):
            inline_keyboard = self.inline_keyboards.cancel_edit_profile
            
            await state.set_state(UI_UserStates.Edit_Age)
            await call.answer()
            with suppress(TelegramBadRequest):
                msg = await call.message.edit_text(text='Введите возраст:', reply_markup=inline_keyboard)
            await state.update_data(data={'msg_id_edit_profile': msg.message_id})
        
        @self.message(F.text.isdigit() < 99, StateFilter(UI_UserStates.Edit_Age))
        async def select_edit_age_profile_handler(message: Message, state: FSMContext, user: User):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(age=int(message.text)))

            data = await state.get_data()
            edit_msg_id = data.get('msg_id_edit_profile')

            user.age = int(message.text)

            with suppress(TelegramBadRequest):
                msg = await message.bot.edit_message_text(
                    chat_id=message.chat.id, message_id=edit_msg_id,
                    text=f'Изменения применены. Теперь ваш возраст - {user.age}')
            
            await state.set_state(state=UI_UserStates.Main_Menu)
            await profile_handler(message=message, state=state, user=user)
            
        @self.callback_query(F.data == 'edit_fullname', StateFilter(UI_UserStates.Main_Menu))
        async def edit_first_name_profile_handler(call: CallbackQuery, state: FSMContext):
            
            inline_keyboard = self.inline_keyboards.cancel_edit_profile
            
            await state.set_state(UI_UserStates.Edit_Firstname)
            await call.answer()
            with suppress(TelegramBadRequest):
                msg = await call.message.edit_text(text='Введите новую фамилию:', reply_markup=inline_keyboard)
            await state.update_data(data={'msg_id_edit_profile': msg.message_id})
        
        @self.message(F.text.split(' ').len() == 1, StateFilter(UI_UserStates.Edit_Firstname))
        async def edit_last_name_profile_handler(message: Message, state: FSMContext):
            
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(first_name=message.text))

            data = await state.get_data()
            edit_msg_id = data.get('msg_id_edit_profile')
            inline_keyboard = self.inline_keyboards.cancel_edit_profile

            await state.set_state(state=UI_UserStates.Edit_Lastname)

            with suppress(TelegramBadRequest):
                msg = await message.bot.edit_message_text(
                    chat_id=message.chat.id, message_id=edit_msg_id,
                    text=f'Фамилия - {message.text}\n\nТеперь введите новое имя:', reply_markup=inline_keyboard)

        @self.message(F.text.split(' ').len() == 1, StateFilter(UI_UserStates.Edit_Lastname))
        async def select_edit_fullname_profile_handler(message: Message, state: FSMContext, user: User):
            await self.managerdb.update_user_data(chat_id=message.chat.id, update=dict(last_name=message.text))

            data = await state.get_data()
            edit_msg_id = data.get('msg_id_edit_profile')

            user.last_name = message.text

            with suppress(TelegramBadRequest):
                msg = await message.bot.edit_message_text(
                    chat_id=message.chat.id, message_id=edit_msg_id,
                    text=f'Изменения применены - {user.first_name} {user.last_name}')
            
            await state.set_state(state=UI_UserStates.Main_Menu)
            await profile_handler(message=message, state=state, user=user)

        
        
        @self.callback_query(F.data == 'ref_link', StateFilter(UI_UserStates.Main_Menu))
        async def profile_ref_link_handler(call: CallbackQuery, state: FSMContext):
            bot_info = await call.bot.get_me()

            user = await self.managerdb.get_user(chat_id=call.message.chat.id)

            inline_keyboard = self.inline_keyboards.ref_link

            await call.answer()
            with suppress(TelegramBadRequest):
                await call.message.edit_text(
                    text=f"<code>https://t.me/{bot_info.username}?start={user.ref_id}</code>",
                    reply_markup=inline_keyboard
                )

        @self.callback_query(F.data == 'back_to_profile', StateFilter(UI_UserStates.Main_Menu))
        async def back_to_profile_handler(call: CallbackQuery, state: FSMContext):
            user = await self.managerdb.get_user(chat_id=call.message.chat.id)
            await call.answer()
            await profile_handler(message=call.message, state=state, user=user, message_id=call.message.message_id)
        
        @self.callback_query(F.data == 'close_profile', StateFilter(UI_UserStates.Main_Menu))
        async def close_profile_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text='Профиль закрыт', reply_markup=None)
            await main_menu_handler(message=call.message, state=state)
        
        @self.callback_query(F.data == 'transactions', StateFilter(UI_UserStates.Main_Menu))
        async def profile_transaction_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination = None):
            await state.set_state(state=UI_UserStates.Menu_Transactions)
            user = await self.managerdb.get_user(chat_id=call.message.chat.id)
            max_page = (len(user.history_wallet) + 4) // 5

            page = 0
            if callback_data:
                page = int(callback_data.page)

            transaction_id_list = user.get_transaction(page=page)

            transactions = await self.managerdb.get_transactions(trans_id_list=transaction_id_list)

            text = f'<b>Транзакции:</b>\n\n{f"({page+1}/{max_page})" if max_page > 1 else ""}'

            inline_keyboard = self.inline_keyboards.transaction_list(transactions=transactions, page=page, max_page=max_page)

            with suppress(TelegramBadRequest):
                await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            await call.answer()
    

        @self.callback_query(Pagination.filter(F.action.in_(['next', 'prev'])), StateFilter(UI_UserStates.Menu_Transactions))
        async def button_profile_transaction_handler(call: CallbackQuery, state:FSMContext, callback_data: Pagination):

            user = await self.managerdb.get_user(chat_id=call.message.chat.id)
            max_page = (len(user.history_wallet) + 4) // 5

            page_num = int(callback_data.page)
            action = callback_data.action
            callback_data.page = str(page_num + 1 if page_num < max_page - 1 else 0)
            if action == 'prev':
                callback_data.page = str(page_num - 1 if page_num > 0 else max_page - 1)
            
            await profile_transaction_handler(call=call ,state=state, callback_data=callback_data)
            
        @self.callback_query(Pagination.filter(F.action == 'back'), StateFilter(UI_UserStates.Menu_Transactions))
        async def back_button_profile_transaction_handler(call: CallbackQuery, state:FSMContext, callback_data: Pagination):
            await state.set_state(state=UI_UserStates.Main_Menu)
            await back_to_profile_handler(call=call, state=state)
        
        @self.callback_query(Pagination.filter(F.action == 'select'), StateFilter(UI_UserStates.Menu_Transactions))
        async def select_profile_transaction_handler(call: CallbackQuery, state:FSMContext, callback_data: Pagination):
            trans_id = callback_data.page
            transaction: Transaction = await self.managerdb.get_transaction(trans_id=trans_id)

            text = transaction.all_info_for_user
            inline_keyboard = self.inline_keyboards.profile_info_transaction
            
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            await call.answer()
        
        @self.callback_query(F.data == 'back_to_transactions', StateFilter(UI_UserStates.Menu_Transactions))
        async def back_button_transactions_handler(call: CallbackQuery, state:FSMContext):
            await profile_transaction_handler(call=call, state=state)