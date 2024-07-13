from aiogram.fsm.state import State, StatesGroup

class AuthAdminStates(StatesGroup):
    Secret_key = State()
    Password = State()
    InputName = State()
    Select_admin_profile = State()

class AdminStates(StatesGroup):
    Main_Menu = State()

    Create_Workday = State()

    Wallet_Transaction = State()

    Payment_Worker = State()
    Payment_Worker_ref = State()

    Search_users = State()
    Mailing_bot = State()

    Create_Work = State()
    Select_departure_time_work = State()
    Select_lunch = State()
    Select_max_workers_work = State()
    Select_salary_work = State()
    Select_age_limit = State()
    Select_vendor_salary_work = State()
    Select_salary_workCreate_Work = State()
    Select_type_payment = State()
    Select_end_time_work = State()
    Select_start_time_work = State()
    Select_ref_money = State()