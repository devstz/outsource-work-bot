

class Request:
    def __init__(self, data: dict):
        self.data = data

    def __getattr__(self, name: str) -> any:
        '''
        name: quest_id: str, user_id: int, admin_id: int, date: int, text: str, answer: str
        '''
        if name in self.data:
            return self.data[name]
        else:
            raise AttributeError(f"'Request object has no attribute '{name}'")

    def __str__(self) -> str:
        """String representation of the request"""
        return f"User: {user_id} text: {self.text} date: {self.date}"