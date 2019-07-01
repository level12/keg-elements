import contextlib
import math
import random
from decimal import Decimal

import pytest
import wrapt
import sqlalchemy as sa
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime

from blazeutils.strings import randchars

from keg.db import db
from keg_elements.extensions import lazy_gettext as _


class utcnow(expression.FunctionElement):
    type = DateTime()


@compiles(utcnow, 'postgresql')
def _pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


@compiles(utcnow, 'mssql')
def _ms_utcnow(element, compiler, **kw):
    return "GETUTCDATE()"


@compiles(utcnow, 'sqlite')
def _sqlite_utcnow(element, compiler, **kw):
    return "CURRENT_TIMESTAMP"


@wrapt.decorator
def no_autoflush(wrapped, instance, args, kwargs):
    autoflush = db.session.autoflush
    db.session.autoflush = False
    try:
        return wrapped(*args, **kwargs)
    finally:
        db.session.autoflush = autoflush


def random_numeric(column):
    fractional_digits = column.type.scale
    whole_digits = column.type.precision - fractional_digits

    # only use about half the digits to make arithmetic done with this less likely to overflow
    max_whole = 10 ** math.ceil(whole_digits / 2.0) - 1

    whole = random.randint(-max_whole, max_whole)

    fractional = Decimal(random.randint(0, 10 ** fractional_digits - 1)) / 10 ** fractional_digits
    return fractional + whole


def validate_unique_exc(exc, constraint_name=None):
    return _validate_unique_msg(db.engine.dialect.name, str(exc), constraint_name)


def _validate_unique_msg(dialect, msg, constraint_name=None):
    """
        Does the heavy lifting for validate_unique_exception().

        Broken out separately for easier unit testing.  This function takes string args.
    """
    if constraint_name is not None and dialect != 'sqlite' and constraint_name not in msg:
        return False

    if dialect == 'postgresql':
        return 'duplicate key value violates unique constraint' in msg
    elif dialect == 'mssql':
        return 'Cannot insert duplicate key' in msg
    elif dialect == 'sqlite':
        return 'UNIQUE constraint failed' in msg
    else:
        raise ValueError('is_unique_exc() does not yet support dialect: %s' % dialect)


@contextlib.contextmanager
def raises_unique_exc(constraint_name):
    with pytest.raises(sa.exc.IntegrityError) as exc:
        yield
    assert validate_unique_exc(exc.value, constraint_name)


@contextlib.contextmanager
def raises_check_exc(contraint_name):
    with pytest.raises(sa.exc.IntegrityError) as exc:
        yield
    assert _is_check_const(db.engine.dialect.name, str(exc.value), contraint_name)


def _is_check_const(dialect, msg, constraint_name):
    if dialect == 'mssql':
        return 'conflicted with the CHECK constraint' in msg and constraint_name in msg
    elif dialect == 'sqlite':
        return (
            'CHECK constraint {} failed'.format(constraint_name) in msg
            or 'CHECK constraint failed' in msg
        )
    elif dialect == 'postgresql':
        return 'violates check constraint' in msg and constraint_name in msg
    else:
        raise ValueError('is_constraint_exc() does not yet support dialect: %s' % dialect)


def randemail(length, randomizer=randchars):
    """Generate a random email address at the given length.
    :param length: must be at least 7 or the function will throw a ValueError.
    :param randomizer: is a function for generating random characters. It must have an identical
                      interface to `randchars`. The default function is `randchars`.
    """
    if length < 7:
        raise ValueError(_('length must be at least 7'))

    half = (length - 2 - 3) / 2.0  # 2 characters for @ and . and 3 for TLD
    return (randomizer(int(math.floor(half)), 'alphanumeric')
            + '@' + randomizer(int(math.ceil(half)), 'alphanumeric')
            + '.' + randomizer(3, 'alpha'))


def session_commit():
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def session_flush():
    try:
        db.session.flush()
    except Exception:
        db.session.rollback()
        raise


class CollectionUpdater(object):

    @no_autoflush
    def __init__(self, entity, attr_name, data):
        self.entity = entity
        self.attr_name = attr_name
        self.data = data
        self.collection = getattr(entity, attr_name)
        self.keep_children = set()

        ent_cls = entity.__class__
        queryable_attr = getattr(ent_cls, attr_name)
        # Unless they sent in the wrong type, rel_prop should be a
        # sqlalchemy.orm.properties.RelationshipProperty instance
        rel_prop = queryable_attr.property
        # now that we have the property, go through the mapper to get to the child entity class
        self.child_cls = rel_prop.mapper.class_

    @no_autoflush
    def find_child(self, data):
        """Find the child record associated with the related object"""
        child_entity_keys = self.child_cls.primary_keys()
        supplied_keys = set(data.get(column.key)
                            for column in child_entity_keys)

        if None in supplied_keys:
            return None

        for child in self.collection:
            record_keys = set(getattr(child, col.key)
                              for col in child_entity_keys)
            if record_keys == supplied_keys:
                return child
        return None

    @no_autoflush
    def update(self):
        """Update the objects associated with the entity"""
        for record in self.data:
            child = self.find_child(record)
            state = sa.inspect(child) if child else None

            if state and state.persistent:
                child.edit(_commit=False, **record)
            else:
                child = self.child_cls.add(_commit=False, **record)
                self.collection.append(child)

            self.keep_children.add(child)
        self.remove_unmodified()

    def remove_unmodified(self):
        remove_children = [child for child in self.collection if child not in self.keep_children]
        for child in remove_children:
            self.collection.remove(child)
