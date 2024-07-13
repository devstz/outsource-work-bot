from dataclasses import dataclass


@dataclass
class Finance:
    budget: int

class Finance:
    def __init__(self, data: dict):
        '''
        attribute: all_money: int, profit: int, ad_money: int,
        transferred_money: int, vendor_money: int, 
        '''
        self.data = data

    def __getattr__(self, name: str) -> any:
        '''
        name: chat_id: int, username: str, name: str, history_transaction: list,
        history_bans: dict
        '''
        if name == 'history_wallet':
            return {date: data for date, data in self.data[name].items()}
        elif name in self.data:
            return self.data[name]
        else:
            raise AttributeError(f"'Finance' object has no attribute '{name}'")

    def __str__(self) -> str:
        """String representation of the finance"""
        return f"Finance "
