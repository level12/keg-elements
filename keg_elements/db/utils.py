import math
import wrapt
import sqlalchemy as sa
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime

from blazeutils.strings import randchars

from keg.db import db


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


def validate_unique_exc(exc):
    return _validate_unique_msg(db.engine.dialect.name, str(exc))


def _validate_unique_msg(dialect, msg):
    """
        Does the heavy lifting for validate_unique_exception().

        Broken out separately for easier unit testing.  This function takes string args.
    """
    if 'IntegrityError' not in msg:
        raise ValueError('"IntegrityError" exception not found')
    if dialect == 'postgresql':
        if 'duplicate key value violates unique constraint' in msg:
            return True
    elif dialect == 'mssql':
        if 'Cannot insert duplicate key' in msg:
            return True
    elif dialect == 'sqlite':
        if 'UNIQUE constraint failed' in msg:
            return True
    else:
        raise ValueError('is_unique_exc() does not yet support dialect: %s' % dialect)
    return False


def randemail(length, randomizer=randchars):
    """Generate a random email address at the given length.
    :param length: must be at least 7 or the funuction will throw a ValueError.
    :param randomzer: is a function for generating random characters. It must have an identical
                      interface to `randchars`. The default function is `randchars`.
    """
    if length < 7:
        raise ValueError('length must be at least 7')

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
            return child if record_keys == supplied_keys else None

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
        self.remove_umodified()

    def remove_umodified(self):
        remove_children = [child for child in self.collection if child not in self.keep_children]
        for child in remove_children:
            self.collection.remove(child)
