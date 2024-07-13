from datetime import datetime
from typing import Set, Union

class Transaction:
    trans_id: str
    from_user_id: int
    for_user_id: int
    date: int
    money: int
    type_id: int
    paid: bool
    paid_date: datetime
    
    def __init__(self, data: dict):
        self.data = data

    def __getattr__(self, name: str) -> any:
        '''
        name: trans_id: str, from_user_id: int, for_user_id: int, date: int, money: int, type_id: int
        
        '''
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(f"'Transaction' object has no attribute '{name}'")

    def __str__(self) -> str:
        """String representation of the transaction"""
        return f"Transaction {self.money} (from {self.from_user_id} for {self.for_user_id}, type_id - {self.type_id})"

    @property
    def info_for_user(self) -> str:
        info_text = f'{self.trans_id}: {self.money}₽ ({self.date})'
        if 'paid' in self.data:
            info_text += f' {"✅" if self.paid else "❌"}'
        return info_text
    
    @property
    def all_info_for_user(self) -> str:
        info_text = f'Транзакция {self.trans_id}:\n\nДата совершения: {self.date}\nСумма: {self.money}₽\nID типа транзакции: {self.type_id}'
        if 'paid' in self.data:
            info_text += f'\nВыплачено - {"✅" if self.paid else "❌"}'
            if self.paid:
                info_text += f'\nДата выплаты - {self.paid_date}'
        return info_text
    
    @property
    def info_for_work(self) -> str:
        info_text = f'{self.trans_id}: {self.money}₽ ({self.date})'
        return info_text
    
    @property
    def all_info_for_work(self) -> str:
        info_text = f'Транзакция {self.trans_id}:\n\nДата совершения: {self.date}\nСумма: {self.money}₽\nID типа транзакции: {self.type_id}'
        return info_text