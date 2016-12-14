import os

import cryptography.hazmat.primitives.ciphers as ciphers
from cryptography.hazmat.backends import default_backend


def aes_cipher(key, iv, mode=None):
    algo = ciphers.algorithms.AES(key)
    mode = mode or ciphers.modes.CBC(iv)
    return ciphers.Cipher(algo, mode, backend=default_backend())


def aes_encryptor(key, iv, mode=None):
    return aes_cipher(key, iv, mode=mode).encryptor()


def aes_decryptor(key, iv, mode=None):
    return aes_cipher(key, iv, mode=mode).decryptor()


def aes_encrypt_str(data, key):
    """
    Function that handles the most common case of encrypting a string with AES in CBC mode
    :param data: A unicode string to be encrypted. This string will be converted to utf-8.
    :param key: A bytes object containing the encryption key
    :returns: The encrypted data as a bytes object. The first 16 bytes are the IV
    """
    iv = os.urandom(16)
    encryptor = aes_encryptor(key, iv)
    bin_data = data.encode('utf-8')
    bin_data += b' ' * (16 - (len(bin_data) % 16))  # pad string to multiple of block size
    encrypted = encryptor.update(bin_data) + encryptor.finalize()
    return iv + encrypted


def aes_decrypt_str(data, key):
    """
    Function that handles the most common case of decrypting a string with AES in CBC mode
    :param data: A bytes object containing the data to be decrypted.
        The first 16 bytes should be the IV. The data is assumed to be encoded as utf-8
    :param key: A bytes object containing the encryption key
    :returns: The decrypted value as a unicode string
    """
    iv, data = data[:16], data[16:]
    decryptor = aes_decryptor(key, iv)
    decrypted = decryptor.update(data) + decryptor.finalize()
    return decrypted.decode('utf-8').rstrip()
