from typing import List
from models.transaction.transaction import Transaction
from models.user.user import User


class Admin:
    def __init__(self, data: dict):
        '''
        attribute: chat_id: int, username: str, name: str, assigned_invoices: list
        '''
        self.data = data

    def __getattr__(self, name: str) -> any:
        '''
        name: chat_id: int, username: str, name: str, filters_search: list
        '''
        if name == 'history_wallet':
            return {date: data for date, data in self.data[name].items()}
        elif name in self.data:
            return self.data[name]
        else:
            raise AttributeError(f"'Admin' object has no attribute '{name}'")

    def __str__(self) -> str:
        """String representation of the admin"""
        return f"Admin {self.name} username={self.username} (chat_id={self.chat_id})"

    def info_for_payment(self, user: User, transactions: List[Transaction], money: int, type_payment: int):
        
        text = f'Выплата {len(transactions)} транзакци{"и" if len(transactions) == 1 else "й"} на сумму {money}₽:\n\n'

        for i, trans in enumerate(transactions, 1):
            text += f'{i}) {trans.work_header} - {trans.money}₽ ({trans.date_work}) <code>{trans.trans_id}</code>\n'
        print(type_payment)
        if type_payment:
            t_p = f'📱: <code>{user.phone}</code>' if int(type_payment) == 1 else f'💳: <code>{user.card_id}</code>'
            text += f'\nОтправьте деньги, используя нижепредставленные реквизиты:\n\n{t_p}\n\n'
            text += 'После отправьте скриншот с выплатой и подпишите сумму пополнения под ним.'
        else:
            text += f'\nВыберите способ оплаты.'

        return text