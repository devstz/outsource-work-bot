from aiogram.fsm.state import State, StatesGroup


class UI_UserStates(StatesGroup):
   Ready_auth = State()
   Main_Menu = State()
   Edit_Firstname = State()
   Edit_Lastname = State()
   Edit_Age = State()
   Edit_Gender = State()
   Edit_Phone = State()
   Edit_Card_ID = State()
   Edit_BusStop = State()
   Menu_Transactions = State()

class Reg_UserStates(StatesGroup):
   Auth = State()
   Gender = State()
   Age = State()
   First_name = State()
   Last_name = State()
   start_Bus_stop_id = State()
   Bus_stop_id = State()
   Ref = State()
   select_Ref = State()
   select_Card_ID = State()
   Phone = State()
   Finish = State()
