"""Common SQLAlchemy column types."""
import binascii
import sqlalchemy as sa

from keg_elements import crypto


class TimeZoneType(sa.Unicode):
    """A column type for time zones, stored as a unicode string."""

    def __init__(self, length=None, **kwargs):  # Override any given length.
        super(TimeZoneType, self).__init__(length=255, **kwargs)


class EncryptedUnicode(sa.TypeDecorator):
    impl = sa.UnicodeText

    def __init__(self, *args, **kwargs):
        self._key = kwargs.pop('key')
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
        return crypto.aes_encrypt_str(value, self.key).hex()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return crypto.aes_decrypt_str(binascii.unhexlify(value), self.key)
