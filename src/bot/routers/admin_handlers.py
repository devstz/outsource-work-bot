import asyncio
import datetime
import decouple
from contextlib import suppress
from datetime import timedelta, datetime

from aiogram import Bot, F, Router
from aiogram.enums.parse_mode import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, or_f, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from ..keyboards import (
    CustomCallData,
    DayCallData,
    InlineAdminKeyboards,
    Pagination,
    ReplyAdminKeyboards,
    UserCallData,
)
from ..routers.auth_admin_handlers import AuthAdminHandlersRouter
from ..states import AdminStates, AuthAdminStates, UI_UserStates

from models import Transaction, User
from services import ManagerDB


class AdminHandlersRouter(Router):
    reply_keyboards: ReplyAdminKeyboards = ReplyAdminKeyboards()
    inline_keyboards: InlineAdminKeyboards = InlineAdminKeyboards()

    def __init__(self, managerdb: ManagerDB) -> None:
        self.managerdb: ManagerDB = managerdb
        super().__init__()
        self.setup()

    def setup(self):
        self.include_router(AuthAdminHandlersRouter(managerdb=self.managerdb))
        self.setup_middlewares()
        self.setup_handlers()
    
    def setup_middlewares(self):
        pass

    def setup_handlers(self):
        @self.message(F.text.in_(['Назад']), StateFilter(AdminStates.Main_Menu))
        async def exit_admin_to_main_menu(message: Message, state: FSMContext):
            await state.clear()
            keyboard = self.reply_keyboards.remove
            await message.answer('Вы вышли из админки. /start', reply_markup=keyboard)

        @self.message(F.text.in_(['Админ-панель']), StateFilter(AdminStates.Main_Menu))
        async def main_menu_handler(message: Message, state: FSMContext):

            keyboard = self.reply_keyboards.admin_menu

            await message.answer("<b>Админ-панель:</b>", reply_markup=keyboard)
        
        
        @self.message(F.text.in_(['📊Статистика']), StateFilter(AdminStates.Main_Menu))
        async def statistics_menu_handler(message: Message, state: FSMContext, message_id: bool = None):

            inline_keyboard = self.inline_keyboards.statistics_menu
            text = "<b>📊Выберите функцию:</b>"
            if message_id:
                with suppress(TelegramBadRequest):
                    await message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await message.answer(text='Открываю меню стастистики...', reply_markup=self.reply_keyboards.remove)
                await message.answer(text=text, reply_markup=inline_keyboard)
        

        
        @self.callback_query(F.data == 'close_statistics_menu', StateFilter(AdminStates.Main_Menu))
        async def close_statistics_menu_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text='Меню статистики закрыто', reply_markup=None)
            await main_menu_handler(message=call.message, state=state)
        
        
        @self.message(F.text.in_(['📦Другое']), StateFilter(AdminStates.Main_Menu))
        async def other_menu_handler(message: Message, state: FSMContext):

            keyboard = self.reply_keyboards.other_menu

            await message.answer("Вкладка <b>📦Другое:</b>", reply_markup=keyboard)
        
        @self.message(F.text.in_(['Назад в меню']), StateFilter(AdminStates.Main_Menu))
        async def back_to_admin_panel_handler(message: Message, state: FSMContext):
            await main_menu_handler(message=message, state=state)
        
        @self.message(F.text.in_(['📮Рассылка в боте']), StateFilter(AdminStates.Main_Menu))
        async def mailing_bot_handler(message: Message, state: FSMContext):
            await state.set_state(state=AdminStates.Mailing_bot)
            await message.answer(text='Введите текст для рассылки:', reply_markup=self.reply_keyboards.cancel)
        
        @self.message(F.text.in_(['Отменить']), StateFilter(AdminStates.Mailing_bot))
        async def mailing_bot_handler(message: Message, state: FSMContext):
            await state.set_state(state=AdminStates.Main_Menu)
            await other_menu_handler(message=message, state=state)
        
        @self.message(StateFilter(AdminStates.Mailing_bot))
        async def mailing_bot_handler(message: Message, state: FSMContext):
            print(message.text)
            print(message.entities)
            successful, failed = 0, 0
            text = f'Просим ничего не писать, пока рассылка не осуществится...\n\nУспешно: {successful}\nПровально: {failed}'
            msg = await message.answer(text=text)

            users_id_list = await self.managerdb.get_list_users()

            for user_id in users_id_list:
                try:
                    await message.bot.send_message(chat_id=user_id, text=message.text)
                    successful += 1
                except:
                    print(f'user - {user_id} banned bot')
                    failed += 1
                if users_id_list.index(user_id) == len(users_id_list) - 1 or not successful % 4 or not failed % 4:
                    text = f'Просим ничего не писать, пока рассылка не осуществится...\n\nУспешно: {successful}\nПровально: {failed}'
                    with suppress(TelegramBadRequest):
                        await message.bot.edit_message_text(text=text, chat_id=message.chat.id, message_id=msg.message_id)

            await state.set_state(state=AdminStates.Main_Menu)
            await other_menu_handler(message=message, state=state)
        

        @self.message(F.text == '👥Пользователи', StateFilter(AdminStates.Main_Menu))
        async def users_menu_handler(message: Message, state: FSMContext, message_id: int = None):

            text = '<b>Выбери действие</b>:'
            inline_keyboard = self.inline_keyboards.users_menu
            if message_id:
                with suppress(TelegramBadRequest):
                    await message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await message.answer(text='Открываю меню пользователей...', reply_markup=self.reply_keyboards.remove)
                await message.answer(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(F.data == 'search_users', StateFilter(AdminStates.Main_Menu))
        async def search_users_handler(call: CallbackQuery, state: FSMContext):
            text = '<b>Введите одно из предложенных для поиска:</b>\n\n <code> - ID пользователя\n - Реферальный ID\n - Фамилия Имя\n - Имя пользователя</code>'
            inline_keyboard = self.inline_keyboards.cancel_search_users
            await state.set_state(state=AdminStates.Search_users)
            await call.answer()
            with suppress(TelegramBadRequest):
                msg = await call.message.edit_text(text=text, reply_markup=inline_keyboard)
                await state.update_data(data={'msg_id_search_user': msg.message_id})
        
        @self.callback_query(Pagination.filter(F.action.in_(['back_to_users_menu'])), StateFilter(AdminStates.Search_users))
        async def back_to_users_menu_with_search_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            await state.set_state(state=AdminStates.Main_Menu)
            await users_menu_handler(message=call.message, state=state, message_id=call.message.message_id)
        
        @self.message(StateFilter(AdminStates.Search_users))
        async def select_search_user_handler(message: Message, state: FSMContext):
            user = await self.managerdb.search_user(fltr=message.text)
            if user:
                data = await state.get_data()
                msg_id = data.get('msg_id_search_user')
                callback_data = UserCallData(action='select_user', page=0, user_id=user.chat_id)
                await state.set_state(state=AdminStates.Main_Menu)
                with suppress(TelegramBadRequest):
                    await message.bot.edit_message_text(chat_id=message.chat.id, message_id=msg_id, text=f'Пользователь {user.get_names} найден.')
                await select_user_handler(call=message, state=state, callback_data=callback_data, old_message=False)
            else:
                await message.answer(text='Пользователь не найден.')
            
    
        @self.callback_query(Pagination.filter(F.action.in_(['users_list'])), StateFilter(AdminStates.Main_Menu))
        async def users_list_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            page = int(callback_data.page)
            page, max_page, user_id_list = await self.managerdb.get_list_users_with_page(page=page)
            print(user_id_list, max_page)
            if user_id_list:
                users = await self.managerdb.get_users(user_id_list=user_id_list)
                text = f'<b>Выбери пользователя</b>:\n\nСтраница {page+1}/{max_page+1}'
            else:
                users = []
                text = f'Пусто.'
            inline_keyboard = self.inline_keyboards.users_list(users=users, page=page, max_page=max_page)
            
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)

        @self.callback_query(Pagination.filter(F.action.in_(['back_to_users_menu'])), StateFilter(AdminStates.Main_Menu))
        async def back_to_users_menu_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            await users_menu_handler(message=call.message, state=state, message_id=call.message.message_id)
        
        @self.callback_query(UserCallData.filter(F.action.in_(['select_user'])), StateFilter(AdminStates.Main_Menu))
        async def select_user_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination, old_message: bool = True):
            if isinstance(call, CallbackQuery):
                message = call.message
            else:
                message = call

            chat_id = int(callback_data.user_id)
            page = int(callback_data.page)
            user = await self.managerdb.get_user(chat_id=chat_id)
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')
            text = user.profile_admin(bus_stop_list=bus_stop_list)
            inline_keyboard = self.inline_keyboards.profile_user(user=user, page=page)
            
            if old_message:
                await call.answer()
                with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard, parse_mode=ParseMode.HTML)
            else:
                await message.answer(text=text, reply_markup=inline_keyboard, parse_mode=ParseMode.HTML)
        
        @self.callback_query(UserCallData.filter(F.action.in_(['delete_user'])), StateFilter(AdminStates.Main_Menu))
        async def delete_user_hanlder(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text='Вы уверены что хотите удалить пользователя?\n\nВсе его данные полностью сотрутся, но во всех списках на работу(архивных и активных) он останется.')

        @self.callback_query(UserCallData.filter(F.action.in_(['switch_ban_user'])), StateFilter(AdminStates.Main_Menu))
        async def switch_ban_user_hanlder(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            page = callback_data.page
            user_id = int(callback_data.user_id)
            user = await self.managerdb.get_user(chat_id=user_id)
            await self.managerdb.update_user_data(chat_id=user_id, update=dict(ban=not user.ban))
            await select_user_handler(call=call, state=state, callback_data=callback_data)

        @self.callback_query(UserCallData.filter(F.action.in_(['wallet_transaction_user'])), StateFilter(AdminStates.Main_Menu))
        async def wallet_transaction_user_hanlder(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            page = callback_data.page
            user_id = callback_data.user_id
            await state.update_data(data={'user_id_for_transaction': user_id, 'page_users': page, })
            inline_keyboard = self.inline_keyboards.wallet_transaction_user(page=page, user_id=user_id)

            await call.answer()
            await state.set_state(state=AdminStates.Wallet_Transaction)
            with suppress(TelegramBadRequest):
                msg = await call.message.edit_text(text='Введите число вычета или взноса на кошелек:', reply_markup=inline_keyboard)
                await state.update_data(data={'message_id_for_edit': msg.message_id})
        
        @self.callback_query(UserCallData.filter(F.action.in_(['cancel_transaction'])), StateFilter(AdminStates.Wallet_Transaction))
        async def cancel_transaction_user_hanlder(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            await state.set_state(state=AdminStates.Main_Menu)
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text='Операция отменена.')
            await select_user_handler(call=call, state=state, callback_data=callback_data, old_message=False)
        
        @self.message(or_f(F.text.isdigit(), F.text[1:].isdigit()), StateFilter(AdminStates.Wallet_Transaction))
        async def cancel_transaction_user_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            page = int(data['page_users'])
            user_id = int(data['user_id_for_transaction'])
            msg_id = int(data['message_id_for_edit'])
            money = int(message.text)

            user = await self.managerdb.get_user(chat_id=user_id) 
            if user.wallet + money < 0:
                money = -user.wallet
            
            await self.managerdb.update_user_data(chat_id=user_id, update=dict(wallet=user.wallet + money))
            with suppress(TelegramBadRequest):
                await message.bot.edit_message_text(chat_id=message.chat.id, message_id=msg_id, text='Вы совершили операцию.')
            callback_data = UserCallData(action='select_user', user_id=user_id, page=page)
            
            await state.set_state(state=AdminStates.Main_Menu)

            await select_user_handler(call=message, state=state, callback_data=callback_data, old_message=False)


        @self.message(F.text == '🍜Выплаты', StateFilter(AdminStates.Main_Menu))
        async def payments_list_handler(message: Message, state: FSMContext, message_id: int = None):
            text = '<b>Выбери категорию</b>:'
            inline_keyboard = self.inline_keyboards.payments_menu
            if message_id:
                with suppress(TelegramBadRequest):
                    await message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await message.answer(text='Открываю меню выплат...', reply_markup=self.reply_keyboards.remove)
                await message.answer(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(F.data == 'close_payments_menu', StateFilter(AdminStates.Main_Menu))
        async def close_payments_menu_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text='Меню выплат закрыто.', reply_markup=None)
            await main_menu_handler(message=call.message, state=state)



            
        @self.callback_query(UserCallData.filter(F.action.in_(['payments_ref'])), StateFilter(AdminStates.Main_Menu))
        async def payments_ref_menu_handler(call: CallbackQuery, state: FSMContext, callback_data: UserCallData, old_message: bool = True):
            message = call
            if isinstance(call, CallbackQuery):
                message: Message = call.message

            page = int(callback_data.page)
            len_list = 6
            users = await self.managerdb.get_users_filter({'awaiting_ref_payments.0': {'$exists': True}})
            text = '<b>Выберите пользователя для оплаты счетов:</b>'
            await self.managerdb.update_admin_data(chat_id=message.chat.id, update=dict(assigned_invoices=[]))
            inline_keyboard = self.inline_keyboards.payments_ref_list(users=users[page*len_list:(page+1)*len_list], page=page, len_list=len_list)

            if old_message:
                await call.answer()
                with suppress(TelegramBadRequest):
                        await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                message = call
                if isinstance(call, CallbackQuery):
                    message: Message = call.message
                await message.answer(text=text, reply_markup=inline_keyboard)


        @self.callback_query(UserCallData.filter(F.action.in_(['select_user_for_payments_ref'])), StateFilter(AdminStates.Main_Menu, 
                                                                                                          AdminStates.Payment_Worker_ref))
        async def select_user_for_payments_ref_handler(call: CallbackQuery, state: FSMContext, callback_data: UserCallData):
            await state.set_state(state=AdminStates.Main_Menu)
            page = int(callback_data.page)
            len_list = 6
            user_id = int(callback_data.user_id)
            
            user = await self.managerdb.get_user(chat_id=user_id)
            admin = await self.managerdb.get_admin(chat_id=call.message.chat.id)

            text = '<b>Выделите платежи для оплаты:</b>'
            transactions = await self.managerdb.get_transactions(trans_id_list=user.awaiting_ref_payments)
            print(transactions)
            print(transactions[page*len_list:(page+1)*len_list])
            print('transssss')
            payment_trans = await self.managerdb.get_transactions(trans_id_list=admin.assigned_invoices)
            
            inline_keyboard = self.inline_keyboards.payments_ref_user_list(
                                                        admin=admin,
                                                        user=user,
                                                        page=page,
                                                        transactions=transactions[page*len_list:(page+1)*len_list],
                                                        payment_trans=payment_trans,
                                                        len_list=len_list
                                                    )
            
            await state.set_data({})
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)


        @self.callback_query(CustomCallData.filter(F.action.in_(['payment_worker_ref'])), StateFilter(AdminStates.Main_Menu))
        async def payment_worker_ref_handler(call: CallbackQuery, state: FSMContext, callback_data: CustomCallData):
            
            page = int(callback_data.page)
            user_id = int(callback_data.user_id)
            money = int(callback_data.item_id)
            
            admin = await self.managerdb.get_admin(chat_id=call.message.chat.id)
            user = await self.managerdb.get_user(chat_id=user_id)
            data = await state.get_data()
            type_payment = data.get('type_payment')

            transactions = await self.managerdb.get_transactions(trans_id_list=admin.assigned_invoices)

            text = admin.info_for_payment(user=user, money=money, transactions=transactions, type_payment=type_payment)

            if type_payment:
                inline_keyboard = self.inline_keyboards.cancel_payment_ref_worker(user=user, page=page)
                await state.set_state(state=AdminStates.Payment_Worker_ref)

            else:
                inline_keyboard = self.inline_keyboards.select_type_ref_payment(page=page, user_id=user_id)
            
            await state.update_data(data={'money': money, 'for_user_id': user.chat_id, 'page': page})
            await call.answer()
            with suppress(TelegramBadRequest):
                    msg = await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            await state.update_data(data={'message_id_payment': msg.message_id})
        
        @self.callback_query(Pagination.filter(F.action.in_(['type_payment_ref_select'])), StateFilter(AdminStates.Main_Menu))
        async def type_ref_payment_select_handler(call: CallbackQuery, state: FSMContext, callback_data: CustomCallData):
            data = await state.get_data()
            page = data.get('page')
            user_id = data.get('for_user_id')
            money = data.get('money')

            await state.update_data({'type_payment': callback_data.page})

            callback_data = CustomCallData(action='payment_worker_ref', page=page, user_id=user_id, item_id=money)

            await payment_worker_ref_handler(call=call, state=state, callback_data=callback_data)


        @self.message(F.photo, F.caption.isdigit(), StateFilter(AdminStates.Payment_Worker_ref))
        async def select_payment_worker_ref_handler(message: Message, state: FSMContext):
            data = await state.get_data()
            money = data.get('money')
            money_check = int(message.caption)
            type_id = int(data.get('type_payment'))
            message_id_payment = data.get('message_id_payment')
            admin = await self.managerdb.get_admin(chat_id=message.chat.id)
            transactions = await self.managerdb.get_transactions(trans_id_list=admin.assigned_invoices)
            print(money, money_check, sum([trans.money for trans in transactions]))
            for_user_id = data.get('for_user_id')
            for_user = await self.managerdb.get_user(chat_id=for_user_id)

            if for_user.ref_money < money:
                await message.answer(text='Счет пользователя некорректен. Сумма вывода превышает счет пользователя.')
                return
                
            if money == money_check == sum([trans.money for trans in transactions]):


                photo_id = message.photo[-1].file_id


                transaction = await self.managerdb.create_transaction(data=message, for_user_id=for_user_id, money=money, type_id=type_id, photo_id=photo_id)

                await self.managerdb.add_user_data(chat_id=for_user_id, update=dict(history_wallet=transaction.trans_id))
                await self.managerdb.update_user_data(chat_id=for_user_id, update=dict(ref_moneny=for_user.ref_money - money))

                for trans in transactions:
                    await self.managerdb.update_to_transaction(trans_id=trans.trans_id, paid=True)
                    await self.managerdb.update_to_transaction(trans_id=trans.trans_id, paid_date=message.date+timedelta(hours=7))
                    await self.managerdb.del_to_user(chat_id=for_user_id, awaiting_ref_payments=trans.trans_id)
                
                await self.managerdb.add_to_work(work_id=trans.work_id, payments=transaction.trans_id)

                with suppress(TelegramBadRequest):
                    await message.bot.edit_message_text(text='Операция выполнена.', chat_id=message.chat.id, message_id=message_id_payment)

                
                text_channel = f'<code>Операция - {transaction.trans_id}\n\nСумма {transaction.money}₽\nДата: {transaction.date}\nПолучатель - {transaction.for_user_id}\nОтправитель - {transaction.from_user_id}</code>'
                text_for_user = f'<code>Операция - {transaction.trans_id}\n\nСумма {transaction.money}₽\nДата: {transaction.date}\n</code>'
                
                trans_channel_id = await self.managerdb.get_const(document_id=config("ID_TRANSACTION_CHANNEL_ID"), key='transaction_channel_id')
                print(trans_channel_id)
                with suppress(TelegramBadRequest):
                    await message.bot.send_photo(chat_id=trans_channel_id, photo=photo_id, caption=text_channel)
                with suppress(TelegramBadRequest):
                    await message.bot.send_photo(chat_id=transaction.for_user_id, photo=photo_id, caption=text_for_user)

                text = f'<code>Операция {transaction.trans_id} была совершена на сумму {transaction.money}₽ в {transaction.date}</code>'
                await message.answer(text=text)

                await state.set_state(state=AdminStates.Main_Menu)
                callback_data = UserCallData(action='null', page=0, user_id='null')
                await payments_ref_menu_handler(call=message, state=state, callback_data=callback_data, old_message=False)
            else:
                await message.answer(text='Сумма некорректна, повторите попытку.')
            

            

        @self.callback_query(CustomCallData.filter(F.action.in_(['switch_trans_worker_ref'])), StateFilter(AdminStates.Main_Menu))
        async def switch_transaction_worker_for_payments_ref_handler(call: CallbackQuery, state: FSMContext, callback_data: CustomCallData):
            trans_id = callback_data.item_id
            admin = await self.managerdb.get_admin(chat_id=call.message.chat.id)
            print(admin, admin.assigned_invoices, 'adminsss')
            if trans_id in admin.assigned_invoices:
                await self.managerdb.del_to_admin(chat_id=call.message.chat.id, assigned_invoices=trans_id)
            else:
                await self.managerdb.add_admin_data(chat_id=call.message.chat.id, assigned_invoices=trans_id)

            callback_data = UserCallData(action='select_user_for_payments_ref', page=callback_data.page, user_id=callback_data.user_id)

            await select_user_for_payments_ref_handler(call=call, state=state, callback_data=callback_data)






        
        @self.callback_query(UserCallData.filter(F.action.in_(['payments_work'])), StateFilter(AdminStates.Main_Menu))
        async def payments_work_menu_handler(call: CallbackQuery, state: FSMContext, callback_data: UserCallData, old_message: bool = True):
            message = call
            if isinstance(call, CallbackQuery):
                message: Message = call.message

            page = int(callback_data.page)
            len_list = 6
            users = await self.managerdb.get_users_filter({'awaiting_payments.0': {'$exists': True}})
            text = '<b>Выберите пользователя для оплаты счетов:</b>'
            await self.managerdb.update_admin_data(chat_id=message.chat.id, update=dict(assigned_invoices=[]))
            inline_keyboard = self.inline_keyboards.payments_work_list(users=users[page*len_list:(page+1)*len_list], page=page, len_list=len_list)

            if old_message:
                await call.answer()
                with suppress(TelegramBadRequest):
                        await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                message = call
                if isinstance(call, CallbackQuery):
                    message: Message = call.message
                await message.answer(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(UserCallData.filter(F.action.in_(['select_user_for_payments'])), StateFilter(AdminStates.Main_Menu, 
                                                                                                          AdminStates.Payment_Worker))
        async def select_user_for_payments_handler(call: CallbackQuery, state: FSMContext, callback_data: UserCallData):
            await state.set_state(state=AdminStates.Main_Menu)
            page = int(callback_data.page)
            len_list = 6
            user_id = int(callback_data.user_id)
            
            user = await self.managerdb.get_user(chat_id=user_id)
            admin = await self.managerdb.get_admin(chat_id=call.message.chat.id)

            text = '<b>Выделите платежи для оплаты:</b>'
            transactions = await self.managerdb.get_transactions(trans_id_list=user.awaiting_payments)
            payment_trans = await self.managerdb.get_transactions(trans_id_list=admin.assigned_invoices)
            
            inline_keyboard = self.inline_keyboards.payments_user_list(
                                                        admin=admin,
                                                        user=user,
                                                        page=page,
                                                        transactions=transactions[page*len_list:(page+1)*len_list],
                                                        payment_trans=payment_trans,
                                                        len_list=len_list
                                                    )
            
            await state.set_data({})
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(CustomCallData.filter(F.action.in_(['payment_worker'])), StateFilter(AdminStates.Main_Menu))
        async def payment_worker_handler(call: CallbackQuery, state: FSMContext, callback_data: CustomCallData):
            
            page = int(callback_data.page)
            user_id = int(callback_data.user_id)
            money = int(callback_data.item_id)
            
            admin = await self.managerdb.get_admin(chat_id=call.message.chat.id)
            user = await self.managerdb.get_user(chat_id=user_id)
            data = await state.get_data()
            type_payment = data.get('type_payment')

            transactions = await self.managerdb.get_transactions(trans_id_list=admin.assigned_invoices)

            text = admin.info_for_payment(user=user, money=money, transactions=transactions, type_payment=type_payment)

            if type_payment:
                inline_keyboard = self.inline_keyboards.cancel_payment_worker(user=user, page=page)
                await state.set_state(state=AdminStates.Payment_Worker)

            else:
                inline_keyboard = self.inline_keyboards.select_type_payment(page=page, user_id=user_id)
            
            await state.update_data(data={'money': money, 'for_user_id': user.chat_id, 'page': page})
            await call.answer()
            with suppress(TelegramBadRequest):
                    msg = await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            await state.update_data(data={'message_id_payment': msg.message_id})
        
        @self.callback_query(Pagination.filter(F.action.in_(['type_payment_select'])), StateFilter(AdminStates.Main_Menu))
        async def type_payment_select_handler(call: CallbackQuery, state: FSMContext, callback_data: CustomCallData):
            data = await state.get_data()
            page = data.get('page')
            user_id = data.get('for_user_id')
            money = data.get('money')

            await state.update_data({'type_payment': callback_data.page})

            callback_data = CustomCallData(action='payment_worker', page=page, user_id=user_id, item_id=money)

            await payment_worker_handler(call=call, state=state, callback_data=callback_data)


        @self.message(F.photo, F.caption.isdigit(), StateFilter(AdminStates.Payment_Worker))
        async def select_payment_worker_handler(message: Message, state: FSMContext):
            data = await state.get_data()
            money = data.get('money')
            money_check = int(message.caption)
            type_id = int(data.get('type_payment'))
            message_id_payment = data.get('message_id_payment')
            admin = await self.managerdb.get_admin(chat_id=message.chat.id)
            transactions = await self.managerdb.get_transactions(trans_id_list=admin.assigned_invoices)
            print(money, money_check, sum([trans.money for trans in transactions]))
            for_user_id = data.get('for_user_id')
            for_user = await self.managerdb.get_user(chat_id=for_user_id)
            if for_user.wallet < money:
                await message.answer(text='Счет пользователя некорректен. Сумма вывода превышает счет пользователя.')
                return
                
            if money == money_check == sum([trans.money for trans in transactions]):


                photo_id = message.photo[-1].file_id


                transaction = await self.managerdb.create_transaction(data=message, for_user_id=for_user_id, money=money, type_id=type_id, photo_id=photo_id)

                await self.managerdb.add_user_data(chat_id=for_user_id, update=dict(history_wallet=transaction.trans_id))
                await self.managerdb.update_user_data(chat_id=for_user_id, update=dict(wallet=for_user.wallet - money))

                for trans in transactions:
                    await self.managerdb.update_to_transaction(trans_id=trans.trans_id, paid=True)
                    await self.managerdb.update_to_transaction(trans_id=trans.trans_id, paid_date=message.date+timedelta(hours=7))
                    await self.managerdb.del_to_user(chat_id=for_user_id, awaiting_payments=trans.trans_id)
                
                await self.managerdb.add_to_work(work_id=trans.work_id, payments=transaction.trans_id)

                with suppress(TelegramBadRequest):
                    await message.bot.edit_message_text(text='Операция выполнена.', chat_id=message.chat.id, message_id=message_id_payment)

                
                text_channel = f'<code>Операция - {transaction.trans_id}\n\nСумма {transaction.money}₽\nДата: {transaction.date}\nПолучатель - {transaction.for_user_id}\nОтправитель - {transaction.from_user_id}</code>'
                text_for_user = f'<code>Операция - {transaction.trans_id}\n\nСумма {transaction.money}₽\nДата: {transaction.date}\n</code>'
                
                trans_channel_id = await self.managerdb.get_const(document_id=config("ID_TRANSACTION_CHANNEL_ID"), key='transaction_channel_id')
                print(trans_channel_id)
                with suppress(TelegramBadRequest):
                    await message.bot.send_photo(chat_id=trans_channel_id, photo=photo_id, caption=text_channel)
                with suppress(TelegramBadRequest):
                    await message.bot.send_photo(chat_id=transaction.for_user_id, photo=photo_id, caption=text_for_user)

                text = f'<code>Операция {transaction.trans_id} была совершена на сумму {transaction.money}₽ в {transaction.date}</code>'
                await message.answer(text=text)

                await state.set_state(state=AdminStates.Main_Menu)
                callback_data = UserCallData(action='null', page=0, user_id='null')
                await payments_work_menu_handler(call=message, state=state, callback_data=callback_data, old_message=False)
            else:
                await message.answer(text='Сумма некорректна, повторите попытку.')
            

            

        @self.callback_query(CustomCallData.filter(F.action.in_(['switch_trans_worker'])), StateFilter(AdminStates.Main_Menu))
        async def switch_transaction_worker_for_payments_handler(call: CallbackQuery, state: FSMContext, callback_data: CustomCallData):
            trans_id = callback_data.item_id
            admin = await self.managerdb.get_admin(chat_id=call.message.chat.id)
            print(admin, admin.assigned_invoices, 'adminsss')
            if trans_id in admin.assigned_invoices:
                await self.managerdb.del_to_admin(chat_id=call.message.chat.id, assigned_invoices=trans_id)
            else:
                await self.managerdb.add_admin_data(chat_id=call.message.chat.id, assigned_invoices=trans_id)
                print('fsdfsd')

            callback_data = UserCallData(action='select_user_for_payments', page=callback_data.page, user_id=callback_data.user_id)

            await select_user_for_payments_handler(call=call, state=state, callback_data=callback_data)

        
        @self.callback_query(F.data == 'back_to_payments_menu', StateFilter(AdminStates.Main_Menu))
        async def back_to_payments_menu_handler(call: CallbackQuery, state: FSMContext):
            await payments_list_handler(message=call.message, state=state, message_id=call.message.message_id)
        
        @self.message(F.text == '💼Работа', StateFilter(AdminStates.Main_Menu))
        async def job_list_handler(message: Message, state: FSMContext, message_id: int = None):

            text = '<b>Выбери категорию</b>:'
            inline_keyboard = self.inline_keyboards.selection_menu
            if message_id:
                with suppress(TelegramBadRequest):
                    await message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await message.answer(text='Открываю меню набора...', reply_markup=self.reply_keyboards.remove)
                await message.answer(text=text, reply_markup=inline_keyboard)
            
        @self.callback_query(F.data == 'active_work_days', StateFilter(AdminStates.Main_Menu))
        async def work_days_handler(call: CallbackQuery, state: FSMContext, new_message: bool = False):

            workdays = await self.managerdb.get_active_workdays()
            
            inline_keyboard = self.inline_keyboards.work_days(workdays=workdays)

            if not new_message:
                await call.answer()
                with suppress(TelegramBadRequest):
                        await call.message.edit_text(text='Актуальные дни работы:', reply_markup=inline_keyboard)
            else:
                await call.message.answer(text='Актуальные дни работы:', reply_markup=inline_keyboard)
        
        
        @self.callback_query(F.data == 'create_workday', StateFilter(AdminStates.Main_Menu))
        async def create_work_day_handler(call: CallbackQuery, state: FSMContext):
            
            day_to_week = await self.managerdb.get_const(document_id=config('ID_DAY_WEEK'), key='day_week')

            dt = datetime.now()
            d_f = dt.strftime(config('FORMAT_DATE'))
            text = f'Введите дату:\n\n<code>Формат - <b>гггг-мм-дд</b>\n\n(Для примера, сегодня - {d_f})</code>'
            inline_keyboard = self.inline_keyboards.select_datetime_work


            await state.set_state(state=AdminStates.Create_Workday)
            await call.answer()
            
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text='Переходим в режим создания рабочего дня...')
            
            await call.message.answer(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(F.data == 'cancel_create_workday', StateFilter(AdminStates.Create_Workday))
        async def cancel_create_active_work_day_handler(call: CallbackQuery, state: FSMContext):
            await state.set_state(state=AdminStates.Main_Menu)
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text='Отмена создания рабочего дня.')
            await work_days_handler(call=call, state=state, new_message=True)
            
        @self.message(StateFilter(AdminStates.Create_Workday))
        async def create_active_work_day_handler(message: Message, state: FSMContext):
            if len(message.text.split('-')) == 3 and len(message.text) >= 9:
                try:
                    dt = datetime.strptime(message.text, "%Y-%m-%d")
                except:
                    await message.answer(text='Дата некорректна.')
                    return

                check_date = await self.managerdb.get_active_workday(date=int(dt.timestamp()))
                if check_date:
                    await message.answer(text='Дата существует.')
                    return

                workday = await self.managerdb.create_workday(date=dt)
                date_f = dt.strftime(config("FORMAT_DATE"))
                text = f'Вы создали рабочий день: {workday.day_ru} ({date_f})'
                inline_keyboard = self.inline_keyboards.select_create_workday(workday=workday)
                
                await state.set_state(state=AdminStates.Main_Menu)
                await message.answer(text=text, reply_markup=inline_keyboard)
            else:
                await message.answer(text='Дата некорректна.')
        
        
        
        @self.callback_query(DayCallData.filter(F.action.in_(['archive_workdays'])), StateFilter(AdminStates.Main_Menu))
        async def archive_workdays_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):

            page = int(callback_data.page)
            len_list = 7
            
            archive_workdays, num_archive_workdays = await self.managerdb.get_archive_workdays(page=page, len_list=len_list)

            max_page = (num_archive_workdays + len_list - 1) // len_list - 1
            
            pg = f'\n\nСтраница {page+1}/{max_page+1}' if page and num_archive_workdays else ''

            text = f'Архивные дни:{pg}'
            inline_keyboard = self.inline_keyboards.archive_workdays(archive_workdays=archive_workdays, page=page, max_page=max_page)

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)

        @self.callback_query(Pagination.filter(F.action.in_(['select_archive_workday'])), StateFilter(AdminStates.Main_Menu))
        async def works_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):

            date = int(callback_data.page)
            works = await self.managerdb.get_archive_works(date=date)

            print(date)

            text, inline_keyboard = self.inline_keyboards.works(works=works, date=date, archived=True)

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)

        
        @self.callback_query(Pagination.filter(F.action.in_(['select_workday'])), StateFilter(AdminStates.Main_Menu))
        async def works_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):

            date = int(callback_data.page)
            works = await self.managerdb.get_works(date=date)

            print(date)

            text, inline_keyboard = self.inline_keyboards.works(works=works, date=date, archived=False)

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            
        @self.callback_query(Pagination.filter(F.action.in_(['archive_workday'])), StateFilter(AdminStates.Main_Menu))
        async def archive_workday_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            date = int(callback_data.page)
            await self.managerdb.archive_workday(date=date)

            await work_days_handler(call=call, state=state)
        
        @self.callback_query(Pagination.filter(F.action.in_(['unarchive_workday'])), StateFilter(AdminStates.Main_Menu))
        async def unarchive_workday_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            date = int(callback_data.page)
            await self.managerdb.unarchive_workday(date=date)

            await archive_workdays_handler(call=call, state=state, callback_data=callback_data)
        
        @self.callback_query(Pagination.filter(F.action.in_(['create_work'])), StateFilter(AdminStates.Main_Menu))
        async def create_header_work_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):

            date_timestamp = int(callback_data.page)
            date = datetime.fromtimestamp(date_timestamp).strftime(config('FORMAT_DATE'))

            workday = await self.managerdb.get_active_workday(date=date_timestamp)

            work = await self.managerdb.create_work(date=date, day_en=workday.day_en, day_ru=workday.day_ru)

            await self.managerdb.add_to_workday(date=date_timestamp, works=work.work_id)

            await state.update_data(data={'now_create_work': work.work_id, 'now_create_work_date': date_timestamp})

            await self.managerdb.add_admin_data(chat_id=call.message.chat.id, now_create_work_id=work.work_id)
            
            text_edit = f'<b>Мы зарегистрировали вашу работу под ID - <code>{work.work_id}</code> на дату {date}.</b>'

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text_edit, reply_markup=None)

            text = '<b>Введите очень короткое название работы:</b>'
            keyboard = self.reply_keyboards.cancel_create_work

            await state.set_state(state=AdminStates.Create_Work)
            
            await call.message.answer(text=text, reply_markup=keyboard)


        @self.message(F.text == 'Отменить', StateFilter(*[AdminStates.Create_Work,
                                                        AdminStates.Select_departure_time_work,
                                                        AdminStates.Select_lunch,
                                                        AdminStates.Select_max_workers_work,
                                                        AdminStates.Select_salary_work,
                                                        AdminStates.Select_age_limit,
                                                        AdminStates.Select_vendor_salary_work,
                                                        AdminStates.Select_salary_workCreate_Work,
                                                        AdminStates.Select_type_payment,
                                                        AdminStates.Select_start_time_work,
                                                        AdminStates.Select_ref_money,
                                                        ]))
        async def cancel_create_work_hanlder(message: Message, state: FSMContext):
            await state.set_state(state=AdminStates.Main_Menu)
            data = await state.get_data()
            date = data.get('now_create_work_date')
            work_id = data.get('now_create_work')

            await self.managerdb.del_work(work_id=work_id, date=date)

            inline_keyboard = inline_keyboard = self.inline_keyboards.back_to_workday(date=date)

            keyboard = self.reply_keyboards.remove

            await message.answer(text='Вы отменили создание работы.', reply_markup=keyboard)
            await message.answer(text='Перейти обратно в рабочий день:', reply_markup=inline_keyboard)


        
        @self.message(StateFilter(AdminStates.Create_Work))
        async def select_salary_work_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            work_id = data.get('now_create_work')

            await self.managerdb.update_to_work(work_id=work_id, header=message.text)

            text = 'Введите размер заработной платы для людей:'
            keyboard = self.reply_keyboards.cancel_create_work

            await state.set_state(state=AdminStates.Select_salary_work)

            await message.answer(text=text, reply_markup=keyboard)
        
        @self.message(F.text.isdigit(), StateFilter(AdminStates.Select_salary_work))
        async def select_vendor_salary_work_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            work_id = data.get('now_create_work')

            await self.managerdb.update_to_work(work_id=work_id, salary=int(message.text))

            text = 'Введите размер заработной платы от поставщика:'
            keyboard = self.reply_keyboards.cancel_create_work

            await state.set_state(state=AdminStates.Select_vendor_salary_work)

            await message.answer(text=text, reply_markup=keyboard)
        
        @self.message(F.text.isdigit(), StateFilter(AdminStates.Select_vendor_salary_work))
        async def select_max_workers_work_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            work_id = data.get('now_create_work')

            await self.managerdb.update_to_work(work_id=work_id, vendor_salary=int(message.text))

            text = 'Введите требующееся кол-во работников:'
            keyboard = self.reply_keyboards.cancel_create_work

            await state.set_state(state=AdminStates.Select_max_workers_work)

            await message.answer(text=text, reply_markup=keyboard)
        
        @self.message(F.text.isdigit(), StateFilter(AdminStates.Select_max_workers_work))
        async def select_age_limit_work_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            work_id = data.get('now_create_work')

            await self.managerdb.update_to_work(work_id=work_id, max_workers=int(message.text))

            text = 'Введите возрастное ограничение:'
            keyboard = self.reply_keyboards.cancel_create_work

            await state.set_state(state=AdminStates.Select_age_limit)

            await message.answer(text=text, reply_markup=keyboard)
        
        @self.message(F.text.isdigit(), StateFilter(AdminStates.Select_age_limit))
        async def select_lunch_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            work_id = data.get('now_create_work')

            await self.managerdb.update_to_work(work_id=work_id, age_limit=int(message.text))

            text = 'Будет ли обед:'

            keyboard = self.reply_keyboards.select_lunch_work

            await state.set_state(state=AdminStates.Select_lunch)

            await message.answer(text=text, reply_markup=keyboard)
        
        @self.message(F.text.in_(['Нет', 'Да']), StateFilter(AdminStates.Select_lunch))
        async def select_departure_time_work_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            work_id = data.get('now_create_work')
            lunch = False
            if message.text == 'Да':
                lunch = True

            await self.managerdb.update_to_work(work_id=work_id, lunch=lunch)

            text = 'Время выхода на остановку<code>(формат чч:мм)</code>:'
            keyboard = self.reply_keyboards.select_departure_time_work

            await state.set_state(state=AdminStates.Select_departure_time_work)

            await message.answer(text=text, reply_markup=keyboard)
        
        @self.message(StateFilter(AdminStates.Select_departure_time_work))
        async def select_start_time_work_hanlder(message: Message, state: FSMContext):
            print(len(message.text.split(':')), len(message.text), message.text)
            if len(message.text.split(':')) == 2 and len(message.text) >= 4:
                data = await state.get_data()
                work_id = data.get('now_create_work')

                await self.managerdb.update_to_work(work_id=work_id, departure_time=message.text)

                text = 'Время с которого начинается работа<code>(формат чч-мм)</code>:'
                keyboard = self.reply_keyboards.select_start_time_work

                await state.set_state(state=AdminStates.Select_start_time_work)

                await message.answer(text=text, reply_markup=keyboard)
            else:
                await message.answer('Некорректно <code>(формат чч:мм)</code>.')

        @self.message(StateFilter(AdminStates.Select_start_time_work))
        async def select_end_time_work_hanlder(message: Message, state: FSMContext):
            if len(message.text.split(':')) == 2 and len(message.text) >= 4:
                data = await state.get_data()
                work_id = data.get('now_create_work')

                await self.managerdb.update_to_work(work_id=work_id, start_work_time=message.text)

                text = 'Время в которое заканчивается работа<code>(формат чч-мм)</code>:'

                keyboard = self.reply_keyboards.select_end_time_work

                await state.set_state(state=AdminStates.Select_end_time_work)

                await message.answer(text=text, reply_markup=keyboard)
            else:
                await message.answer('Некорректно <code>(формат чч:мм)</code>.')

        @self.message(StateFilter(AdminStates.Select_end_time_work))
        async def select_type_payments_hanlder(message: Message, state: FSMContext):
            if len(message.text.split(':')) == 2 and len(message.text) >= 4:
                data = await state.get_data()
                work_id = data.get('now_create_work')

                await self.managerdb.update_to_work(work_id=work_id, end_work_time=message.text)

                text = 'Напишите словами, то каким образом будет выдаваться зарплата:'
                
                keyboard = self.reply_keyboards.cancel_create_work

                await state.set_state(state=AdminStates.Select_type_payment)

                await message.answer(text=text, reply_markup=keyboard)
            else:
                await message.answer('Некорректно <code>(формат чч:мм)</code>.')
        
        @self.message(StateFilter(AdminStates.Select_type_payment))
        async def select_ref_money_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            work_id = data.get('now_create_work')

            await self.managerdb.update_to_work(work_id=work_id, type_payment=message.text)

            work = await self.managerdb.get_work(work_id=work_id)

            text = 'Введите сумму за реферельную систему с каждого человека:'
            keyboard = self.reply_keyboards.select_ref_money

            await state.set_state(state=AdminStates.Select_ref_money)
            
            await message.answer(text=text, reply_markup=keyboard)
        
        @self.message(F.text.isdigit(), StateFilter(AdminStates.Select_ref_money))
        async def finish_create_work_hanlder(message: Message, state: FSMContext):
            data = await state.get_data()
            work_id = data.get('now_create_work')

            print(work_id)

            await self.managerdb.update_to_work(work_id=work_id, ref_money=int(message.text))
            await self.managerdb.update_to_work(work_id=work_id, ready_work=True)

            work = await self.managerdb.get_work(work_id=work_id)

            text_edit = 'Вы создали работу. Сейчас я перенапавлю вас в настройки работы.'
            keyboard = self.reply_keyboards.remove

            text = 'Нажмите чтобы перейти в настройки работы.'

            inline_keyboard = self.inline_keyboards.select_create_work(work=work)

            await state.set_state(state=AdminStates.Main_Menu)
            
            await message.answer(text=text_edit, reply_markup=keyboard)

            await message.answer(text=text, reply_markup=inline_keyboard)

        

        async def survey_distribution_turnout(work_id: str, bot: Bot):
            work = await self.managerdb.get_work(work_id=work_id)
            if work.workers:
                users = await self.managerdb.get_users(user_id_list=work.workers)
                text = 'Вы были на рабочем месте?'
                inline_keyboard = self.inline_keyboards.survey_distribution_turnout(work_id=work_id)

                for user in users:
                    await bot.send_message(chat_id=user.chat_id, text=text, reply_markup=inline_keyboard)
                print('sdgsdg')

        @self.callback_query(Pagination.filter(F.action.in_(['select_work'])), StateFilter(AdminStates.Main_Menu))
        async def work_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):

            work_id = callback_data.page
            work = await self.managerdb.get_work(work_id=work_id)
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')


            users = []
            if work.workers:
                users = await self.managerdb.get_users(user_id_list=work.workers)
            

            text = work.info_for_admin(users=users, bus_stop_list=bus_stop_list)
            inline_keyboard = self.inline_keyboards.work(work=work)

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(Pagination.filter(F.action == 'generator_workers_list_work'), StateFilter(AdminStates.Main_Menu))
        async def generator_workers_list_work_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            work_id = callback_data.page
            work = await self.managerdb.get_work(work_id=work_id)
            bus_stop_list = await self.managerdb.get_const(document_id=config('ID_BUS_STOPS'), key='bus_stop_list')
            phone = await self.managerdb.get_const(document_id=config('ID_CONTACTS'), key='phone')

            users = []
            if work.workers:
                users = await self.managerdb.get_users(user_id_list=work.workers)

            text = work.generator_lis_workers(users=users, bus_stop_list=bus_stop_list, phone=phone)
            
            inline_keyboard = self.inline_keyboards.generator_list_workers(work_id=work_id)

            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            
        
        @self.callback_query(Pagination.filter(F.action == 'public_message_work'), StateFilter(AdminStates.Main_Menu))
        async def public_message_work_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):

            work_id = callback_data.page
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
            if work.public_message_id:
                try:
                    msg = await call.message.bot.edit_message_text(
                            chat_id=public_channel_id,
                            message_id=work.public_message_id,
                            text=text,
                            reply_markup=keyboard_for_public_message)
                except: 
                    msg = await call.message.bot.send_message(
                        chat_id=public_channel_id,
                        text=text,
                        reply_markup=keyboard_for_public_message)
            else:
                msg = await call.message.bot.send_message(
                    chat_id=public_channel_id,
                    text=text,
                    reply_markup=keyboard_for_public_message)

            if msg:
                await self.managerdb.update_to_work(work_id=work_id, public_message_id=msg.message_id)
                await call.answer(text='Пост выложен успешно.', cache_time=5)

            await work_handler(call=call, state=state, callback_data=callback_data)

            
        
        @self.callback_query(CustomCallData.filter(F.action.in_(['transactions_wallet_workers'])), StateFilter(AdminStates.Main_Menu))
        async def transactions_wallet_workers_handler(call: CallbackQuery, state: FSMContext, callback_data: CustomCallData, old_message: bool = True):
            work_id = callback_data.item_id
            work = await self.managerdb.get_work(work_id=work_id)

            user = await self.managerdb.get_user(chat_id=call.message.chat.id)
            len_list = 6
            max_page = (len(work.transaction_wallets) + len_list - 1) // len_list - 1

            page = 0
            if callback_data:
                page = int(callback_data.page)

            transactions = await self.managerdb.get_transactions(trans_id_list=work.transaction_wallets[page*len_list:(page+1)*len_list])

            text = f'<b>Транзакци(ЗП + Реф):</b>\n\n{f"({page+1}/{max_page})" if max_page > 1 else ""}'

            inline_keyboard = self.inline_keyboards.transaction_list_work(transactions=transactions, work_id=work_id, page=page, max_page=max_page)

            with suppress(TelegramBadRequest):
                await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            await call.answer()
        
        @self.callback_query(CustomCallData.filter(F.action == 'select_transaction'), StateFilter(AdminStates.Main_Menu))
        async def select_transaction_work_handler(call: CallbackQuery, state:FSMContext, callback_data: Pagination):
            trans_id = callback_data.user_id
            work_id = callback_data.item_id
            page = int(callback_data.page)
            transaction: Transaction = await self.managerdb.get_transaction(trans_id=trans_id)

            text = transaction.all_info_for_work
            inline_keyboard = self.inline_keyboards.info_transaction_work(work_id=work_id, page=page)
            
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            await call.answer()

        @self.callback_query(CustomCallData.filter(F.action.in_(['payments_ref_to_wallet'])), StateFilter(AdminStates.Main_Menu))
        async def payments_ref_to_wallet_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination, old_message: bool = True):
            work_id = callback_data.item_id
            work = await self.managerdb.get_work(work_id=work_id)

            page_num = int(callback_data.page)
            max_page = len(work.ref_salaries) - 1
            
            if page_num < 0:
                page = max_page
            elif page_num > max_page:
                page = 0
            else:
                page = page_num
            
            if work.ref_salaries:
                user = await self.managerdb.get_user(chat_id=list(map(int, work.ref_salaries.keys()))[page])
                info_user = user.info_for_trans_to_wallet(salary=work.ref_salaries[str(user.chat_id)])
                sum_ref_sal = work.sum_ref_salaries
                text = f'<b>Расчет рефералки</b>(Оставшаяся сумма - {sum_ref_sal}):\n\n{info_user}\n\n{page+1}/{max_page+1}'
            else:
                text = 'Список пуст.'
                user = None

            inline_keyboard = self.inline_keyboards.ref_salaries_workers(user=user, page=page, work=work)
            await call.answer()
            if old_message:
                with suppress(TelegramBadRequest):
                        await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await call.message.answer(text=text, reply_markup=inline_keyboard)
        
        @self.callback_query(CustomCallData.filter(F.action.in_(['payment_ref_to_wallet_worker'])), StateFilter(AdminStates.Main_Menu))
        async def payment_to_wallet_worker_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            chat_id = int(callback_data.user_id)
            work_id = callback_data.item_id
            
            user = await self.managerdb.get_user(chat_id=chat_id)
            work = await self.managerdb.get_work(work_id=work_id)

            trans_money = work.ref_salaries[str(chat_id)]

            transaction = await self.managerdb.create_transaction(data=call.message, for_user_id=chat_id, money=trans_money, type_id=4, work=work)

            await self.managerdb.add_to_work(work_id=work_id, transaction_wallets=transaction.trans_id)
            await self.managerdb.del_to_object_work(work_id=work_id, update={f'ref_salaries.{chat_id}': ''})

            await self.managerdb.update_user_data(chat_id=chat_id, update=dict(ref_money=user.ref_money + trans_money))
            await self.managerdb.add_user_data(chat_id=chat_id, update=dict(awaiting_ref_payments=transaction.trans_id))
            await self.managerdb.add_user_data(chat_id=chat_id, update=dict(history_wallet=transaction.trans_id))

            text = f'Проведена транзакция - <code>{transaction.trans_id}</code> на сумму {transaction.money}₽ от {transaction.from_user_id} для {chat_id} в {transaction.date}'
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text=text)

            text_for_user = f'<code>Проведена транзакция - {transaction.trans_id}</code> на сумму {transaction.money}₽ в {transaction.date}</code>'
            with suppress(TelegramBadRequest):
                await call.message.bot.send_message(chat_id=chat_id, text=text_for_user)

            await payments_ref_to_wallet_handler(call=call, state=state, callback_data=callback_data, old_message=False)
        
        @self.callback_query(CustomCallData.filter(F.action.in_(['payments_to_wallet'])), StateFilter(AdminStates.Main_Menu))
        async def payments_to_wallet_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination, old_message: bool = True):
            work_id = callback_data.item_id
            work = await self.managerdb.get_work(work_id=work_id)

            page_num = int(callback_data.page)
            max_page = len(work.estimated_salaries) - 1
            
            if page_num < 0:
                page = max_page
            elif page_num > max_page:
                page = 0
            else:
                page = page_num
            
            if work.estimated_salaries:
                user = await self.managerdb.get_user(chat_id=list(map(int, work.estimated_salaries.keys()))[page])
                info_user = user.info_for_trans_to_wallet(salary=work.estimated_salaries[str(user.chat_id)])
                sum_est_sal = work.sum_estimated_salaries
                text = f'<b>Расчет на кошельки без рефералки</b>(Оставшаяся сумма - {sum_est_sal}):\n\n{info_user}\n\n{page+1}/{max_page+1}'
            else:
                text = 'Список пуст.'
                user = None

            inline_keyboard = self.inline_keyboards.estimated_salaries_workers(user=user, page=page, work=work)
            await call.answer()
            if old_message:
                with suppress(TelegramBadRequest):
                        await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await call.message.answer(text=text, reply_markup=inline_keyboard)

        @self.callback_query(CustomCallData.filter(F.action.in_(['payment_to_wallet_worker'])), StateFilter(AdminStates.Main_Menu))
        async def payment_to_wallet_worker_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            chat_id = int(callback_data.user_id)
            work_id = callback_data.item_id
            
            user = await self.managerdb.get_user(chat_id=chat_id)
            work = await self.managerdb.get_work(work_id=work_id)

            trans_money = work.estimated_salaries[str(chat_id)]

            transaction = await self.managerdb.create_transaction(data=call.message, for_user_id=chat_id, money=trans_money, type_id=0, work=work)

            await self.managerdb.add_to_work(work_id=work_id, transaction_wallets=transaction.trans_id)
            await self.managerdb.del_to_object_work(work_id=work_id, update={f'estimated_salaries.{chat_id}': ''})

            await self.managerdb.update_user_data(chat_id=chat_id, update=dict(wallet=user.wallet + trans_money))
            await self.managerdb.add_user_data(chat_id=chat_id, update=dict(awaiting_payments=transaction.trans_id))
            await self.managerdb.add_user_data(chat_id=chat_id, update=dict(history_wallet=transaction.trans_id))

            text = f'Проведена транзакция - <code>{transaction.trans_id}</code> на сумму {transaction.money}₽ от {transaction.from_user_id} для {chat_id} в {transaction.date}'
            with suppress(TelegramBadRequest):
                await call.message.edit_text(text=text)

            text_for_user = f'<code>Проведена транзакция - {transaction.trans_id}</code> на сумму {transaction.money}₽ в {transaction.date}</code>'
            with suppress(TelegramBadRequest):
                await call.message.bot.send_message(chat_id=chat_id, text=text_for_user)

            await payments_to_wallet_handler(call=call, state=state, callback_data=callback_data, old_message=False)


        @self.callback_query(CustomCallData.filter(F.action.in_(['turnout_worker'])), StateFilter(AdminStates.Main_Menu))
        async def turnout_worker_list_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination, old_message: bool = True):
            work_id = callback_data.item_id
            work = await self.managerdb.get_work(work_id=work_id)

            len_list = 6
            page_num = int(callback_data.page)
            max_page = (len(work.workers) + len_list - 1) // len_list - 1

            if page_num < 0:
                page = max_page
            elif page_num > max_page:
                page = 0
            else:
                page = page_num

            users = await self.managerdb.get_users(user_id_list=work.workers[page*len_list:(page+1)*len_list])
            text = '<b>Проставь явки и сделай расчёт</b>:'
            inline_keyboard = self.inline_keyboards.turnount_worker_list(users=users, page=page, work=work, max_page=max_page)
            await call.answer()
            if old_message:
                with suppress(TelegramBadRequest):
                        await call.message.edit_text(text=text, reply_markup=inline_keyboard)
            else:
                await call.message.answer(text=text, reply_markup=inline_keyboard)


        @self.callback_query(CustomCallData.filter(F.action.in_(['calculation_salaries_workers'])), StateFilter(AdminStates.Main_Menu))
        async def calculation_salaries_workers_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            work_id = callback_data.item_id
            work = await self.managerdb.get_work(work_id=work_id)
            users = await self.managerdb.get_users(user_id_list=work.workers)
            if work.worker_turnout:
                estimated_salaries, ref_salaries, sum_ref, all_vendor_salaries, profit, salaries_num = work.calculation_salaries_workers(users=users)

                text=f'<b>Расчет произведен:</b>\nОбщая сумма от поставщика - {all_vendor_salaries}₽\nОбщая сумма выплат - {salaries_num}₽\nРефералок на - {sum_ref}₽\nЗаработаем - {profit}₽'
                
                await self.managerdb.update_to_work(work_id=work_id, estimated_salaries=estimated_salaries,
                                                    sum_ref=sum_ref, all_vendor_salaries=all_vendor_salaries,
                                                    profit=profit, ref_salaries=ref_salaries)
                await call.answer()
                await call.message.edit_text(text=text, reply_markup=None)

                await turnout_worker_list_handler(call=call, state=state, callback_data=callback_data, old_message=False)
            else:
                await call.answer(text='Проставьте явки.')

            

        @self.callback_query(CustomCallData.filter(F.action.in_(['switch_turnout_worker'])), StateFilter(AdminStates.Main_Menu))
        async def switch_turnout_worker_list_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            work_id = callback_data.item_id
            user_id = int(callback_data.user_id)
            work = await self.managerdb.get_work(work_id=work_id)

            if user_id in work.worker_turnout:
                await self.managerdb.del_to_work(work_id=work_id, worker_turnout=user_id)
            else:
                await self.managerdb.add_to_work(work_id=work_id, worker_turnout=user_id)

            await turnout_worker_list_handler(call=call, state=state, callback_data=callback_data)


        @self.callback_query(Pagination.filter(F.action == 'switch_finish_work'), StateFilter(AdminStates.Main_Menu))
        async def switch_finish_work_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            work_id = callback_data.page
            work = await self.managerdb.get_work(work_id=work_id)
            await self.managerdb.update_to_work(work_id=work_id, finish_work=False if work.finish_work else True)

            await call.answer()
            await work_handler(call=call, state=state, callback_data=callback_data)

        
        @self.callback_query(Pagination.filter(F.action == 'switch_set_workers'), StateFilter(AdminStates.Main_Menu))
        async def switch_set_workers_to_work_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            work_id = callback_data.page
            work = await self.managerdb.get_work(work_id=work_id)
            await self.managerdb.update_to_work(work_id=work_id, set_workers=False if work.set_workers else True)

            await call.answer()
            await work_handler(call=call, state=state, callback_data=callback_data)
        
        @self.callback_query(Pagination.filter(F.action == 'delete_work'), StateFilter(AdminStates.Main_Menu))
        async def back_to_works_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            work_id = callback_data.page

            date = await self.managerdb.delete_work(work_id=work_id)
            callback_data.page = str(date)
            await call.answer()
            await works_handler(call=call, state=state, callback_data=callback_data)
        
        @self.callback_query(Pagination.filter(F.action == 'back_to_works'), StateFilter(AdminStates.Main_Menu))
        async def back_to_works_handler(call: CallbackQuery, state: FSMContext, callback_data: Pagination):
            await call.answer()
            await works_handler(call=call, state=state, callback_data=callback_data)
        
        @self.callback_query(F.data == 'back_to_workdays', StateFilter(AdminStates.Main_Menu))
        async def back_to_workdays_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            await work_days_handler(call=call, state=state)
        
        @self.callback_query(F.data == 'back_to_job_list', StateFilter(AdminStates.Main_Menu))
        async def back_to_job_list_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            await job_list_handler(message=call.message, state=state, message_id=call.message.message_id)
        
        @self.callback_query(F.data == 'close_job_list', StateFilter(AdminStates.Main_Menu))
        async def close_job_list_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text='Список работы закрыт', reply_markup=None)
            await main_menu_handler(message=call.message, state=state)
        
        @self.callback_query(F.data == 'close_users_menu', StateFilter(AdminStates.Main_Menu))
        async def close_job_list_handler(call: CallbackQuery, state: FSMContext):
            await call.answer()
            with suppress(TelegramBadRequest):
                    await call.message.edit_text(text='Список меню пользователей закрыт', reply_markup=None)
            await main_menu_handler(message=call.message, state=state)