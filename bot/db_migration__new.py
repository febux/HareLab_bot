from peewee import InternalError

from models import User, Admin, Author, Phrase, BlockedUser, Post, database

try:
    database.connect()
    database.drop_tables([User, Admin, Author, Phrase, BlockedUser, Post])
    database.create_tables([User, Admin, Author, Phrase, BlockedUser, Post])
except InternalError as err:
    print(err)
    database.close()
else:
    user_1 = User.create(user_id=526995113, username='febux')
    admin_1 = Admin.create(profile=user_1, permissions='admin_permissions')
    user_2 = User.create(user_id=526545459, username='Dmitry_Rusak')
    admin_2 = Admin.create(profile=user_2, permissions='admin_permissions')
    print('success creation of tables')
    database.close()
