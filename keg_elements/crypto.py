import os
import base64

from keg_elements.encoding import force_bytes

import cryptography.fernet as fernet
import cryptography.hazmat.primitives.ciphers as ciphers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import (
    constant_time,
    hashes,
    hmac,
)


def aes_cipher(key, iv, mode=None):
    algo = ciphers.algorithms.AES(key)
    mode = mode or ciphers.modes.CBC(iv)
    return ciphers.Cipher(algo, mode, backend=default_backend())


def aes_encryptor(key, mode=None):
    iv = os.urandom(ciphers.algorithms.AES.block_size // 8)
    cipher = aes_cipher(key, iv, mode=mode)
    return cipher.encryptor(), iv


def aes_decryptor(key, iv, mode=None):
    cipher = aes_cipher(key, iv=iv, mode=mode)
    return cipher.decryptor()


def fernet_cipher(key):
    return fernet.Fernet(base64.urlsafe_b64encode(key))


def encrypt(data, key):
    """
    Encrypts binary data using cryptography's default fernet algorithm
    :param data: plaintext data to encrypt
    :param key: encryption key
    :return: encrypted data as a fernet token (a signed, base64 encoded string)
    """
    return fernet_cipher(key).encrypt(data)


def decrypt(data, key):
    """
    Decrypts binary data using cryptography's default fernet algorithm
    :param data: a fernet token to decrypt
    :param key: encryption key
    :return: decrypted data
    """
    return fernet_cipher(key).decrypt(data)


def encrypt_str(data, key):
    """
    Encrypts a unicode string using cryptography's default fernet algorithm
    :param data: unicode string to encrypt
    :param key: encryption key
    :return: encrypted utf-8 string as a fernet token
    """
    bin_data = data.encode('utf-8')
    return encrypt(bin_data, key)


def decrypt_str(cipher_text, key):
    """
    Decrypts a unicode string using cryptography's default fernet algorithm
    :param cipher_text: a utf-8 string as a fernet token to decrypt
    :param key: encryption key
    :return: decrypted unicode string
    """
    bin_data = decrypt(cipher_text, key)
    return bin_data.decode('utf-8')


def constant_time_compare(a, b):
    return constant_time.bytes_eq(a, b)


def salted_hmac(salt, value, secret):
    salt = force_bytes(salt)
    secret = force_bytes(secret)
    value = force_bytes(value)

    hasher = hashes.Hash(hashes.SHA512(), backend=default_backend())
    hasher.update(salt + secret)
    key = hasher.finalize()

    hmacer = hmac.HMAC(key, hashes.SHA512(), backend=default_backend())
    hmacer.update(value)
    return hmacer.finalize()
