from datetime import datetime
from decouple import config
from typing import Dict, List

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models import Admin, Transaction, User, Work, WorkDay

from .user_keyboards import Pagination


class CustomCallData(CallbackData, prefix='custom'):
    action: str
    page: str | int
    item_id: str | int
    user_id: str | int

class DayCallData(CallbackData, prefix='day'):
    action: str
    page: str | int
    item_id: str | int

class UserCallData(CallbackData, prefix='user'):
    action: str
    page: str | int
    user_id: str | int

class ReplyAuthAdminKeyboards:
    def __init__(self) -> None:
        ...

    @property
    def secret_key(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Назад')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Введи секретный ключ"
        )
        return markup
    
    @property
    def password(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Назад')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Введи пароль"
        )
        return markup
    
    @property
    def input_name(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Назад')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Введи имя"
        )
        return markup
    
    @property
    def to_admin_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Админ-панель')],
                    [KeyboardButton(text='Назад')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Нажми на кнопку"
        )
        return markup
    
    @property
    def to_main_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Главное меню')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Перейди в главное меню"
        )
        return markup
    
    @property
    def remove(self) -> ReplyKeyboardRemove:
        markup = ReplyKeyboardRemove()
        return markup

class InlineAdminKeyboards:
    def __init__(self) -> None:
        ...
    
    @property
    def cancel_search_users(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back_to_users_menu', page=0).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    @property
    def statistics_menu(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Статистика явок', callback_data='calendar_turnout_users')],
                    [InlineKeyboardButton(text='Закрыть', callback_data='close_statistics_menu')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def keyboard_for_public_message(self, work_id: int, url: str) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Записаться', url=url)]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    def wallet_transaction_user(self, page: int, user_id: int):
        keyboard = [[InlineKeyboardButton(text='Отменить', callback_data=UserCallData(action='cancel_transaction', page=page, user_id=user_id).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def profile_user(self, user: User, page: int) -> InlineKeyboardMarkup:
        ban_text = 'Разбан' if user.ban else 'Бан'
        
        keyboard = [[InlineKeyboardButton(text='Транзакции', callback_data=UserCallData(action='transactions_user', page=page, user_id=user.chat_id).pack()),
                     InlineKeyboardButton(text='Операция', callback_data=UserCallData(action='wallet_transaction_user', page=page, user_id=user.chat_id).pack())],
                    [InlineKeyboardButton(text='Забанить', callback_data=UserCallData(action='switch_ban_user', page=page, user_id=user.chat_id).pack()),
                     InlineKeyboardButton(text='Удалить', callback_data=UserCallData(action='delete_user', page=page, user_id=user.chat_id).pack())],
                    [InlineKeyboardButton(text='Назад', callback_data=Pagination(action='users_list', page=page).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    def users_list(self, users: List[User], max_page: int, page: int = 0, len_list: int = 6) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if users:
            for user in users:
                builder.row(InlineKeyboardButton(text=user.get_names, callback_data=UserCallData(action='select_user', page=page, user_id=user.chat_id).pack()), width=1)
        
        if max_page:
            builder.row(InlineKeyboardButton(text='◀', callback_data=Pagination(action='users_list', page=page-1).pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back_to_users_menu', page=0).pack()))
            builder.add(InlineKeyboardButton(text='▶', callback_data=Pagination(action='users_list', page=page+1).pack()))
        else:
            builder.row(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back_to_users_menu', page=0).pack()), width=1)
        
        return builder.as_markup()
    
    def payments_woker_list(self, users: List[User], page: int = 0, len_list: int = 6) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if users:
            for user in users:
                builder.row(InlineKeyboardButton(text=user.get_names, callback_data=UserCallData(action='select_user', page=page, user_id=user.chat_id).pack()), width=1)

        if (len(users) == len_list and not page) or page:
            builder.row(InlineKeyboardButton(text='◀', callback_data=Pagination(action='users_list', page=page-1).pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back_to_users_menu', page=0).pack()))
            builder.add(InlineKeyboardButton(text='▶', callback_data=Pagination(action='users_list', page=page+1).pack()))
        else:
            builder.row(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back_to_users_menu', page=0).pack()), width=1)
        
        return builder.as_markup()

    @property
    def users_menu(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Список пользователей', callback_data=Pagination(action='users_list', page=0).pack())],
                    [InlineKeyboardButton(text='Поиск', callback_data='search_users'),
                     InlineKeyboardButton(text='Фильтр', callback_data='filters_search_users')],
                    [InlineKeyboardButton(text='Закрыть', callback_data='close_users_menu')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard


    @property
    def selection_menu(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Вакансии', callback_data='vacancies'),
                     InlineKeyboardButton(text='Работа', callback_data='active_work_days')],
                    [InlineKeyboardButton(text='Закрыть', callback_data='close_job_list')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    def work_days(self, workdays: List[WorkDay]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if workdays:
            for workday in workdays:
                builder.row(InlineKeyboardButton(text=workday.info_for_button_user(), callback_data=Pagination(action='select_workday', page=str(workday.date)).pack()), width=1)
        
        builder.row(InlineKeyboardButton(text='Добавить день работы', callback_data='create_workday'), width=2)
        builder.add(InlineKeyboardButton(text='Архив дней', callback_data=DayCallData(action='archive_workdays', page=0, item_id='null').pack()))

        builder.row(InlineKeyboardButton(text='Назад', callback_data='back_to_job_list'), width=1)
        return builder.as_markup()

    def works(self, works: List[Work], date: datetime, archived: bool) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        text = 'Работы нет.'
        if works:
            dt = works[0].date
            text = f'Работа на {works[0].day_ru}({dt}):'
            for work in works:
                builder.row(InlineKeyboardButton(text=work.header, callback_data=Pagination(action='select_work', page=work.work_id).pack()), width=1)

        builder.row(InlineKeyboardButton(text='Добавить работу', callback_data=Pagination(action='create_work', page=date).pack()), width=2)
        if not archived:
            builder.add(InlineKeyboardButton(text='Архивировать день', callback_data=Pagination(action='archive_workday', page=date).pack()))
        else:
            builder.add(InlineKeyboardButton(text='Разархивировать день', callback_data=Pagination(action='unarchive_workday', page=date).pack()))
        builder.row(InlineKeyboardButton(text='Назад', callback_data='back_to_workdays'), width=1)
        return text, builder.as_markup()
    
    def work(self, work: Work) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        public_message_text = 'Переопубликовать' if work.public_message_id else 'Опубликовать'
        builder.row(InlineKeyboardButton(text=public_message_text, callback_data=Pagination(action='public_message_work', page=work.work_id).pack()), width=1)

        if work.workers:
            builder.row(InlineKeyboardButton(text='Список', callback_data=Pagination(action='generator_workers_list_work', page=work.work_id).pack()), width=1)
        

        if not work.set_workers:
            finish_work_text = 'Продолжить день' if work.finish_work else 'Закончить день'
            builder.row(InlineKeyboardButton(text=finish_work_text, callback_data=Pagination(action='switch_finish_work', page=work.work_id).pack()), width=1)

        if work.finish_work:
            if work.workers:
                turnount_worker_text = 'Явки'
                builder.row(InlineKeyboardButton(text=turnount_worker_text, callback_data=CustomCallData(action='turnout_worker', page=0, item_id=work.work_id, user_id='null').pack()), width=3)

            if work.estimated_salaries:
                payments_text = 'Раскид ЗП'
                builder.add(InlineKeyboardButton(text=payments_text, callback_data=CustomCallData(action='payments_to_wallet', page=0, item_id=work.work_id, user_id='null').pack()))
            if work.ref_salaries:
                payments_ref_text = 'Раскид Реф.'
                builder.add(InlineKeyboardButton(text=payments_ref_text, callback_data=CustomCallData(action='payments_ref_to_wallet', page=0, item_id=work.work_id, user_id='null').pack()))
        
            if work.transaction_wallets:
                turnount_worker_text = 'Транзакции'
                builder.row(InlineKeyboardButton(text=turnount_worker_text, callback_data=CustomCallData(action='transactions_wallet_workers', page=0, item_id=work.work_id, user_id='null').pack()), width=1)

        else:
            set_workers_text, set_workers_action = ('Закрыть набор', 'switch_set_workers') if work.set_workers else ('Открыть набор', 'switch_set_workers')
            builder.row(InlineKeyboardButton(text=set_workers_text, callback_data=Pagination(action=set_workers_action, page=work.work_id).pack()), width=1)
        builder.row(InlineKeyboardButton(text='Удалить работу', callback_data=Pagination(action='delete_work', page=work.work_id).pack()), width=1)

        dt = int(datetime.strptime(work.date, "%Y-%m-%d").timestamp())
        builder.row(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back_to_works', page=dt).pack()), width=1)
        return builder.as_markup()
    
    def back_to_workday(self, date: int) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_workday', page=date).pack())]]

        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def select_create_workday(self, workday: WorkDay) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Перейти', callback_data=Pagination(action='select_workday', page=workday.date).pack())],
                    [InlineKeyboardButton(text='Назад', callback_data='active_work_days')]]
        
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def select_create_work(self, work: Work) -> InlineKeyboardMarkup:
        dt = int(datetime.strptime(work.date, "%Y-%m-%d").timestamp())
        keyboard = [[InlineKeyboardButton(text='Войти', callback_data=Pagination(action='select_work', page=work.work_id).pack())],
                    [InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back_to_works', page=dt).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def generator_list_workers(self, work_id: int) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work_id).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def turnount_worker_list(self, users: List[User], page: int, work: Work, max_page: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        left_button = True if page > 0 else False
        for user in users:
            turnout = '✅' if user.chat_id in work.worker_turnout else '❌'
            builder.row(
                InlineKeyboardButton(
                    text=f'{turnout}{user.get_names}', callback_data=CustomCallData(action='switch_turnout_worker', page=page, item_id=work.work_id, user_id=user.chat_id).pack()),
                    width=1
                    )
        builder.row(
                InlineKeyboardButton(
                    text='Расчитать', callback_data=CustomCallData(action='calculation_salaries_workers', page=page, item_id=work.work_id, user_id='null').pack()),
                    width=1
                    )
        if left_button:
            builder.row(
                InlineKeyboardButton(text=user.get_names, callback_data=CustomCallData(action='turnout_worker', page=page-1, item_id=work.work_id, user_id='null').pack()),
                width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work.work_id).pack()))
        else:
            builder.row(
                InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work.work_id).pack()),
                width=2
                )
        if page < max_page:
            builder.add(
                InlineKeyboardButton(text=user.get_names, callback_data=CustomCallData(action='turnout_worker', page=page+1, item_id=work.work_id, user_id='null')))

        return builder.as_markup()
    
    @property
    def select_datetime_work(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Отменить', callback_data='cancel_create_workday')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def archive_workdays(self, archive_workdays: List[WorkDay], page: int, max_page: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if archive_workdays:
            for workday in archive_workdays:
                builder.row(InlineKeyboardButton(text=workday.info_for_button_user(), callback_data=Pagination(action='select_archive_workday', page=str(workday.date)).pack()), width=1)


        builder.row(InlineKeyboardButton(
            text='◀',
            callback_data=DayCallData(action='archive_workdays', page=page-1 if page > 0 else max_page, item_id='null').pack()),
            width=3
            )
        
        builder.add(InlineKeyboardButton(
            text='Назад',
            callback_data='active_work_days')
            )

        builder.add(InlineKeyboardButton(
            text='▶',
            callback_data=DayCallData(action='archive_workdays', page=page+1 if page < max_page else 0, item_id='null').pack())
            )

        return builder.as_markup()
    
    def ref_salaries_workers(self, user: User, page: int, work: Work) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if user:
            builder.row(InlineKeyboardButton(text='Скинуть', callback_data=CustomCallData(action='payment_ref_to_wallet_worker', page=page, item_id=work.work_id, user_id=user.chat_id).pack()), width=1)
            builder.row(InlineKeyboardButton(text='◀', callback_data=CustomCallData(action='payments_ref_to_wallet', page=page-1, item_id=work.work_id, user_id='null').pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work.work_id).pack()))
            builder.add(InlineKeyboardButton(text='▶', callback_data=CustomCallData(action='payments_ref_to_wallet', page=page+1, item_id=work.work_id, user_id='null').pack()))
        else:
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work.work_id).pack()))

        return builder.as_markup()
    
    def estimated_salaries_workers(self, user: User, page: int, work: Work) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if user:
            builder.row(InlineKeyboardButton(text='Скинуть', callback_data=CustomCallData(action='payment_to_wallet_worker', page=page, item_id=work.work_id, user_id=user.chat_id).pack()), width=1)
            builder.row(InlineKeyboardButton(text='◀', callback_data=CustomCallData(action='payments_to_wallet', page=page-1, item_id=work.work_id, user_id='null').pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work.work_id).pack()))
            builder.add(InlineKeyboardButton(text='▶', callback_data=CustomCallData(action='payments_to_wallet', page=page+1, item_id=work.work_id, user_id='null').pack()))
        else:
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work.work_id).pack()))

        return builder.as_markup()

    def transaction_list_work(self, transactions: List[Transaction], work_id: str, page: int = 0, max_page: int = 0) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()


        for trans in transactions:
            builder.row(InlineKeyboardButton(text=trans.info_for_work, callback_data=CustomCallData(action='select_transaction', page=page, item_id=work_id, user_id=trans.trans_id).pack()), width=1)
        
        if page > 0:
            builder.row(InlineKeyboardButton(text='◀', callback_data=CustomCallData(action='transactions_wallet_workers', page=page-1, item_id=work_id, user_id='null').pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work_id).pack()))
        else:
            builder.row(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='select_work', page=work_id).pack()), width=2)
        
        if page < max_page:
            builder.add(InlineKeyboardButton(text='▶', callback_data=CustomCallData(action='transactions_wallet_workers', page=page+1, item_id=work_id, user_id='null').pack()))

        return builder.as_markup()
    
    def info_transaction_work(self, work_id: str, page: int = 0):
        keyboard = [[InlineKeyboardButton(text='Назад', callback_data=CustomCallData(action='transactions_wallet_workers', page=page, item_id=work_id, user_id='null').pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    @property
    def payments_menu(self):
        keyboard = [[InlineKeyboardButton(text='Обычные ЗП', callback_data=UserCallData(action='payments_work', page=0, user_id='null').pack()),
                     InlineKeyboardButton(text='Рефки', callback_data=UserCallData(action='payments_ref', page=0, user_id='null').pack())],
                    [InlineKeyboardButton(text='Закрыть', callback_data='close_payments_menu')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def payments_ref_list(self, users: List[User], page: int = 0, len_list: int = 6) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if users:
            for user in users:
                builder.row(InlineKeyboardButton(text=f'{user.get_names} - {user.ref_money}₽ ({len(user.awaiting_ref_payments)})', callback_data=UserCallData(action='select_user_for_payments_ref', page=0, user_id=user.chat_id).pack()), width=1)

        if (len(users) == len_list and not page) or page:
            builder.row(InlineKeyboardButton(text='◀', callback_data=Pagination(action='payments_ref_work', page=page-1).pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data='back_to_payments_menu'))
            builder.add(InlineKeyboardButton(text='▶', callback_data=Pagination(action='payments_ref_work', page=page+1).pack()))
        else:
            builder.row(InlineKeyboardButton(text='Назад', callback_data='back_to_payments_menu'), width=1)
        
        return builder.as_markup()
    
    def payments_ref_user_list(self, admin: Admin, user: User, page: int, transactions: List[Transaction], payment_trans: List[Transaction] = None, len_list: int = 6) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for trans in transactions:
            check = ''
            if trans.trans_id in admin.assigned_invoices:
                check = '✅'
            builder.row(InlineKeyboardButton(
                text=f'{trans.money}₽ - {trans.date_work} {check}',
                callback_data=CustomCallData(action='switch_trans_worker_ref',
                page=page, user_id=user.chat_id, item_id=trans.trans_id).pack()),
                width=1
                )
        
        if admin.assigned_invoices:
            money = sum([float(trans.money) for trans in payment_trans if trans.for_user_id == user.chat_id])
            builder.row(InlineKeyboardButton(
                    text=f'Выплатить {money} ₽',
                    callback_data=CustomCallData(action='payment_worker_ref',
                    page=page, user_id=user.chat_id, item_id=money).pack()),
                    width=1
                    )
        
        if (len(transactions) == len_list and not page) or page:
            builder.row(InlineKeyboardButton(text='◀', callback_data=UserCallData(action='select_user_for_payments_ref', page=page-1, user_id=user.chat_id).pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data=UserCallData(action='payments_ref', page=0, user_id='null').pack()))
            builder.add(InlineKeyboardButton(text='▶', callback_data=UserCallData(action='select_user_for_payments_ref', page=page+1, user_id=user.chat_id).pack()))
        else:
            builder.row(InlineKeyboardButton(text='Назад', callback_data=UserCallData(action='payments_ref', page=0, user_id='null').pack()), width=1)
        
        return builder.as_markup()
    
    def cancel_payment_ref_worker(self, user: User, page: int) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Отменить', callback_data=UserCallData(action='select_user_for_payments_ref', page=page, user_id=user.chat_id).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def select_type_ref_payment(self, page: int, user_id: int) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Карта', callback_data=Pagination(action='type_payment_ref_select', page=2).pack()),
                     InlineKeyboardButton(text='Телефон', callback_data=Pagination(action='type_payment_ref_select', page=1).pack())],
                    [InlineKeyboardButton(text='Отменить', callback_data=UserCallData(action='select_user_for_payments_ref', page=page, user_id=user_id).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def payments_work_list(self, users: List[User], page: int = 0, len_list: int = 6) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if users:
            for user in users:
                builder.row(InlineKeyboardButton(text=f'{user.get_names} - {user.wallet}₽ ({len(user.awaiting_payments)})', callback_data=UserCallData(action='select_user_for_payments', page=0, user_id=user.chat_id).pack()), width=1)

        if (len(users) == len_list and not page) or page:
            builder.row(InlineKeyboardButton(text='◀', callback_data=Pagination(action='payments_work', page=page-1).pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data='back_to_payments_menu'))
            builder.add(InlineKeyboardButton(text='▶', callback_data=Pagination(action='payments_work', page=page+1).pack()))
        else:
            builder.row(InlineKeyboardButton(text='Назад', callback_data='back_to_payments_menu'), width=1)
        
        return builder.as_markup()
    
    def payments_user_list(self, admin: Admin, user: User, page: int, transactions: List[Transaction], payment_trans: List[Transaction] = None, len_list: int = 6) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        for trans in transactions:
            check = ''
            if trans.trans_id in admin.assigned_invoices:
                check = '✅'
            builder.row(InlineKeyboardButton(
                text=f'{trans.money}₽ - {trans.date_work} {check}',
                callback_data=CustomCallData(action='switch_trans_worker',
                page=page, user_id=user.chat_id, item_id=trans.trans_id).pack()),
                width=1
                )
        
        if admin.assigned_invoices:
            money = sum([float(trans.money) for trans in payment_trans if trans.for_user_id == user.chat_id])
            builder.row(InlineKeyboardButton(
                    text=f'Выплатить {money} ₽',
                    callback_data=CustomCallData(action='payment_worker',
                    page=page, user_id=user.chat_id, item_id=money).pack()),
                    width=1
                    )
        
        if (len(transactions) == len_list and not page) or page:
            builder.row(InlineKeyboardButton(text='◀', callback_data=UserCallData(action='select_user_for_payments', page=page-1, user_id=user.chat_id).pack()), width=3)
            builder.add(InlineKeyboardButton(text='Назад', callback_data=UserCallData(action='payments_work', page=0, user_id='null').pack()))
            builder.add(InlineKeyboardButton(text='▶', callback_data=UserCallData(action='select_user_for_payments', page=page+1, user_id=user.chat_id).pack()))
        else:
            builder.row(InlineKeyboardButton(text='Назад', callback_data=UserCallData(action='payments_work', page=0, user_id='null').pack()), width=1)
        
        return builder.as_markup()
    
    def cancel_payment_worker(self, user: User, page: int) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Отменить', callback_data=UserCallData(action='select_user_for_payments', page=page, user_id=user.chat_id).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    def survey_distribution_turnout(self, work_id: str) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Да', callback_data=UserCallData(action='self_turnout_worker', page='yes', user_id=work_id).pack()),
                     InlineKeyboardButton(text='Нет', callback_data=UserCallData(action='self_turnout_worker', page='no', user_id=work_id).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard


    def select_type_payment(self, page: int, user_id: int) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Карта', callback_data=Pagination(action='type_payment_select', page=2).pack()),
                     InlineKeyboardButton(text='Телефон', callback_data=Pagination(action='type_payment_select', page=1).pack())],
                    [InlineKeyboardButton(text='Отменить', callback_data=UserCallData(action='select_user_for_payments', page=page, user_id=user_id).pack())]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard



class ReplyAdminKeyboards:
    def __init__(self) -> None:
        ...
    
    @property
    def wallet_transaction_user(self):
        keyboard = [[KeyboardButton(text='Отменить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        return markup
    
    @property
    def admin_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='📢Реклама'),
                     KeyboardButton(text='💼Работа'),
                     KeyboardButton(text='👥Пользователи'),
                     KeyboardButton(text='🍜Выплаты')],
                    [KeyboardButton(text='📊Статистика'),
                     KeyboardButton(text='Назад'),
                     KeyboardButton(text='📦Другое'),]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        return markup

    
    @property
    def ads_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Назад')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        return markup

    
    @property
    def transaction_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Зарегестрироваться')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        return markup
    
    @property
    def test_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Добавить транзакцию'),
                     KeyboardButton(text='Добавить транзакцию'),
                     KeyboardButton(text='Добавить транзакцию'),],
                    [KeyboardButton(text='Добавить транзакцию'),
                     KeyboardButton(text='Добавить транзакцию')]
                    [KeyboardButton(text='Назад')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        return markup
    
    @property
    def other_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [
                    [KeyboardButton(text='📮Рассылка в боте')],

                    [KeyboardButton(text='Пост в канале(кнопки)'),
                     KeyboardButton(text='Пост в канале'),],

                    [KeyboardButton(text='Назад в меню')]
                    ]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
        return markup
    
    @property
    def to_main_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Главное меню')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Перейди в главное меню"
        )
        return markup
    
    @property
    def remove(self) -> ReplyKeyboardRemove:
        markup = ReplyKeyboardRemove()
        return markup
    
    @property
    def cancel(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Отменить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Введите данные сюда"
        )
        return markup

    @property
    def cancel_create_work(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Отменить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Введите данные сюда"
        )
        return markup
    
    @property
    def select_lunch_work(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Да'), KeyboardButton(text='Нет')],
                    [KeyboardButton(text='Отменить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите ответ"
        )
        return markup
    
    @property
    def select_departure_time_work(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='6:50')],
                    [KeyboardButton(text='Отменить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите заготовку или введите свое"
        )
        return markup
    
    @property
    def select_start_time_work(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='8:00')],
                    [KeyboardButton(text='Отменить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите заготовку или введите свое"
        )
        return markup
    
    @property
    def select_end_time_work(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='18:30')],
                    [KeyboardButton(text='Отменить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите заготовку или введите свое"
        )
        return markup
    
    @property
    def select_ref_money(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='200')],
                    [KeyboardButton(text='Отменить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите заготовку или введите свое"
        )
        return markup
    