import io
import os
import base64
from pathlib import Path

from keg_elements.encoding import force_bytes

import cryptography.fernet as fernet
import cryptography.hazmat.primitives.ciphers as ciphers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import (
    constant_time,
    hashes,
    hmac,
    padding
)

from keg_elements.extensions import lazy_gettext as _


def aes_cipher(key, iv, mode=None):
    """Wrapper to build AES cipher from cryptography.

    :param key: AES key.
    :param iv: Used to create a CBC mode if a mode isn't manually provided.
    :param mode: Optional, provides an explicit mode to the cipher. CBC if not provided.
    :returns: Cipher instance.
    """
    algo = ciphers.algorithms.AES(key)
    mode = mode or ciphers.modes.CBC(iv)
    return ciphers.Cipher(algo, mode, backend=default_backend())


def aes_encryptor(key, mode=None):
    """Get encryptor cipher context for an AES key.

    Init vector is generated randomly.

    :param key: AES key.
    :param mode: Optional, provides an explicit mode to the cipher. CBC if not provided.
    :returns: Encryptor cipher context.
    """
    iv = os.urandom(ciphers.algorithms.AES.block_size // 8)
    cipher = aes_cipher(key, iv, mode=mode)
    return cipher.encryptor(), iv


def aes_decryptor(key, iv, mode=None):
    """Get decryptor cipher context for an AES key.

    :param key: AES key.
    :param iv: Initialization vector used to construct the default CBC mode.
    :param mode: Optional, provides an explicit mode to the cipher. CBC if not provided.
    :returns: Decryptor cipher context.
    """
    cipher = aes_cipher(key, iv=iv, mode=mode)
    return cipher.decryptor()


def fernet_cipher(key):
    """Build a Fernet cipher from the given key."""
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


def encrypt_file(key, in_fpath, out_fpath=None, chunksize=64 * 1024):
    """ Encrypts a file using AES (CBC mode) with the given key.

    :param key: The encryption key - a string that must be
        either 16, 24 or 32 bytes long. Longer keys
        are more secure.
    :param in_fpath: Full path of the input file
    :param out_fpath: Full path of the output file. If None, '<in_fpath>.enc' will be used.
    :param chunksize: Sets the size of the chunk which the function uses to read and encrypt
        the file. Larger chunk sizes can be faster for some files and machines. chunksize must
        be divisible by 16.
    :returns: Output file path string.
    """
    if not out_fpath:
        out_fpath = in_fpath + '.enc'

    with open(in_fpath, 'rb') as infile, open(out_fpath, 'wb') as outfile:
        for chunk in encrypt_fileobj(key, infile, chunksize):
            outfile.write(chunk)

    return out_fpath


def encrypt_fileobj(key, in_fileobj, chunksize=64 * 1024):
    """ Encrypts a file object using AES (CBC mode) with the given key.

    Example::

        with open('my_encrypted_file', mode='wb') as f:
            for chunk in encrypt_fileobj(my_crypto_key, buffer):
                f.write(chunk)

    :param key: The encryption key - a string that must be
        either 16, 24 or 32 bytes long. Longer keys
        are more secure.
    :param in_fpath: Full path of the input file
    :param out_fpath: Full path of the output file. If None, '<in_fpath>.enc' will be used.
    :param chunksize: Sets the size of the chunk which the function uses to read and encrypt
        the file. Larger chunk sizes can be faster for some files and machines. chunksize must
        be divisible by 16.
    :returns: Output file path string.
    """
    encryptor, iv = aes_encryptor(key)
    padder = padding.PKCS7(encryptor._ctx._cipher.block_size).padder()

    yield iv
    for chunk in iter(lambda: in_fileobj.read(chunksize), b''):
        data = padder.update(chunk)
        data = encryptor.update(data)
        yield data
    data = padder.finalize()
    yield encryptor.update(data)
    yield encryptor.finalize()


def decrypt_file(key, in_fpath, out_fpath=None, chunksize=24 * 1024):
    """ Decrypts a file using AES (CBC mode) with the
        given key. Parameters are similar to encrypt_file,
        with one difference: out_filename, if not supplied
        will be in_filename without its last extension
        (i.e. if in_filename is 'aaa.zip.enc' then
        out_filename will be 'aaa.zip')
    """
    if out_fpath is None:
        if Path(in_fpath).suffix == '.enc':
            out_fpath = Path(in_fpath).stem
        else:
            raise ValueError(_('If input file name doesn\'t end in ".enc" then output '
                               'filename must be given.'))
    with open(in_fpath, 'rb') as infile, open(out_fpath, 'wb') as outfile:
        decrypt_fileobj(key, infile, outfile, chunksize)

    return out_fpath


def decrypt_bytesio(key, in_fpath, chunksize=24 * 1024):
    """ Decrypts a file using AES (CBC mode) with the given key, and returns
    the contents in a BytesIO stream.

    :param key: The encryption key - a string that must be
        either 16, 24 or 32 bytes long. Longer keys
        are more secure.
    :param in_fpath: Full path of the input file
    :param chunksize: Sets the size of the chunk which the function uses to read and encrypt
        the file. Larger chunk sizes can be faster for some files and machines. chunksize must
        be divisible by 16.
    :returns: Output file path string.
    """
    with open(in_fpath, 'rb') as infile:
        bytes_fobj = io.BytesIO()
        decrypt_fileobj(key, infile, bytes_fobj, chunksize)
    # prep for reading from the start of the file
    bytes_fobj.seek(0)
    return bytes_fobj


def decrypt_fileobj(key, in_fileobj, out_fileobj, chunksize):
    """ Decrypts a file object using AES (CBC mode) with the given key, and writes
    the contents to the given output file object.

    :param key: The encryption key - a string that must be
        either 16, 24 or 32 bytes long. Longer keys
        are more secure.
    :param in_fileobj: Readable IO stream holding encrypted contents.
    :param out_fileobj: Writeable IO stream for decrypted contents.
    :param chunksize: Sets the size of the chunk which the function uses to read and encrypt
        the file. Larger chunk sizes can be faster for some files and machines. chunksize must
        be divisible by 16.
    :returns: None.
    """
    iv = in_fileobj.read(16)
    decryptor = aes_decryptor(key, iv)
    unpadder = padding.PKCS7(decryptor._ctx._cipher.block_size).unpadder()

    for chunk in iter(lambda: in_fileobj.read(chunksize), b''):
        data = decryptor.update(chunk)
        data = unpadder.update(data)
        out_fileobj.write(data)

    out_fileobj.write(unpadder.update(decryptor.finalize()))
    out_fileobj.write(unpadder.finalize())


def constant_time_compare(a, b):
    """Wrapper for cryptography constant time comparison, which will defeat timing attacks."""
    return constant_time.bytes_eq(a, b)


def salted_hmac(salt, value, secret):
    """Create an HMAC for a value using the given salt and secret.

    :param salt:
    :param value:
    :param secret:
    """
    salt = force_bytes(salt)
    secret = force_bytes(secret)
    value = force_bytes(value)

    hasher = hashes.Hash(hashes.SHA512(), backend=default_backend())
    hasher.update(salt + secret)
    key = hasher.finalize()

    hmacer = hmac.HMAC(key, hashes.SHA512(), backend=default_backend())
    hmacer.update(value)
    return hmacer.finalize()
