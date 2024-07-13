from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from typing import Dict, List

from models import Transaction, WorkDay, Work

from datetime import datetime


class Pagination(CallbackData, prefix='pagination'):
    
    action: str | int
    page: str | int

class AuthInlineUserKeyboards:
    def __init__(self) -> None:
        ...
    
    def bus_stop_list(self, len_list: int, bus_stop_list: List[str], page_num: int = 0, action: str = None) -> InlineKeyboardMarkup:

        page = 0
        if action == 'prev':
            page = page_num - 1 if page_num > 0 else (len(bus_stop_list) + len_list - 1) // len_list - 1
        elif action == 'next':
            page = page_num + 1 if page_num < (len(bus_stop_list) + len_list - 1) // len_list - 1 else 0

        data = {bs: f'{i}' for i, bs in enumerate(bus_stop_list[page*len_list:(page+1)*len_list], page*len_list)}

        keyboard = self.custom_pagination(page=page, data=data)

        return keyboard, page

    def custom_pagination(self, page: int = 0, data: dict = None, can_back: bool = False) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if data:
            for text, action in data.items():
                builder.row(
                    InlineKeyboardButton(text=text, callback_data=Pagination(action='select', page=action).pack()),
                    width=1
                        )
        
        builder.row(InlineKeyboardButton(text='◀', callback_data=Pagination(action='prev', page=page).pack()), width=3)
        if can_back:
            builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back', page=page).pack()))
        builder.add(InlineKeyboardButton(text='▶', callback_data=Pagination(action='next', page=page).pack()))

        return builder.as_markup()

class AuthReplyUserKeyboards:
    def __init__(self) -> None:
        ...
    
    @property
    def auth(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Зарегистрироваться')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Нажмите на кнопку"
        )
        return markup
    
    @property
    def genders(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Мужчина'), KeyboardButton(text='Женщина')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите пол"
        )
        return markup
    
    @property
    def remove(self) -> ReplyKeyboardRemove:
        markup = ReplyKeyboardRemove()
        return markup

    @property
    def ref(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Пропустить')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Можете просто пропустить"
        )
        return markup
    
    @property
    def menu_path(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='Главное меню')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="хохо"
        )
        return markup



class ReplyUserKeyboards:
    def __init__(self) -> None:
        ...
    
    @property
    def main_menu(self) -> ReplyKeyboardMarkup:
        keyboard = [[KeyboardButton(text='📋Профиль'), KeyboardButton(text='💼Работа'), KeyboardButton(text='ℹИнформация')],
                    [KeyboardButton(text='⛑Поддержка'), KeyboardButton(text='📜Правила'), KeyboardButton(text='')]]
        markup = ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            input_field_placeholder="Выберите действие",
        )
        return markup
    
    @property
    def remove(self) -> ReplyKeyboardRemove:
        markup = ReplyKeyboardRemove()
        return markup


class Action(CallbackData, prefix='action'):
    action: str

