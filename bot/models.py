import datetime

from peewee import SqliteDatabase
import files

from peewee import Model, PrimaryKeyField, DateTimeField, CharField, \
    IntegerField, TextField, ForeignKeyField


DATABASE = files.main_db
database = SqliteDatabase(DATABASE)


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    user_id = IntegerField(unique=True, null=False)
    username = CharField(max_length=100, null=True)

    created_at = DateTimeField(default=datetime.datetime.now())
    updated_at = DateTimeField(default=datetime.datetime.now())

    class Meta:
        db_table = "users"
        order_by = ('created_at',)


class Admin(BaseModel):
    id = PrimaryKeyField(null=False)
    profile = ForeignKeyField(User, unique=True, backref='profile', on_delete='CASCADE')
    permissions = TextField(default='')

    created_at = DateTimeField(default=datetime.datetime.now())
    updated_at = DateTimeField(default=datetime.datetime.now())

    class Meta:
        db_table = "admins"
        order_by = ('created_at',)


class Author(BaseModel):
    id = PrimaryKeyField(null=False)
    profile = ForeignKeyField(User, unique=True, backref='profile', on_delete='CASCADE')
    permissions = TextField(default='')
    experience = IntegerField(null=False, default=0)

    created_at = DateTimeField(default=datetime.datetime.now())
    updated_at = DateTimeField(default=datetime.datetime.now())

    class Meta:
        db_table = "authors"
        order_by = ('created_at',)


class BlockedUser(BaseModel):
    id = PrimaryKeyField(null=False)
    profile = ForeignKeyField(User, unique=True, backref='profile', on_delete='CASCADE')
    who_blocked = CharField(max_length=100, null=True)

    created_at = DateTimeField(default=datetime.datetime.now())
    updated_at = DateTimeField(default=datetime.datetime.now())

    class Meta:
        db_table = "blocked_users"
        order_by = ('created_at',)


class Phrase(BaseModel):
    phrase = CharField(null=False)
    phrase_text = TextField(null=False)
    phrase_text_entities = TextField(default={})

    created_at = DateTimeField(default=datetime.datetime.now())
    updated_at = DateTimeField(default=datetime.datetime.now())

    class Meta:
        db_table = "phrases"
        order_by = ('created_at',)


class Post(BaseModel):
    id_post = PrimaryKeyField(null=False)
    author = ForeignKeyField(User, backref='authors', on_delete='CASCADE')
    post_name = TextField(unique=True, null=False)
    post_date = TextField(null=True)
    post_desc = TextField(null=False)
    what_needs = TextField(null=True)
    site = TextField(null=True)
    twitter = TextField(null=True)
    discord = TextField(null=True)
    hashtags = TextField(null=False)
    pic_post = TextField(default='')
    name_entities = TextField(default='')
    desc_entities = TextField(default='')
    date_entities = TextField(default='')
    what_needs_entities = TextField(default='')
    status = IntegerField(default=0)
    message_id = IntegerField(null=True)

    created_at = DateTimeField(default=datetime.datetime.now())
    updated_at = DateTimeField(default=datetime.datetime.now())

    class Meta:
        db_table = "posts"
        order_by = ('created_at',)
