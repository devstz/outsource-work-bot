from ..transaction.transaction import Transaction
from datetime import datetime

class User:
    chat_id: int
    username: str
    first_name: str
    last_name: str
    date_registration: datetime
    date_ban: datetime
    gender: str
    age: int
    bus_stop_id: int
    phone: str
    ready_profile: bool
    invite_users: list
    invited_user_id: int
    invited_ref_id: str
    ref_id: str
    wallet: int
    awaiting_payments: list
    history_wallet: list
    ban: bool
    ref_money: int
    card_id: int

    def __init__(self, data: dict):
        '''
        attribute: chat_id: int, username: str, first_name: str, last_name: str, gender: str,
        age: int, bus_stop_id: int, phone: str, ready_profile: bool, invite_users: list,
        invited_user: int, working_day: list, wallet: dict, history_wallet: list, ban: bool,
        '''
        self.data = data

    def __getattr__(self, name: str) -> any:
        '''
        name: chat_id: int, username: str, first_name: str, last_name: str, gender: str,
        age: int, bus_stop_id: int, phone: str, ready_profile: bool, invite_users: list,
        invited_user: int, working_day: list, wallet: dict, history_wallet: list, ban: bool
        '''
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(f"'User' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value: any):
        if name == 'data':
            super().__setattr__(name, value)
        else:
            self.data[name] = value

    def __str__(self) -> str:
        """String representation of the user"""
        return f"User {self.username} (chat_id={self.chat_id})"
    
    @property
    def get_names(self) -> str:
        return f'{self.first_name} {self.last_name}'
    
    def profile(self, bus_stop_list: list) -> str:
        text = 'Профиль не готов.'
        if self.ready_profile == 'ready':
            text = f'👤 Профиль пользователя:\n\n'
            text += f'🎨 Имя: {self.first_name} {self.last_name}\n'
            text += f'⚥ Пол: {self.gender}\n'
            text += f'🎂 Возраст: {self.age}\n'
            text += f'🚏 Остановка: {bus_stop_list[self.bus_stop_id]}\n'
            text += f'📱 Телефон: <code>{self.phone}</code>\n'
            text += f'💳 Карта: <code>{self.card_id}</code>\n\n'
            text += f'💸 Деньги с рефки: {self.ref_money}\n'
            text += f'💳 Кошелек: {self.wallet} ₽\n\n'
            text += f'📢 Рефералка: <code>{self.ref_id}</code>\n'
            if self.invited_ref_id:
                text += f'🙋‍♂️ Подключенная рефералка: {self.invited_ref_id}\n'
            if len(self.invite_users):
                text += f'🤝 Пригласил пользователей: {len(self.invite_users)}\n'

        return text
    
    def profile_admin(self, bus_stop_list: list) -> str:
        text = 'Профиль не готов.'
        text = f'👤 Профиль пользователя:\n\n'
        text += f'Бан: {"✅" if self.ban else "❌"}\n'
        link = f'@{self.username}' if self.username else f"<a href='tg://user?id={self.chat_id}'>{self.chat_id}</a>"
        text += f"🆔: {link}\n"
        if self.ready_profile == 'ready':
            text += f'🎨 Имя: {self.first_name} {self.last_name}\n'
            text += f'⚥ Пол: {self.gender}\n'
            text += f'🎂 Возраст: {self.age}\n'
            text += f'🚏 Остановка: {bus_stop_list[self.bus_stop_id]}\n'
            text += f'📱 Телефон: {self.phone}\n'
            text += f'💳 Карта: {self.card_id}\n\n'
        text += f'💸 Деньги с рефки: {self.ref_money}\n'
        text += f'💵 Кошелек: {self.wallet} ₽\n\n'
        text += f'📢 Рефералка: <code>{self.ref_id}</code>\n'
        if self.invited_ref_id:
            text += f'🙋‍♂️ Подключенная рефералка: {self.invited_ref_id}\n'
        if len(self.invite_users):
            text += f'🤝 Пригласил пользователей: {len(self.invite_users)}\n'

        return text
    
    def get_transaction(self, page: int = 0, lengh_list: int = 5):
        history_wallet = self.history_wallet
        transactions_id_list = self.history_wallet[page*lengh_list:(page+1)*lengh_list]
        
        return transactions_id_list
    
    def info_for_trans_to_wallet(self, salary: int):
        text = f'Перевод на кошелек для {self.get_names} на сумму {salary}.'
        return text