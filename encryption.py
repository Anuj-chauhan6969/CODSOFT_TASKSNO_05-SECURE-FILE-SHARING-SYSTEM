from cryptography.fernet import Fernet
import os

KEY_FILE = "secret.key"


def get_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()

        with open(KEY_FILE, "wb") as f:
            f.write(key)

        return key

    with open(KEY_FILE, "rb") as f:
        return f.read()


fernet = Fernet(get_key())


def encrypt_file(data):
    return fernet.encrypt(data)


def decrypt_file(data):
    return fernet.decrypt(data)
