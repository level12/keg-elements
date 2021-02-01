"""Common SQLAlchemy column types."""
import enum
import random

import sqlalchemy as sa

from keg_elements import crypto
from keg_elements.extensions import lazy_gettext as _


class TimeZoneType(sa.Unicode):
    """A column type for time zones, stored as a unicode string."""

    def __init__(self, length=None, **kwargs):  # Override any given length.
        super(TimeZoneType, self).__init__(length=255, **kwargs)


class EncryptedUnicode(sa.TypeDecorator):
    """
    Unicode column type that encrypts value with the given key for persistance to storage.

    :param key: A bytes object containing the encryption key or a callable that returns the key
    :param encrypt: A callable that takes a unicode string and the encryption key as arguments
        and returns the encrypted data as a bytes object.
    :param decrypt: A callable that takes a bytes object and the encryption key as arguments
        and returns the decrypted data as a unicode string.
    """
    impl = sa.UnicodeText

    def __init__(self, *args, **kwargs):
        self._key = kwargs.pop('key')
        self._encrypt = kwargs.pop('encrypt', crypto.encrypt_str)
        self._decrypt = kwargs.pop('decrypt', crypto.decrypt_str)
        super(EncryptedUnicode, self).__init__(*args, **kwargs)

    @property
    def key(self):
        key_val = self._key() if callable(self._key) else self._key
        if len(key_val) < 32:
            raise ValueError(_('Key must be at least 32 bytes long'))
        return key_val[:32]

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return self._encrypt(value, self.key).decode()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return self._decrypt(value.encode(), self.key)


class DBEnum(enum.Enum):
    """
    Base class for all database enum types.

    To create a new enum, subclass this, add the enum values, and implement db_name()::

        class MyEnum(DBEnum):
            option1 = 'Option 1'
            option2 = 'Option 2'

            @classmethod
            def db_name(cls):
                return 'my_enum_db_name'

    To declare a DB column of this type::

        class MyEntity(db.Model):
            option = sa.Column(MyEnum.db_type())

    To set the choices on a form field::

        class MyEntityForm(wtforms.Form):
            option = wtforms.SelectField(
                'Option',
                choices=MyEnum.form_options()
                coerce=MyEnum.coerce
            )

    If using `ModelForm` the field will be configured with the above options automatically::

        class MyEntityForm(ModelForm):
            class Meta:
                model = MyEntity

    """
    @classmethod
    def db_name(cls):
        raise NotImplementedError

    @classmethod
    def db_type(cls):
        return sa.Enum(cls, name=cls.db_name())

    @classmethod
    def option_pairs(cls):
        return [(o.name, o.value) for o in cls]

    @classmethod
    def form_options(cls):
        return [(o, o.value) for o in cls]

    @classmethod
    def coerce(cls, value):
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        try:
            return cls[value]
        except KeyError:
            raise ValueError('Not a valid selection')

    @classmethod
    def random(cls):
        return random.choice(list(cls))

    def __str__(self):
        return self.name

    def __json__(self):
        return str(self)
