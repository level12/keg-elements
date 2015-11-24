import datetime as dt
import random

import arrow
from blazeutils.strings import randchars
from keg.db import db
import sqlalchemy as sa
from sqlalchemy.inspection import inspect as sainsp
import six
import sqlalchemy.orm as saorm
from sqlalchemy_utils import ArrowType, EmailType

from .utils import (
    session_commit,
    session_flush,
    randemail,
    utcnow
)


class DefaultColsMixin(object):
    id = sa.Column(sa.Integer, primary_key=True)
    created_utc = sa.Column(ArrowType, nullable=False, default=arrow.now, server_default=utcnow())
    updated_utc = sa.Column(ArrowType, nullable=False, default=arrow.now, onupdate=arrow.now,
                            server_default=utcnow())


class MethodsMixin(object):
    def from_dict(self, data):
        """
        Update an instance with data from a JSON-style nested dict/list
        structure.
        """
        # surrogate can be guessed from autoincrement/sequence but I guess
        # that's not 100% reliable, so we'll need an override

        mapper = saorm.object_mapper(self)

        for key, value in six.iteritems(data):
            if isinstance(value, dict):
                dbvalue = getattr(self, key)
                rel_class = mapper.get_property(key).mapper.class_
                pk_props = rel_class._descriptor.primary_key_properties

                # If the data doesn't contain any pk, and the relationship
                # already has a value, update that record.
                if not [1 for p in pk_props if p.key in data] and \
                   dbvalue is not None:
                    dbvalue.from_dict(value)
                else:
                    record = rel_class.update_or_create(value)
                    setattr(self, key, record)
            elif isinstance(value, list) and \
                    value and isinstance(value[0], dict):

                rel_class = mapper.get_property(key).mapper.class_
                new_attr_value = []
                for row in value:
                    if not isinstance(row, dict):
                        raise Exception(
                            'Cannot send mixed (dict/non dict) data '
                            'to list relationships in from_dict data.'
                        )
                    record = rel_class.update_or_create(row)
                    new_attr_value.append(record)
                setattr(self, key, new_attr_value)
            else:
                setattr(self, key, value)

    def to_dict(self, exclude=None):
        if exclude is None:
            exclude = []
        insp = sainsp(self)
        return dict((attr.key, attr.value)
                    for attr in insp.attrs if attr.key not in exclude)

    @classmethod
    def add(cls, _commit=True, _flush=False, **kwargs):
        o = cls()
        o.from_dict(kwargs)
        db.session.add(o)
        if _flush:
            session_flush()
        elif _commit:
            session_commit()
        return o

    @classmethod
    def delete_all(cls, commit=True):
        retval = cls.query.delete()
        if commit:
            session_commit()
        return retval

    @classmethod
    def testing_create(cls, **kwargs):
        """Create an object for testing with default data appropriate for the field type

        * Will automatically set most field types ignoring those passed in via kwargs.
        * Subclasses that have foreign key relationships should setup those relationships before
          calling this method.

        Special kwargs:
        _numeric_defaults_range: a tuple of (HIGH, LOW) which controls the acceptable defaults of
                                 the two number types. Both integer and numeric (float) fields are
                                 controlled by this setting.
        """

        NUMERIC_HIGH, NUMERIC_LOW = kwargs.get('_numeric_defaults_range', (-100, 100))

        insp = sainsp(cls)

        skippable = lambda column: (column.key in kwargs      # skip fields already in kwargs
                                    or column.foreign_keys    # skip foreign keys
                                    or column.server_default  # skip fields with server defaults
                                    or column.default         # skip fields with defaults
                                    or column.primary_key     # skip any primary key
                                    )

        for column in (col for col in insp.columns if not skippable(col)):
            if isinstance(column.type, sa.types.Enum):
                kwargs[column.key] = random.choice(column.type.enums)
            elif isinstance(column.type, sa.types.Boolean):
                kwargs[column.key] = random.choice([True, False])
            elif isinstance(column.type, sa.types.Integer):
                kwargs[column.key] = random.randint(NUMERIC_HIGH, NUMERIC_LOW)
            elif isinstance(column.type, sa.types.Numeric):
                kwargs[column.key] = random.uniform(NUMERIC_HIGH, NUMERIC_LOW)
            elif isinstance(column.type, sa.types.Date):
                kwargs[column.key] = dt.date.today()
            elif isinstance(column.type, sa.types.DateTime):
                kwargs[column.key] = dt.datetime.now()
            elif isinstance(column.type, EmailType):
                kwargs[column.key] = randemail(min(column.type.length or 50, 50))
            elif isinstance(column.type, sa.types.String):
                kwargs[column.key] = randchars(min(column.type.length or 25, 25))

        return cls.add(**kwargs)

    def ensure(self, key, _flush=False, _commit=True):
        cls_columns = sainsp(self).mapper.columns
        key_col = getattr(cls_columns, key)
        key_val = getattr(self, key)
        exiting_record = self.query.filter(key_col == key_val).first()
        if not exiting_record:
            db.session.add(self)
            if _flush:
                session_flush()
            elif _commit:
                session_commit()
            return self
        return exiting_record
