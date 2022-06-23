import datetime
from peewee import Model, CharField, DateTimeField, BooleanField, TextField, SqliteDatabase, IntegerField

db = SqliteDatabase('ipset-config.db', thread_safe=True)


class Base(Model):
    created_at = DateTimeField(default=datetime.datetime.utcnow())
    updated_at = DateTimeField(null=True)

    class Meta:
        database = db


class Server(Base):
    host = CharField(max_length=100, null=False, unique=True, index=True)
    name = CharField(max_length=30, null=True)
    port = CharField(null=False)
    protocol = CharField(max_length=10, null=False)
    is_post_installed = BooleanField(default=False)
    is_active = BooleanField(default=True)


class IpAddress(Base):
    ip_address = CharField(max_length=19, unique=True, index=True, null=False)
    is_active = BooleanField(default=False)


class Log(Base):
    text = TextField(null=False)
