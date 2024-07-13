from .work import Work
from datetime import datetime

class WorkDay:
    def __init__(self, data: dict) -> None:
        self.data = data
    
    def __getattr__(self, name: str) -> any:
        """
        Dynamically access attributes from the underlying data.

        Supported attributes:
            - date: int // timestamp
            - day_en: str
            - day_ru: str
            - works: list
        """
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(f"'WorkDay' object has no attribute '{name}'")

    def info_for_button_user(self):
        dt = str(datetime.fromtimestamp(self.date)).split(' ')[0]
        text = f'{self.day_ru} ({dt})'
        return text