class InlineUserKeyboards:
    def __init__(self) -> None:
        ...
    
    def bus_stop_list(self, len_list: int, bus_stop_list: List[str], page_num: int = 0, action: str = None, max_page: int = None) -> InlineKeyboardMarkup:

        page = 0
        if action == 'prev':
            page = page_num - 1 if page_num > 0 else (len(bus_stop_list) + len_list - 1) // len_list - 1
        elif action == 'next':
            page = page_num + 1 if page_num < (len(bus_stop_list) + len_list - 1) // len_list - 1 else 0

        data = {f'{i}': bs for i, bs in enumerate(bus_stop_list[page*len_list:(page+1)*len_list], page*len_list)}

        keyboard = self.custom_pagination(page=page, data=data, can_back=True, max_page=max_page)

        return keyboard, page
    
    @property
    def cancel_edit_profile(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Отменить', callback_data='cancel_edit_profile')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard


    def keyboard_for_public_message(self, work_id: int, url: str) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Записаться', url=url)]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    def info_project(self, link_public_channel: str, link_trans_channel: str) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='📰Основной канал📰', url=link_public_channel)],
                    [InlineKeyboardButton(text='💱Транзакции💱', url=link_trans_channel)]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    @property
    def profile(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='🔗Реф. ссылка', callback_data='ref_link'),
                     InlineKeyboardButton(text='Транзакции', callback_data='transactions')],
                    [InlineKeyboardButton(text='Редактировать', callback_data='edit_profile')],
                    [InlineKeyboardButton(text='Закрыть', callback_data='close_profile')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    @property
    def edit_profile(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='🎨ФИ', callback_data='edit_fullname'),
                     InlineKeyboardButton(text='🎂Возраст', callback_data='edit_age'),
                     InlineKeyboardButton(text='⚥Пол', callback_data='edit_gender')],

                    [InlineKeyboardButton(text='💳Карта', callback_data='edit_card_id'),
                     InlineKeyboardButton(text='📱Телефон', callback_data='edit_phone'),
                     InlineKeyboardButton(text='🚏Остановка', callback_data=Pagination(action='start', page=0).pack())],

                    [InlineKeyboardButton(text='Назад', callback_data='back_to_profile')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    @property
    def edit_gender_profile(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Мужчина', callback_data='select_men_gender'),
                     InlineKeyboardButton(text='Женщина', callback_data='select_women_gender')],
                    [InlineKeyboardButton(text='Отменить', callback_data='cancel_edit_profile')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    @property
    def job_list(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Вакансии', callback_data='vacancies'),
                     InlineKeyboardButton(text='Работа', callback_data='active_work_days')],
                    [InlineKeyboardButton(text='Закрыть', callback_data='close_job_list')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    @property
    def vacancies(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Назад', callback_data='back_to_job_list')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    
    

    def work_days(self, workdays: List[WorkDay]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if workdays:
            for workday in workdays:
                builder.row(InlineKeyboardButton(text=workday.info_for_button_user(), callback_data=Pagination(action='select_day_work', page=str(workday.date)).pack()), width=1)
        builder.row(InlineKeyboardButton(text='Назад', callback_data='back_to_job_list'), width=1)
        return builder.as_markup()

    def works(self, works: List[Work]) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        text = 'Работы нет.'
        if works:
            dt = works[0].date
            text = f'Работа на {works[0].day_ru}({dt}):'
            for work in works:
                builder.row(InlineKeyboardButton(text=work.header, callback_data=Pagination(action='select_work', page=str(work.work_id)).pack()), width=1)
        builder.row(InlineKeyboardButton(text='Назад', callback_data='back_to_workdays'), width=1)
        return text, builder.as_markup()
    
    def work(self, work: Work, chat_id: int, already_registration_work_id: bool) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if work.set_workers and (not already_registration_work_id or already_registration_work_id == work.work_id) and work.max_workers != len(work.workers):
            registration, action = ('Отписаться', 'unregistration_work') if chat_id in work.workers else ('Записаться', 'registration_work')
            builder.row(InlineKeyboardButton(text=registration, callback_data=Pagination(action=action, page=str(work.work_id)).pack()), width=1)
        dt = int(datetime.strptime(work.date, "%Y-%m-%d").timestamp())
        builder.row(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back_to_works', page=dt).pack()), width=1)
        return builder.as_markup()
    
    @property
    def ref_link(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Назад', callback_data='back_to_profile')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard
    
    @property
    def profile_info_transaction(self) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(text='Назад', callback_data='back_to_transactions')]]
        inline_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
        return inline_keyboard

    

    def transaction_list(self, transactions: List[Transaction], page: int = 0, max_page: int = 0) -> InlineKeyboardMarkup:
        transactions_data = {trans.trans_id: trans.info_for_user for trans in transactions}
        inline_keyboard = self.custom_pagination(page=page, max_page=max_page, data=transactions_data)
        return inline_keyboard
        
    
    def custom_pagination(self, page: int = 0, data: dict = None, can_back: bool = True, max_page: int = 0) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if data:
            for action, text in data.items():
                builder.row(
                    InlineKeyboardButton(text=text, callback_data=Pagination(action='select', page=action).pack()),
                    width=1
                        )
        
        if max_page > 1:
            builder.row(InlineKeyboardButton(text='◀', callback_data=Pagination(action='prev', page=page).pack()), width=3)
            if can_back:
                builder.add(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back', page=page).pack()))
            builder.add(InlineKeyboardButton(text='▶', callback_data=Pagination(action='next', page=page).pack()))
        else:
            if can_back:
                builder.row(InlineKeyboardButton(text='Назад', callback_data=Pagination(action='back', page=page).pack()), width=1)

        return builder.as_markup()