from cryptography.fernet import Fernet

from models import Server, IpAddress, Log


def encrypt(key, plain_str):
    fernet = Fernet(key)
    return fernet.encrypt(plain_str.encode())


def decrypt(key, encrypted_str):
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_str).decode()


def create_tables(db, models):
    db.connect()
    db.create_tables(models)


def init_db(db):
    models = [Server, IpAddress, Log]
    print("Creating tables from models...")
    create_tables(db, models)


