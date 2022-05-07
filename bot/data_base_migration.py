from peewee import InternalError

from models import User, Admin, Author, Phrase, BlockedUser, Post, database

try:
    database.connect()
    database.drop_tables([User, Admin, Author, Phrase, BlockedUser, Post])
    database.create_tables([User, Admin, Author, Phrase, BlockedUser, Post])
except InternalError as px:
    print(str(px))
else:
    user = User.create(user_id=526995113, username='febux')
    admin = Admin.create(profile=user, permissions='admin_permissions')
    print('success creation of tables')
    database.close()
