import datetime as dt
import operator
import random

from keg.db import db
from sqlalchemy_utils import ArrowType, EmailType
import arrow
import blazeutils.strings
import pytz
import six
import sqlalchemy as sa

import keg_elements.decorators as decor
import keg_elements.db.columns as columns
import keg_elements.db.utils as dbutils


might_commit = decor.keyword_optional('_commit', after=dbutils.session_commit, when_missing=True)
might_flush = decor.keyword_optional('_flush', after=dbutils.session_flush)


class DefaultColsMixin(object):
    id = sa.Column('id', sa.Integer, primary_key=True)
    created_utc = sa.Column(ArrowType, nullable=False, default=arrow.now,
                            server_default=dbutils.utcnow())
    updated_utc = sa.Column(ArrowType, nullable=False, default=arrow.now, onupdate=arrow.now,
                            server_default=dbutils.utcnow())


class MethodsMixin:
    def from_dict(self, data):
        """Update the instance with the passed information in `data`.

        `from_dict` will also update relationships either, 1:1, 1:N, M:M.

        .. note::
            `from_dict` intentionally does not commit and for related entities
            turns off auto flushing. This is to prevent premature flushes with
            incomplete objects
        """

        @dbutils.no_autoflush
        def update_related(key, value, prop):
            """Update the entity based on the type of relationship it is"""
            related_class = prop.mapper.class_

            if prop.uselist:
                new_list = list()
                for row in value:
                    obj = related_class.add_or_edit(row, _commit=False)
                    new_list.append(obj)
                setattr(self, key, new_list)
            else:
                setattr(self, key, related_class.add_or_edit(value, _commit=False))

        mapper = self.__mapper__
        entity_props = {attr.key: attr for attr in mapper.attrs}

        for key, value in six.iteritems(data):
            prop = entity_props.get(key)
            is_column = isinstance(prop, sa.orm.properties.ColumnProperty)
            is_relationship = isinstance(prop, sa.orm.properties.RelationshipProperty)

            if prop is None:
                continue
            elif is_column:
                setattr(self, key, value)
            elif is_relationship:
                update_related(key, value, prop)
            else:
                raise NotImplementedError(
                    'Updating {} property types is not implemented.')

    def to_dict(self, exclude=frozenset(), hybrids=frozenset()):
        """Covert the object properties to a dictionary.

        :param exclude: a list of columns to ignore
        :param hybrids: a list of the hybrid properties to include in the dictionary.
        :returns: a dictionary representation of the object

        .. note: By default hybrid properties are not included in the returned dict. To add a hybrid
        property to the returned dict pass a list of the property names and they will be included.
        """
        data = dict((name, getattr(self, name))
                    for name in self.column_names()
                    if name not in exclude)

        for hybrid in hybrids:
            data[hybrid] = getattr(self, hybrid)

        return data

    @classmethod
    def column_names(cls):
        return {col.key for col in cls.__mapper__.columns}

    @classmethod
    def primary_keys(cls):
        return cls.__table__.primary_key.columns

    @might_commit
    @might_flush
    @classmethod
    def add(cls, **kwargs):
        obj = cls()
        obj.from_dict(kwargs)
        db.session.add(obj)
        return obj

    @might_commit
    @might_flush
    @classmethod
    def delete(cls, oid):
        """Delete an object from the session

        :param oid: the object identifier, normally the primary key
        :rtype: bool
        :return: The result of the operation
        """
        obj = cls.query.get(oid)

        if obj is None:
            return False

        db.session.delete(obj)
        return True

    @might_commit
    @classmethod
    def delete_cascaded(cls):
        cls.query.delete(synchronize_session=False)
        db.session.expire_all()

    @might_commit
    @might_flush
    @classmethod
    def edit(cls, oid=None, **kwargs):
        try:
            primary_keys = oid or [kwargs.get(x.name)
                                   for x in cls.primary_keys()
                                   if x is not None]
        except KeyError:
            raise AttributeError('No primary key was found in `oid` or `kwargs`'
                                 ' for which to retrieve the object to edit')

        obj = cls.query.get(primary_keys)
        obj.from_dict(kwargs)
        return obj

    @classmethod
    def get_by(cls, **kwargs):
        """Returns the instance of this class matching the given criteria or
        None if there is no record matching the criteria.

        If multiple records are returned, an exception is raised.
        """
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get_where(cls, *clauses):
        """
        Returns the instance of this class matching the given clause(s) or None
        if there is no record matching the criteria.

        If multiple records are returned, an exception is raised.
        """
        return cls.query.filter(*clauses).one_or_none()

    @classmethod
    def pairs(cls, key_field, value_field, order_by=(), query=None,
              items=None):
        """Return a list of two item tuples

        :param key_field: string representing the key
        :param value_field: string representing the value
        :param order_by: iterable of columns to order the query by
        :param query: a base query from which to generate the pairs
        :param items: a function which takes one record returned by query and
                      returns the tuple object
        """

        items = items if items else operator.attrgetter(key_field, value_field)
        query = query or cls.query
        result = query.order_by(*order_by).all()

        return [items(obj) for obj in result]

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

        NUMERIC_HIGH, NUMERIC_LOW = kwargs.pop('_numeric_defaults_range', (-100, 100))

        insp = sa.inspection.inspect(cls)

        skippable = lambda column: (column.key in kwargs      # skip fields already in kwargs
                                    or column.foreign_keys    # skip foreign keys
                                    or column.server_default  # skip fields with server defaults
                                    or column.default         # skip fields with defaults
                                    or column.primary_key     # skip any primary key
                                    )

        for column in (col for col in insp.columns if not skippable(col)):
            try:
                kwargs[column.key] = cls.random_data_for_column(
                    column, NUMERIC_HIGH, NUMERIC_LOW)
            except ValueError:
                pass

        return cls.add(**kwargs)

    @classmethod
    def random_data_for_column(cls, column, numeric_high, numeric_low):
        if isinstance(column.type, sa.types.Enum):
            return random.choice(column.type.enums)
        elif isinstance(column.type, sa.types.Boolean):
            return random.choice([True, False])
        elif isinstance(column.type, sa.types.Integer):
            return random.randint(numeric_high, numeric_low)
        elif isinstance(column.type, sa.types.Numeric):
            return random.uniform(numeric_high, numeric_low)
        elif isinstance(column.type, sa.types.Date):
            return dt.date.today()
        elif isinstance(column.type, sa.types.DateTime):
            return dt.datetime.utcnow()
        elif isinstance(column.type, ArrowType):
            return arrow.utcnow()
        elif isinstance(column.type, EmailType):
            return dbutils.randemail(min(column.type.length or 50, 50))
        elif isinstance(column.type, columns.TimeZoneType):
            return random.choice(pytz.common_timezones)
        elif isinstance(column.type, (sa.types.String, sa.types.Unicode)):
            return blazeutils.strings.randchars(min(column.type.length or 25, 25))
        raise ValueError('No randomization for this column type')

    @might_commit
    @might_flush
    @classmethod
    def add_or_edit(cls, data):
        """Creates or updates the record associated with `data`

        `add_or_edit` supports multiple primary key entities.
        """
        if isinstance(data, db.Model) or not data:
            return data

        primary_keys = [data.get(x.name) for x in cls.primary_keys() if x
                        is not None]
        obj = cls.query.get(primary_keys)

        return (cls.add(_commit=False, **data)
                if obj is None
                else cls.edit(primary_keys, _commit=False, **data))

    def update_collection(self, attr_name, data):
        dbutils.CollectionUpdater(self, attr_name, data).update()


class DefaultMixin(DefaultColsMixin, MethodsMixin):
    pass
