from datetime import datetime

from decouple import config

from bot import GKBot
from services import DataBase


def main():
    time_session = datetime.now()
    setup_logging(time_session)

    filename = config('name_db')
    name_db = config('name_mongodb')
    db = DataBase(filename=filename, name_db=name_db)
    bot = GKBot(db=db)

    try:
        bot.run()
    except KeyboardInterrupt:
        try:
            bot.close()
        except RuntimeError:
            print('Stop bot')


if __name__ == '__main__':
    main()