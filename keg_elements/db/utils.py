import contextlib
import math
import random
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime
import sqlalchemy_utils as sautils

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


def has_column(orm_cls_or_table, column_name):
    """Searches an entity for a column having the given key.

    While a column's default key is the entity attribute name, a column may be given
    an explicit key instead. This method uses sqlalchemy-utils to find the column.
    """
    for column in sautils.get_columns(orm_cls_or_table):
        if column.key == column_name:
            return True

    return False


def range_from_column(column):
    if 'random_range' in column.info:
        rand_range = column.info['random_range']
        if not isinstance(rand_range, tuple) or len(rand_range) != 2:
            raise Exception(
                'random_range info for {} expected to be tuple with low and high'.format(
                    column.key
                ))
        return rand_range

    if 'random_magnitude' in column.info:
        rand_mag = column.info['random_magnitude']
        return (-rand_mag, rand_mag)

    return None


def random_int(column, default_range):
    """Find a random number that satisfies the given column's data size and meta info.

    :param column: SA column to find a range by type/info and generate a random number.
    :param default_range: Tuple. Fallback range if type/info does not provide a range.
    :returns: Random integer.
    """
    column_range = range_from_column(column)
    if column_range:
        return random.randint(*column_range)

    if type(column.type) is sa.Integer:
        exponent = 31
    elif type(column.type) is sa.SmallInteger:
        exponent = 15
    elif type(column.type) is sa.BigInteger:
        exponent = 63
    else:
        return random.randint(*default_range)
    magnitude = (2 ** exponent) - 1
    return random.randint(-magnitude, magnitude)


def random_numeric(column):
    """Find a random number that satisfies the given column's precision and scale."""
    column_range = range_from_column(column)
    if column_range:
        return random.uniform(*column_range)

    fractional_digits = column.type.scale
    whole_digits = column.type.precision - fractional_digits

    # only use about half the digits to make arithmetic done with this less likely to overflow
    max_whole = 10 ** math.ceil(whole_digits / 2.0) - 1

    whole = random.randint(-max_whole, max_whole)

    fractional = Decimal(random.randint(0, 10 ** fractional_digits - 1)) / 10 ** fractional_digits
    return fractional + whole


def validate_unique_exc(exc, constraint_name=None):
    """Check the given exception to see if it indicates a duplicate key error.

    Supports SQLite, PostgreSQL, and MSSQL dialects.

    Optionally provide a constraint_name kwarg for a stricter test.
    """
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
    """pytest helper and context manager to ensure an exception result is a duplicate key error."""
    import pytest
    with pytest.raises(sa.exc.IntegrityError) as exc:
        yield
    assert validate_unique_exc(exc.value, constraint_name)


@contextlib.contextmanager
def raises_check_exc(contraint_name):
    """pytest helper and context manager to ensure an exception result is a check constraint
       error."""
    import pytest
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
    """Commit the db session, and roll back if there is a failure.

    Raises the exception that caused the rollback."""
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def session_flush():
    """Flush the db session, and roll back if there is a failure.

    Raises the exception that caused the rollback."""
    try:
        db.session.flush()
    except Exception:
        db.session.rollback()
        raise


class CollectionUpdater(object):
    """Update a collection attribute of a model object.

    Takes a model object, the attribute name of the collection to be updated, and
    the data to update the collection with. If a record in the given data matches
    a record in the collection, the record is edited. Otherwise, the given record is
    added to the collection.

    All records in the collection that are not included in the given data are removed
    from the collection.
    """

    def __init__(self, entity, attr_name, data):
        self.entity = entity
        self.attr_name = attr_name
        self.data = data
        self.keep_children = set()
        ent_cls = entity.__class__

        with db.session.no_autoflush:
            self.collection = getattr(entity, attr_name)
            queryable_attr = getattr(ent_cls, attr_name)
            # Unless they sent in the wrong type, rel_prop should be a
            # sqlalchemy.orm.properties.RelationshipProperty instance
            rel_prop = queryable_attr.property
            # now that we have the property, go through the mapper to get to the child entity class
            self.child_cls = rel_prop.mapper.class_

    def find_child(self, data):
        """Find the child record associated with the related object"""
        with db.session.no_autoflush:
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

    def update(self):
        """Update the objects associated with the entity

        Objects are matched by keys found in supplied data, if any. If no keys are supplied,
        the existing objects in the collection are removed, and new records are constructed
        from the data.

        The way SQLAlchemy handles collection updates presents a limitation for collections
        having unique constraints. If we drop/recreate the record with the same unique value,
        we will get a unique constraint exception. To work around this, we cache info from
        matched objects in state, then remove/flush objects first. This clears the table for
        the new records from adds/edits.
        """
        with db.session.no_autoflush:
            to_add = []
            to_edit = []
            for record in self.data:
                child = self.find_child(record)
                state = sa.inspect(child) if child else None

                if state and state.persistent:
                    to_edit.append((child, record))
                else:
                    to_add.append(record)

                self.keep_children.add(child)

            self._remove_unmodified()
            session_flush()

            for child, record in to_edit:
                child.edit(_commit=False, **record)

            for record in to_add:
                child = self.child_cls.add(_commit=False, **record)
                self.collection.append(child)

    def _remove_unmodified(self):
        remove_children = [child for child in self.collection if child not in self.keep_children]
        for child in remove_children:
            self.collection.remove(child)
