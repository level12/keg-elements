"""Common SQLAlchemy column types."""
import sqlalchemy as sa

from keg_elements import crypto


class TimeZoneType(sa.Unicode):
    """A column type for time zones, stored as a unicode string."""

    def __init__(self, length=None, **kwargs):  # Override any given length.
        super(TimeZoneType, self).__init__(length=255, **kwargs)


class EncryptedUnicode(sa.TypeDecorator):
    impl = sa.UnicodeText

    def __init__(self, *args, **kwargs):
        """
        Constructor for encrypted unicode type
        :param key: A bytes object containing the encryption key or a callable that returns the key
        :param encrypt: A callable that takes a unicode string and the encryption key as arguments
            and returns the encrypted data as a bytes object.
        :param decrypt: A callable that takes a bytes object and the encryption key as arguments
            and returns the decrypted data as a unicode string.
        """
        self._key = kwargs.pop('key')
        self._encrypt = kwargs.pop('encrypt', crypto.encrypt_str)
        self._decrypt = kwargs.pop('decrypt', crypto.decrypt_str)
        super(EncryptedUnicode, self).__init__(*args, **kwargs)

    @property
    def key(self):
        key_val = self._key() if callable(self._key) else self._key
        if len(key_val) < 32:
            raise ValueError('Key must be at least 32 bytes long')
        return key_val[:32]

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return self._encrypt(value, self.key).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self._decrypt(value.encode(), self.key)
