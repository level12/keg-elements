import cryptography
import pytest
from blazeutils import randchars
from cryptography.hazmat.primitives import ciphers

from keg_elements import crypto


key = b'abcdefghijklmnopqrstuvwxyz123456'


def test_encrypt():
    data = b'\x01\x02\x03\x04\x05'
    encrypted = crypto.encrypt(data, key)
    assert data not in encrypted
    assert encrypted != crypto.encrypt(data, key)


def test_decrypt():
    data = b'\x01\x02\x03\x04\x05'
    assert crypto.decrypt(
        b'gAAAAABYVEWYMFW8Nyg91RlWubjVe_B82Q7AIyNDemSQSylUnJefKZ3k9smRdEP9-rD2vyNirrXqWCZ3wN1gk-Fu'
        b'gcdkwGuelQ==',
        key
    ) == data
    assert crypto.decrypt(
        b'gAAAAABYVEXjvHp-r0FnZYJ5t3_p1H9TDMU6lGOAAeHerYkHR40XHCfEJl1FEI0w6WsmwW5Gc1976LVyf46jX4K3'
        b'BPfWkY8aNA==',
        key
    ) == data

    with pytest.raises(cryptography.fernet.InvalidToken):
        crypto.decrypt(
            b'gAAAAABYVEXjvHp-r0FnZYJ5t3_p1H9TDMU6lGOAAeHerYkHR40XHCfEJl1FEI0w6WsmwW5Gc1976LVyf46j'
            b'X4K3BPfWkY8aNA==',
            b'a' * 32
        )


def test_encrypt_str():
    s = randchars()
    encrypted = crypto.encrypt_str(s, key)
    assert s.encode() not in encrypted
    assert encrypted != crypto.encrypt_str(s, key)


def test_decrypt_str():
    assert crypto.decrypt_str(
        b'gAAAAABYVEJVKXq6WlWn0wo3DDakIr6nwtHtk6llws4uJxgVvoBPLfhNRZc5eiWJEEAsEvtUjzQBqfaNscmqy2U'
        b'h0J21n1TyDA==',
        key
    ) == 'foo'
    assert crypto.decrypt_str(
        b'gAAAAABYVENwMqAohDnzfTAZy6P4SV1Z8fOkREMNd52Oey1SeVE5aZcgcJBomEVFORJjMvh5LIUEQ2vgeVI-bi'
        b'CDjboq37uOaw==',
        key
    ) == 'foo'


class TestCryptors:
    def enc_algo(self, encryptor):
        return encryptor._ctx._cipher.name, encryptor._ctx._mode.name

    def test_aes_encryptor_defaults(self):
        enc1, iv1 = crypto.aes_encryptor(key)
        enc2, iv2 = crypto.aes_encryptor(key)
        assert self.enc_algo(enc1) == ('AES', 'CBC')
        assert self.enc_algo(enc2) == ('AES', 'CBC')

        assert iv1 != iv2
        assert len(iv1) == 16
        assert len(iv2) == 16

    def test_aes_encryptor_mode(self):
        enc, iv = crypto.aes_encryptor(key, mode=ciphers.modes.ECB())
        assert self.enc_algo(enc) == ('AES', 'ECB')

    def test_aes_decryptor_defaults(self):
        dec1 = crypto.aes_decryptor(key, b'a' * 16)
        dec2 = crypto.aes_decryptor(key, b'a' * 16)
        assert self.enc_algo(dec1) == ('AES', 'CBC')
        assert self.enc_algo(dec2) == ('AES', 'CBC')

    def test_aes_decryptor_mode(self):
        dec = crypto.aes_decryptor(key, b'a' * 16, mode=ciphers.modes.ECB())
        assert self.enc_algo(dec) == ('AES', 'ECB')

    def test_encrypt_decrypt(self):
        data = b'a' * 32
        enc, iv = crypto.aes_encryptor(key)
        enc_data = enc.update(data) + enc.finalize()

        # check CBC is functioning
        assert enc_data[:16] != enc_data[16:]

        dec = crypto.aes_decryptor(key, iv)
        dec_data = dec.update(enc_data) + dec.finalize()
        assert dec_data == data
