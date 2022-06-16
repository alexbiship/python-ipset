from cryptography.fernet import Fernet
from peewee import MySQLDatabase

from models import Server, IpAddress, Log
import os
from dotenv import load_dotenv

load_dotenv()


def encrypt(key, plain_str):
    fernet = Fernet(key)
    return fernet.encrypt(plain_str.encode())


def decrypt(key, encrypted_str):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_str).decode()


def create_tables(db, models):
    db.connect()
    db.create_tables(models)
    db.close()


def init_db(db):
    models = [Server, IpAddress, Log]
    print("Creating tables from models...")
    create_tables(db, models)


def connect_remote_db():
    host = os.getenv("REMOTE_DB_HOST")
    user = os.getenv("REMOTE_DB_USER")
    port = os.getenv("REMOTE_DB_PORT")
    passwd = os.getenv("REMOTE_DB_PASS")
    db = os.getenv("REMOTE_DB_NAME")
    mysql = MySQLDatabase(
        db,
        host=host,
        port=port,
        user=user,
        passwd=passwd
    )
    return mysql


def get_remote_db_data():
    table = os.getenv("REMOTE_DB_TABLE")
    select_field = os.getenv("REMOTE_DB_COLUMN")
    mysql = connect_remote_db()
    mysql.connect()
    # TODO Set logic to fetch rows using OFFSET and LIMIT
    sql = "SELECT %s FROM %s" % (select_field, table)
    cursor = mysql.execute_sql(sql)
    res = cursor.fetchone()
    print(res)
