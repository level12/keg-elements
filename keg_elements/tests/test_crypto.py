from io import BytesIO

import cryptography
import pytest
from blazeutils import randchars
from cryptography.hazmat.primitives import ciphers

from keg_elements import crypto


CRYPTO_KEY = b'abcdefghijklmnopqrstuvwxyz123456'


def test_encrypt():
    data = b'\x01\x02\x03\x04\x05'
    encrypted = crypto.encrypt(data, CRYPTO_KEY)
    assert data not in encrypted
    assert encrypted != crypto.encrypt(data, CRYPTO_KEY)


def test_decrypt():
    data = b'\x01\x02\x03\x04\x05'
    assert crypto.decrypt(
        b'gAAAAABYVEWYMFW8Nyg91RlWubjVe_B82Q7AIyNDemSQSylUnJefKZ3k9smRdEP9-rD2vyNirrXqWCZ3wN1gk-Fu'
        b'gcdkwGuelQ==',
        CRYPTO_KEY
    ) == data
    assert crypto.decrypt(
        b'gAAAAABYVEXjvHp-r0FnZYJ5t3_p1H9TDMU6lGOAAeHerYkHR40XHCfEJl1FEI0w6WsmwW5Gc1976LVyf46jX4K3'
        b'BPfWkY8aNA==',
        CRYPTO_KEY
    ) == data

    with pytest.raises(cryptography.fernet.InvalidToken):
        crypto.decrypt(
            b'gAAAAABYVEXjvHp-r0FnZYJ5t3_p1H9TDMU6lGOAAeHerYkHR40XHCfEJl1FEI0w6WsmwW5Gc1976LVyf46j'
            b'X4K3BPfWkY8aNA==',
            b'a' * 32
        )


def test_encrypt_str():
    s = randchars()
    encrypted = crypto.encrypt_str(s, CRYPTO_KEY)
    assert s.encode() not in encrypted
    assert encrypted != crypto.encrypt_str(s, CRYPTO_KEY)


def test_decrypt_str():
    assert crypto.decrypt_str(
        b'gAAAAABYVEJVKXq6WlWn0wo3DDakIr6nwtHtk6llws4uJxgVvoBPLfhNRZc5eiWJEEAsEvtUjzQBqfaNscmqy2U'
        b'h0J21n1TyDA==',
        CRYPTO_KEY
    ) == 'foo'
    assert crypto.decrypt_str(
        b'gAAAAABYVENwMqAohDnzfTAZy6P4SV1Z8fOkREMNd52Oey1SeVE5aZcgcJBomEVFORJjMvh5LIUEQ2vgeVI-bi'
        b'CDjboq37uOaw==',
        CRYPTO_KEY
    ) == 'foo'


def test_constant_time_compare():
    # Known cases
    assert crypto.constant_time_compare(b'a', b'a')
    assert not crypto.constant_time_compare(b'aa', b'c')
    try:
        assert crypto.constant_time_compare('a', True)
    except TypeError:
        pass
    else:
        raise AssertionError('Should have raised a TypeError')

    # Fuzz Test
    rando1 = randchars(200).encode()
    rando2 = randchars(200).encode()
    rando3 = randchars(201).encode()
    assert crypto.constant_time_compare(rando1, rando1)
    assert crypto.constant_time_compare(rando2, rando2)
    assert crypto.constant_time_compare(rando3, rando3)
    assert not crypto.constant_time_compare(rando1, rando2)
    assert not crypto.constant_time_compare(rando1, rando3)


class TestCryptors:
    def enc_algo(self, encryptor):
        return encryptor._ctx._cipher.name, encryptor._ctx._mode.name

    def test_aes_encryptor_defaults(self):
        enc1, iv1 = crypto.aes_encryptor(CRYPTO_KEY)
        enc2, iv2 = crypto.aes_encryptor(CRYPTO_KEY)
        assert self.enc_algo(enc1) == ('AES', 'CBC')
        assert self.enc_algo(enc2) == ('AES', 'CBC')

        assert iv1 != iv2
        assert len(iv1) == 16
        assert len(iv2) == 16

    def test_aes_encryptor_mode(self):
        enc, iv = crypto.aes_encryptor(CRYPTO_KEY, mode=ciphers.modes.ECB())
        assert self.enc_algo(enc) == ('AES', 'ECB')

    def test_aes_decryptor_defaults(self):
        dec1 = crypto.aes_decryptor(CRYPTO_KEY, b'a' * 16)
        dec2 = crypto.aes_decryptor(CRYPTO_KEY, b'a' * 16)
        assert self.enc_algo(dec1) == ('AES', 'CBC')
        assert self.enc_algo(dec2) == ('AES', 'CBC')

    def test_aes_decryptor_mode(self):
        dec = crypto.aes_decryptor(CRYPTO_KEY, b'a' * 16, mode=ciphers.modes.ECB())
        assert self.enc_algo(dec) == ('AES', 'ECB')

    def test_encrypt_decrypt(self):
        data = b'a' * 32
        enc, iv = crypto.aes_encryptor(CRYPTO_KEY)
        enc_data = enc.update(data) + enc.finalize()

        # check CBC is functioning
        assert enc_data[:16] != enc_data[16:]

        dec = crypto.aes_decryptor(CRYPTO_KEY, iv)
        dec_data = dec.update(enc_data) + dec.finalize()
        assert dec_data == data


