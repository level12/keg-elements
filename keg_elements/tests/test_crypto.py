from keg_elements import crypto


def test_aes_encrypt_str():
    key = b'abcdefghijklmnopqrstuvwxyz123456'
    encrypted = crypto.aes_encrypt_str('foo', key)
    assert b'foo' not in encrypted
    assert len(encrypted) == 32
    assert encrypted != crypto.aes_encrypt_str('foo', key)


def test_aes_decrypt_str():
    key = b'abcdefghijklmnopqrstuvwxyz123456'
    assert crypto.aes_decrypt_str(
        b'\xa9\xf3_\n\xb6\xd8-\x9c\xbb_%\xe7\xc8\xd8\x8b\x8c\x1b2\xb6I\xd3\x9c\x18"^>Qu'
        b'\x19\xe1\x165',
        key
    ) == 'foo'
    assert crypto.aes_decrypt_str(
        b'\xf3\xcb\x02\x1d\xd5H*\r\xb2\xadC\xcdv\x9f\x14\xc5\x01\x01\xcf\x9f\x12\x00"\x97\x89\xa7'
        b'\xde9j\xfd\x07\xd7',
        key
    ) == 'foo'
