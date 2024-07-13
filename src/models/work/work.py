from models import User
from typing import List, Dict
from datetime import datetime


class Work:
    work_id: str#
    header: str#
    typing: str#
    date: str#
    day_ru: str#
    day_en: str#
    salary: int#
    vendor_salary: int#
    ref_money: dict
    workers: list#
    worker_turnout: list#
    finish_work: bool#
    max_workers: int#
    bus_info: str#
    age_limit: int#
    departure_time: str#
    start_work_time: str#
    end_work_time: str#
    type_payment: str
    bus_photo_id: int#
    set_workers: bool#
    public_message_id: int#
    public_bus_message_id: int#
    transaction_wallets: dict#
    payments: dict#
    lunch: bool#
    ready_work: bool
    estimated_salaries: dict
    all_vendor_salaries: int
    sum_ref: int
    profit: int
    self_representations: list

    def __init__(self, data: dict) -> None:
        self.data = data

    def __getattr__(self, name: str) -> any:
        '''
        name: work_id: str, header: str, typing: str, date: int, day_ru:str, day_en: str,
        salary: int, workers: list, max_workers: int, bus_info: str, age_limit: int,
        departure_time: str, start_work_time: str, end_work_time: str, type_payment: str,
        bus_photo_id: int, set_workers: bool, public_message_id: int, payments: list,
        lunch: bool, ready_work: bool
        '''
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(f"'Work' object has no attribute '{name}'")

    def __str__(self) -> str:
        """String representation of the work"""
        return f"Work {self.header} (date={self.date})"
    
    def info_for_user(self, users: List[User], bus_stop_list: List[str]) -> str:
        dt = str(self.date).split(' ')[0]
        text = ''
        if not self.set_workers:
            text = f'Набор закрыт. Инфрормация ниже для тех, кто записался:\n\n'

        text += f'📌<b>{self.header}</b>\n\nНа {dt}({self.day_ru}) требуются разнорабочие от {self.age_limit} лет ‼️\n'
        text += f'⏰С {self.start_work_time} до {self.end_work_time}\n'
        text += f'💸Оплата {self.salary} руб. день\n'
        text += f'🕰Выплаты: {self.type_payment}\n'
        if self.lunch:
            text += f'🍜Имеется обед\n'
        text += f'🚐Выезд в {self.departure_time} с ткацкого.\n'
        if users and self.workers:
            if self.finish_work and self.worker_turnout:
                text += f'\n✅Были данные люди:\n'
                turnout_users = []
                for user in users:
                    if user.chat_id in self.worker_turnout:
                        turnout_users.append(user.chat_id)
                        text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]} - ✅\n'
                if len(turnout_users) != len(self.workers):
                    text += '\n⚠️Не было:\n'
                    for worker_id in self.workers:
                        if worker_id not in turnout_users:
                            text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]} - ❌\n'
            else:
                text += f'\n‼️Записаны данные люди(забронировано - {len(users)}/{self.max_workers}):\n'
                for user in users:
                    text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]}\n'
        
        text += '\n📍С собой обязательно сапоги и перчатки\n\n'
        text += '❓Если есть вопросы, пишите - @geka_support'

        return text
    
    def info_for_admin(self, users: List[User], bus_stop_list: List[str]) -> str:
        dt = str(self.date).split(' ')[0]
        text = ''
        if not self.set_workers:
            text = f'Набор закрыт. Инфрормация ниже для тех, кто записался:\n\n'

        text += f'📌<b>{self.header}</b>\n\nНа {dt}({self.day_ru}) требуются разнорабочие от {self.age_limit} лет ‼️\n'
        text += f'⏰С {self.start_work_time} до {self.end_work_time}\n'
        text += f'💸Оплата {self.salary} руб. день\n'
        text += f'🕰Выплаты: {self.type_payment}\n'
        if self.lunch:
            text += f'🍜Имеется обед\n'
        text += f'🚐Выезд в {self.departure_time} с ткацкого.\n'
        if users and self.workers:
            if self.finish_work and self.worker_turnout:
                text += f'\n✅Были данные люди:\n'
                turnout_users = []
                for user in users:
                    if user.chat_id in self.worker_turnout:
                        turnout_users.append(user.chat_id)
                        text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]} - ✅\n'
                if len(turnout_users) != len(self.workers):
                    text += '\n⚠️Не было:\n'
                    for worker_id in self.workers:
                        if worker_id not in turnout_users:
                            text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]} - ❌\n'
            else:
                text += f'\n‼️Записаны данные люди(забронировано - {len(users)}/{self.max_workers}):\n'
                for user in users:
                    text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]}\n'

        return text

    def info_for_channel(self, users: List[User], bus_stop_list: List[str]) -> str:
        dt = str(self.date).split(' ')[0]
        text = ''
        if not self.set_workers:
            text += f'Набор закрыт. Инфрормация ниже для тех, кто записался:\n\n'

        text += f'📌<b>{self.header}</b>\n\nНа {dt}({self.day_ru}) требуются разнорабочие от {self.age_limit} лет ‼️\n'
        text += f'⏰С {self.start_work_time} до {self.end_work_time}\n'
        text += f'💸Оплата {self.salary} руб. день\n'
        text += f'🕰Выплаты: {self.type_payment}\n'
        if self.lunch:
            text += f'🍜Имеется обед\n'
        text += f'🚐Выезд в {self.departure_time} с ткацкого.\n'
        if users and self.workers:
            if self.finish_work and self.worker_turnout:
                text += f'\n✅Были данные люди:\n'
                turnout_users = []
                for user in users:
                    if user.chat_id in self.worker_turnout:
                        turnout_users.append(user.chat_id)
                        text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]} - ✅\n'
                if len(turnout_users) != len(self.workers):
                    text += '\n⚠️Не было:\n'
                    for worker_id in self.workers:
                        if worker_id not in turnout_users:
                            text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]} - ❌\n'
            else:
                text += f'\n‼️Записаны данные люди(забронировано - {len(users)}/{self.max_workers}):\n'
                for user in users:
                    text += f'{user.get_names}, {bus_stop_list[user.bus_stop_id]}\n'
        text += f'\n<code>Последнее обновление списка: {datetime.now().strftime("%H:%M:%S")}</code>'
        return text

    def generator_lis_workers(self, users: List[User], bus_stop_list: List[str], phone: str) -> str:
        text = 'Список пуст.'
        if users and self.workers:
            text = f'{phone}\n\n'
            for k, user in enumerate(users, 1):
                if self.finish_work and self.worker_turnout:
                    pass
                else:
                    text += f'{k}) {user.get_names}, {bus_stop_list[user.bus_stop_id]}\n'
    
        return text
    
    def calculation_salaries_workers(self, users: List[User]) -> dict:
        if self.worker_turnout:
            users = {user.chat_id: user for user in users}
            salaries = {}
            ref_salaries = {}
            sum_ref = 0
            all_vendor_salaries = len(self.worker_turnout) * self.vendor_salary
            profit = len(self.worker_turnout) * (self.vendor_salary - self.salary)
            salaries_num = 0

            for worker_id in self.worker_turnout:
                salaries[str(worker_id)] = self.salary
                salaries_num += self.salary
                inv_user_id = users[worker_id].invited_user_id
                if inv_user_id:
                    ref_salaries[str(inv_user_id)] = ref_salaries.get(str(inv_user_id), 0) + self.ref_money
                    sum_ref += 200
            
            profit -= sum_ref
            salaries_num += sum_ref

            self.data['ref_salaries'] = ref_salaries
            self.data['estimated_salaries'] = salaries
            self.data['profit'] = profit
            self.data['all_vendor_salaries'] = all_vendor_salaries
            self.data['sum_ref'] = sum_ref

            return self.estimated_salaries, ref_salaries, sum_ref, all_vendor_salaries, profit, salaries_num
    
    @property
    def sum_estimated_salaries(self):
        return sum([k for k in self.estimated_salaries.values()])
    
    @property
    def sum_ref_salaries(self):
        return sum([k for k in self.ref_salaries.values()])