class TestStreamEncryption:
    @pytest.mark.parametrize("bytes_count", range(0, 100))
    def test_encrypt_decrypt_range(self, tmpdir, bytes_count):
        """
            The point of the test here is to do the encrypt/decrypt dance for a range of byte
            lengths that cross the 16 byte boundary and ensure we don't have corner cases that
            don't work.
        """
        value = b'b' * bytes_count
        fobj = tmpdir.join('{}-bytes.txt'.format(bytes_count))
        fobj.write(value)
        enc_fpath = crypto.encrypt_file(CRYPTO_KEY, fobj.strpath)

        bio_fobj = crypto.decrypt_bytesio(CRYPTO_KEY, enc_fpath)
        assert bio_fobj.read() == value

    @pytest.mark.parametrize("chunk_size", range(16, 300, 16))
    def test_encrypt_chunk_size(self, tmpdir, chunk_size):
        value = b'b' * 23
        fobj = tmpdir.join('{}-chunk.txt'.format(chunk_size))
        fobj.write(value)
        enc_fpath = crypto.encrypt_file(CRYPTO_KEY, fobj.strpath, chunksize=chunk_size)

        bio_fobj = crypto.decrypt_bytesio(CRYPTO_KEY, enc_fpath)
        assert bio_fobj.read() == value

    @pytest.mark.parametrize("chunk_size", range(1, 100, 1))
    def test_decrypt_chunk_size(self, tmpdir, chunk_size):
        value = b'b' * 23
        fobj = tmpdir.join('{}-chunk.txt'.format(chunk_size))
        fobj.write(value)
        enc_fpath = crypto.encrypt_file(CRYPTO_KEY, fobj.strpath)

        bio_fobj = crypto.decrypt_bytesio(CRYPTO_KEY, enc_fpath, chunk_size)
        assert bio_fobj.read() == value

    def test_encrypt_explicit_out_fpath(self, tmpdir):
        fobj = tmpdir.join('16-bytes.txt')
        fobj.write('b' * 16)
        enc_fpath = crypto.encrypt_file(CRYPTO_KEY, fobj.strpath, tmpdir.join('out.enc').strpath)

        bio_fobj = crypto.decrypt_bytesio(CRYPTO_KEY, enc_fpath)
        assert bio_fobj.read() == b'b' * 16

    def test_decrypt_bytesio(self, tmpdir):
        fobj = tmpdir.join('tempfile.txt')
        fobj.write('just some text')
        enc_fpath = crypto.encrypt_file(CRYPTO_KEY, fobj.strpath)

        bio_fobj = crypto.decrypt_bytesio(CRYPTO_KEY, enc_fpath)
        assert bio_fobj.read() == b'just some text'

    def test_decrypt_file(self, tmpdir):
        fobj = tmpdir.join('tempfile.txt')
        fobj.write('just some text')
        enc_fpath = crypto.encrypt_file(CRYPTO_KEY, fobj.strpath)

        # implicit name for output file
        out_fpath = crypto.decrypt_file(CRYPTO_KEY, enc_fpath)
        with open(out_fpath) as fp:
            assert fp.read() == 'just some text'

        # explicit name for output file
        fobj = tmpdir.join('tempfile-encrypted.txt')
        out_fpath = crypto.decrypt_file(CRYPTO_KEY, enc_fpath, fobj.strpath)
        with open(out_fpath) as fp:
            assert fp.read() == 'just some text'

        # Input file name doesn't in ".enc" but no output file name given.
        with pytest.raises(ValueError) as excinfo:
            fobj = tmpdir.join('wrong-name.txt')
            crypto.decrypt_file(CRYPTO_KEY, fobj.strpath)
        assert 'doesn\'t end in ".enc" then' in str(excinfo.value)

    def test_decrypt_without_truncate(self, tmpdir):
        fobj = tmpdir.join('tempfile.txt')
        fobj.write('just some text, and more for arguments sake')
        enc_fpath = crypto.encrypt_file(CRYPTO_KEY, fobj.strpath)

        # sys.stdout isn't really stdout, it's something py.test uses for capturing stdout, so
        # create our own container for the output:
        bio = BytesIO()

        def notruncate(*args, **kwargs):
            assert False, 'Truncate should not be called by decrypt_fileobj'  # pragma: no cover

        bio.truncate = notruncate

        with open(enc_fpath, 'rb') as infile:
            crypto.decrypt_fileobj(CRYPTO_KEY, infile, bio, 24 * 1024)
