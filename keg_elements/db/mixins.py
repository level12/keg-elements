import datetime as dt
import random

import arrow
from blazeutils.strings import randchars
from keg.db import db
import sqlalchemy as sa
from sqlalchemy.inspection import inspect as sainsp
import six
import sqlalchemy.orm as saorm
from sqlalchemy_utils import ArrowType

from .utils import (
    session_commit,
    session_flush,
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
        #for attr in insp.attrs:
        return dict([(attr.key, attr.value)
                     for attr in insp.attrs if attr.key not in exclude])


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
        # automatically sets most field types. Any fields passed into the method
        #   will override the automatic behavior
        # subclasses need to set any necessary key values before calling this method
        #   including primary and foreign keys
        insp = sainsp(cls)
        for column in insp.columns:
            # skip fields already in kwargs, foreign key references, and any
            #   field having a default or server_default configured
            if (column.key in kwargs or column.foreign_keys or column.server_default
                    or column.default or column.primary_key):
                continue

            # If the column is being used for polymorphic inheritance identification, then don't
            # set the value.
            if insp.mapper.polymorphic_on is column:
                continue

            if isinstance(column.type, sa.types.Enum):
                kwargs[column.key] = random.choice(column.type.enums)
            elif isinstance(column.type, sa.types.String):
                kwargs[column.key] = randchars(min(column.type.length or 25, 25))
            elif isinstance(column.type, (sa.types.Integer, sa.types.Numeric)):
                kwargs[column.key] = 0
            elif isinstance(column.type, sa.types.Date):
                kwargs[column.key] = dt.date.today()
            elif isinstance(column.type, sa.types.DateTime):
                kwargs[column.key] = dt.datetime.now()

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
