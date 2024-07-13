import asyncio
from datetime import datetime, timedelta
from typing import List

from bson.objectid import ObjectId
from decouple import config
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from aiogram.types import Message

from models import Admin, Finance, Request, Transaction, User, Work, WorkDay
from services.tools import generator_key


class ManagerDB:
    const_all_len_list: int = 5
    users: AsyncIOMotorCollection
    transactions: AsyncIOMotorCollection
    admins: AsyncIOMotorCollection
    works: AsyncIOMotorCollection
    active_workdays: AsyncIOMotorCollection
    archive_workdays: AsyncIOMotorCollection
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    def __getattr__(self, name: str) -> any:
        return self.db[name]
    

    '''
    LISTS
    '''
    async def get_list_users(self) -> List:
        list_users_id = await self.lists.find_one(dict(users_list_id='users_list_id'))
        return list_users_id['users_list']


    async def get_list_users_with_page(self, page: int, len_list: int = 6):
        list_users = await self.lists.find_one(dict(users_list_id='users_list_id'))
        len_users_list = len(list_users['users_list'])
        max_page = (len_users_list + len_list - 1) // len_list - 1
        if page > max_page:
            page = 0
        if page < 0:
            page = max_page
        print(list_users['users_list'])
        list_users = list_users['users_list'][page*len_list:(page+1)*len_list]

        return page, max_page, list_users


    '''
    WorkDays
    '''
    
    async def get_archive_workdays(self, page: int, len_list: int):
        skip = page * len_list
        pipeline = [
            { "$skip": skip },
            { "$limit": len_list}
        ]
        workdays_data = await self.archive_workdays.aggregate(pipeline).to_list(len_list)
        workdays = [WorkDay(data=workday_data) for workday_data in workdays_data]

        num_archive_workdays = await self.archive_workdays.count_documents({})

        return workdays, num_archive_workdays
    
    async def unarchive_workday(self, date: int) -> None:
        workday_data = await self.archive_workdays.find_one_and_delete(filter=dict(date=date))
        await self.active_workdays.insert_one(document=workday_data)

    async def archive_workday(self, date: int) -> None:
        workday_data = await self.active_workdays.find_one_and_delete(filter=dict(date=date))
        await self.archive_workdays.insert_one(document=workday_data)
        

    async def create_workday(self, date:  datetime) -> WorkDay:
        day_to_week = await self.get_const(document_id=config('ID_DAY_WEEK'), key='day_week')

        dt_of_timestamp = int(date.timestamp())
        day_of_week_en = date.strftime("%A")
        day_of_week_ru = day_to_week[date.weekday()]

        work_id = generator_key(7)
        workday_data = dict(
            date=dt_of_timestamp,
            day_en=day_of_week_en,
            day_ru=day_of_week_ru,
            works=[],
            archived=False,
        )

        await self.active_workdays.insert_one(document=workday_data)
        workday = Work(data=workday_data)

        return workday

    async def del_work(self, date: int, work_id: str) -> None:
        await self.active_workdays.update_one(filter=dict(date=date), update={'$pull': dict(works=work_id)})
        await self.works.delete_one(dict(work_id=work_id))

    async def add_to_workday(self, date: int, **kwargs) -> None:
        await self.active_workdays.update_one(filter=dict(date=date), update={'$push': kwargs})

    async def get_active_workday(self, date: int):
        workday_data = await self.active_workdays.find_one(filter=dict(date=date))
        if workday_data:
            workday = WorkDay(data=workday_data)
            return workday

    async def get_active_workdays(self):
        work_days = await self.active_workdays.find().to_list(length=10)
        work_days = [WorkDay(data=data) for data in work_days]
        return work_days

    '''
    Works
    '''
    async def delete_work(self, work_id: str):
        work_data = await self.works.find_one_and_delete(dict(work_id=work_id))
        work = Work(data=work_data)
        dt_st = int(datetime.strptime(work.date, '%Y-%m-%d').timestamp())
        self.active_workdays.update_one(filter=dict(date=dt_st), update={'$pull': dict(works=work_id)})
        return dt_st


    async def create_work(self, date: datetime, day_en: str, day_ru: str) -> Work:
                          
        work_id = generator_key(7)
        work_data = dict(
            work_id=work_id,
            header=None,
            date=date,
            day_ru=day_ru,
            day_en=day_en,
            salary=None,
            vendor_salary=None,
            workers=[],
            worker_turnout=[],
            finish_work=False,
            max_workers=None,
            bus_info=None,
            age_limit=None,
            departure_time=None,
            start_work_time=None,
            end_work_time=None,
            type_payment=None,
            bus_photo_id=None,
            set_workers=False,
            public_message_id=None,
            public_bus_message_id=None,
            transaction_wallets=[],
            payments={},
            lunch=None,
            ready_work=False,
            estimated_salaries={},
            ref_salaries={},
        )

        await self.works.insert_one(document=work_data)
        await self.lists.update_one(filter=dict(works_list_id='works_id_list'), update={'$push': dict(work_id=work_id)})
        work = Work(data=work_data)

        return work

    async def add_to_work(self, work_id: int, **kwargs) -> None:
        await self.works.update_one(filter=dict(work_id=work_id), update={'$push': kwargs})

    async def update_to_work(self, work_id: int, **kwargs) -> None:
        print(kwargs)
        await self.works.update_one(filter=dict(work_id=work_id), update={'$set': kwargs})
    
    async def del_to_work(self, work_id: int, **kwargs) -> None:
        await self.works.update_one(filter=dict(work_id=work_id), update={'$pull': kwargs})
    
    async def del_to_object_work(self, work_id: int, update: dict) -> None:
        await self.works.update_one(filter=dict(work_id=work_id), update={'$unset': update})

    async def get_archive_works(self, date: int) -> List[Work]:
        work_day_data = await self.archive_workdays.find_one(dict(date=date))
        print(date, work_day_data)
        workday = WorkDay(data=work_day_data)
        filter_query = {"work_id": {"$in": workday.works}}
        works = await self.works.find(filter_query).to_list(length=10)
        works = [Work(data=work_data) for work_data in works]
        return works

    async def get_works(self, date: int) -> List[Work]:
        work_day_data = await self.active_workdays.find_one(dict(date=date))
        print(date, work_day_data)
        workday = WorkDay(data=work_day_data)
        filter_query = {"work_id": {"$in": workday.works}}
        works = await self.works.find(filter_query).to_list(length=10)
        works = [Work(data=work_data) for work_data in works]
        return works
    
    async def get_work(self, work_id: int) -> Work:
        work_data = await self.works.find_one(dict(work_id=work_id))
        work = Work(data=work_data)
        return work
    
    async def get_work_with_user(self, date: int, chat_id: int) -> Work:
        filter_query = {'workers': {'$in': [chat_id]}, "date": date}
        print(filter_query)
        work_data = await self.works.find_one(filter_query)
        print(work_data)
        work = Work(data=work_data) if work_data else None
        return work


    '''
    TRANSACTIONS
    '''

    async def update_to_transaction(self, trans_id: str, **kwargs):
        await self.transactions.update_one(filter=dict(trans_id=trans_id), update={'$set': kwargs})

    async def get_transaction(self, **kwargs) -> Admin | None:
        trans_data = await self.transactions.find_one(kwargs)
        if trans_data:
            trans = Transaction(data=trans_data)
            return trans
    
    async def get_transactions(self, trans_id_list: list) -> list | None:
        filter_query = {"trans_id": {"$in": trans_id_list}}
        transactions = await self.transactions.find(filter_query).to_list(length=1000)
        transactions = [Transaction(data=trans_data) for trans_data in transactions]
        return transactions
    
    async def create_transaction(self, data: Message, for_user_id: int, money: int, type_id: int, work: Work = None, photo_id: str = None) -> Transaction:
        trans_id=generator_key(8)
        transaction_data = dict(
            trans_id=trans_id,
            from_user_id=data.chat.id,
            for_user_id=for_user_id,
            date=data.date+timedelta(hours=7),
            money=money,
            type_id=type_id
        )
        if type_id in [0, 4]:
            transaction_data['paid'] = False
            transaction_data['paid_date'] = None
            if work.date:
                transaction_data['date_work'] = work.date
                transaction_data['work_id'] = work.date
                transaction_data['work_header'] = work.header

        if photo_id:
            transaction_data['photo_id'] = photo_id


        await self.transactions.insert_one(document=transaction_data)
        await self.lists.update_one(filter=dict(transactions_list_id='transactions_id_list'), update={'$push': dict(trans_id=trans_id)})
        trans = Transaction(data=transaction_data)

        return trans


    '''
    CONSTS
    '''

    async def get_const(self, document_id: int, key: str) -> int | str:
        consts = await self.consts.find_one({"_id": ObjectId(document_id)})
        const = consts.get(key)
        if const:
            return const
        else:
            if key == 'len_bus_stop_list':
                return self.const_all_len_list
    
    
    


    '''
    ADMINS
    '''

    async def get_admin(self, **kwargs) -> Admin | None:
        admin_data = await self.admins.find_one(kwargs)
        if admin_data:
            admin = Admin(data=admin_data)
            return admin



    
    async def del_to_admin(self, chat_id: int, **kwargs) -> None:
        await self.admins.update_one(filter=dict(chat_id=chat_id), update={'$pull': kwargs})

    async def update_admin_data(self, chat_id: int, update: dict) -> None:
        await self.admins.update_one(filter=dict(chat_id=chat_id), update={'$set': update})
    
    async def add_admin_data(self, chat_id: int, **kwargs) -> None:
        print(chat_id, kwargs, '123')
        await self.admins.update_one(filter=dict(chat_id=chat_id), update={'$push': kwargs})
    
    async def create_admin(self, data: Message, name: str) -> Admin:

        admin_data = dict(
            chat_id=data.chat.id,
            username=data.chat.username,
            name=name,
            date_registration=data.date+timedelta(hours=7),
            assigned_invoices=[],
        )

        await self.admins.insert_one(document=admin_data)
        admin = Admin(data=admin_data)

        return admin


    '''
    USERS
    '''
    async def search_user(self, fltr: str) -> User | None:
        if len(fltr) == 5 and len(fltr.split(' ')) == 1:
            user = await self.get_user(ref_id=fltr)
            return user

        elif len(fltr.split(' ')) == 2:
            first_name, last_name = fltr.split(' ')
            user = await self.get_user(first_name=first_name, last_name=last_name)
            if user:
                return user
            else:
                user = await self.get_user(first_name=last_name, last_name=first_name)
                return user
        
        elif '@' in fltr:
            username = fltr[1:]
            user = await self.get_user(username=username)
            return user
        
        elif fltr.isdigit():
            user = await self.get_user(chat_id=int(fltr))
            return user

        
            

    async def check_registration_user(self, chat_id: int, date: int) -> bool:
        work = await self.get_work_with_user(date=date, chat_id=chat_id)
        if work:
            return work.work_id
        else:
            return False
    
    async def del_to_user(self, chat_id: int, **kwargs) -> None:
        await self.users.update_one(filter=dict(chat_id=chat_id), update={'$pull': kwargs})

    async def update_user_data(self, chat_id: int, update: dict) -> None:
        await self.users.update_one(filter=dict(chat_id=chat_id), update={'$set': update})
    
    async def add_user_data(self, chat_id: int, update: dict) -> None:
        await self.users.update_one(filter=dict(chat_id=chat_id), update={'$push': update})
    
    async def get_users(self, user_id_list: list = None) -> List[User] | List:
        if user_id_list:
            filter_query = {"chat_id": {"$in": user_id_list}}
            users = await self.users.find(filter_query).to_list(length=1000)
            users = [User(data=user_data) for user_data in users]
        else:
            users = await self.users.find().to_list(length=10000)
            users = [User(data=user_data) for user_data in users]
        return users
    
    async def get_users_filter(self, *args) -> List[User] | List:
        users = await self.users.find(*args).to_list(length=1000)

        users = [User(data=user_data) for user_data in users]
        return users

    async def get_user(self, **kwargs) -> User | None:
        user_data = await self.users.find_one(kwargs)
        if user_data:
            user = User(data=user_data)
            return user
    
    
    async def validate_user(self, ref_id: str) -> int:
        invited_user = await self.get_user(ref_id=ref_id)

        if invited_user:
            return invited_user.chat_id
        

    async def create_user(self, data: Message, invited_ref_id: int = None) -> User:

        invited_user_id = await self.validate_user(ref_id=invited_ref_id)
        
        if invited_user_id:
            await self.add_user_data(chat_id=invited_user_id, update=dict(invite_users=data.chat.id))

        user_data = dict(
            chat_id=data.chat.id,
            username=data.chat.username,
            date_registration=data.date+timedelta(hours=7),
            date_ban=None,
            first_name=None,
            last_name=None,
            gender=None,
            age=None,
            bus_stop_id=None,
            ready_profile='not_ready',
            ref_id=generator_key(5),
            invite_users=[],
            invited_user_id=invited_user_id,
            invited_ref_id=invited_ref_id, 
            wallet=0,
            awaiting_payments=[],
            ref_money=0,
            history_wallet=[],
            ban=False,
            card_id=None,
            phone=None,
        )

        await self.users.insert_one(document=user_data)
        await self.lists.update_one(filter=dict(users_list_id='users_list_id'), update={'$push': dict(users_list=data.chat.id)})
        user = User(data=user_data)

        return user



if __name__ == "__main__":
    pass
