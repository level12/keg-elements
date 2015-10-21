import math
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
