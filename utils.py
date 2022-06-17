import datetime

import paramiko
from cryptography.fernet import Fernet
from peewee import MySQLDatabase

from models import Server, IpAddress, Log
import os
from dotenv import load_dotenv

from post_install import run_command

load_dotenv()


def encrypt(key, plain_str):
    fernet = Fernet(key)
    return fernet.encrypt(plain_str.encode())


def decrypt(key, encrypted_str):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_str).decode()


def insert_server_detail(host, name):
    Server.insert(
        host=host,
        name=name,
        created_at=datetime.datetime.utcnow()
    ).on_conflict(
        "replace"
    ).execute()
    print("%s server registered" % name)






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
        port=int(port),
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
    res = cursor.fetchall()
    return res


def sync_remote_and_local_db():
    rule_name = os.getenv("IPSET_RULE_NAME")
    remote_ips = get_remote_db_data()
    # sync remote to local
    for remote_ip in remote_ips:
        query = IpAddress.select().where(IpAddress.ip_address == remote_ip[0]).where(IpAddress.is_active == 1)
        if query.exists() is False:
            try:
                cmd = "sudo ipset add {rule_name} {ip}".format(rule_name=rule_name, ip=remote_ip[0])
                run_command(cmd)
                IpAddress.insert(
                    ip_address=remote_ip[0],
                    is_active=True,
                    created_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow()
                ).on_conflict(
                    action='replace',
                ).execute()
            except BaseException as e:
                Log.insert(text="IP: %s %s" % (remote_ip[0], str(e)), created_at=datetime.datetime.utcnow()).execute()

    # sync local to remote
    local_ips = IpAddress.select().execute()

    for local_ip in local_ips:
        is_exists = False
        try:
            for remote_ip in remote_ips:
                if local_ip.ip_address == remote_ip[0]:
                    is_exists = True
            if is_exists is False:
                cmd = "sudo ipset del {rule_name} {ip}".format(
                    rule_name=rule_name,
                    ip=local_ip.ip_address
                )
                run_command(cmd)
                IpAddress.update({
                    IpAddress.is_active: 0,
                    IpAddress.updated_at: datetime.datetime.utcnow()
                }).where(
                    IpAddress.ip_address == local_ip.ip_address
                ).execute()
        except BaseException as e:
            Log.insert(
                text="IP: %s %s" % (local_ip, str(e)),
                created_at=datetime.datetime.utcnow()
            ).execute()
