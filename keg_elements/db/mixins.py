import datetime as dt
import operator
import random

import arrow
import blazeutils.strings
import pytz
import six
import sqlalchemy as sa
import wrapt
from blazeutils import tolist
from keg.db import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import ArrowType, EmailType

import keg_elements.db.columns as columns
import keg_elements.db.utils as dbutils
import keg_elements.decorators as decor
from keg_elements.extensions import lazy_gettext as _

might_commit = decor.keyword_optional('_commit', after=dbutils.session_commit, when_missing=True)
might_flush = decor.keyword_optional('_flush', after=dbutils.session_flush)


@wrapt.decorator
def kwargs_match_entity(wrapped, instance, args, kwargs):
    """
    Asserts that the kwargs passed to the wrapped method match the columns/relationships
    of the entity.
    """
    if kwargs.get('_check_kwargs', True):
        insp = sa.inspection.inspect(instance)

        # Only allow kwargs that correspond to a column or relationship on the entity
        allowed_keys = {col.key for col in insp.columns} | set(insp.relationships.keys())

        # Ignore kwargs starting with "_"
        kwarg_keys = set(key for key in kwargs if not key.startswith('_'))
        extra_kwargs = kwarg_keys - allowed_keys
        assert not extra_kwargs, _('Unknown column or relationship names in kwargs: {kwargs!r}',
                                   kwargs=sorted(extra_kwargs))
    return wrapped(*args, **kwargs)


class DefaultColsMixin(object):
    id = sa.Column('id', sa.Integer, primary_key=True)
    created_utc = sa.Column(ArrowType, nullable=False, default=arrow.utcnow,
                            server_default=dbutils.utcnow())
    updated_utc = sa.Column(ArrowType, nullable=False, default=arrow.utcnow, onupdate=arrow.utcnow,
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
                    _('Updating property types is not implemented.'))

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
            raise AttributeError(_('No primary key was found in `oid` or `kwargs`'
                                   ' for which to retrieve the object to edit'))

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

    @kwargs_match_entity
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

        numeric_range = kwargs.pop('_numeric_defaults_range', None)

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
                    column, numeric_range)
            except ValueError:
                pass

        return cls.add(**kwargs)

    @classmethod
    def random_data_for_column(cls, column, numeric_range):
        if 'randomdata' in column.info:
            if type(column.info['randomdata']) is str:
                # assume randomdata the is name of a method on the class
                callable = getattr(cls, column.info['randomdata'])
                data = callable()
                return data

            return column.info['randomdata']()

        default_range = (-100, 100) if numeric_range is None else numeric_range
        if isinstance(column.type, sa.types.Enum):
            return random.choice(column.type.enums)
        elif isinstance(column.type, sa.types.Boolean):
            return random.choice([True, False])
        elif isinstance(column.type, sa.types.Integer):
            return random.randint(*default_range)
        elif isinstance(column.type, sa.types.Float):
            return random.uniform(*default_range)
        elif isinstance(column.type, sa.types.Numeric):
            if numeric_range is not None or column.type.scale is None:
                return random.uniform(*default_range)
            return dbutils.random_numeric(column)
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
        raise ValueError(_('No randomization for this column type'))

    @classmethod
    def testing_set_related(cls, kwargs, model,
                            *testing_create_args, **testing_create_kwargs):
        """Create a related object for testing, if it is not specified in kwargs.

        Designed to be used by `testing_create`. A common issue is that related
        test records need to be set up with the test entity instance, but they
        could be specified already in kwargs. In addition, relationships already
        specified may be given on the relationship attribute or the foreign-key
        field.

        This method takes existing `testing_create` kwargs and the related
        entity, and makes the necessary updates.

        Relationship name is generated from the given entity by default, but may
        be passed in as a `_relationship_name` keyword argument. The foreign key
        field is assumed to be the relationship name with an `_id` suffix, but
        may be specified with the `_relationship_field` keyword argument.

        Any additional args/kwargs are passed to the given model's `testing_create`.
        """
        relationship_name = testing_create_kwargs.pop(
            '_relationship_name',
            blazeutils.strings.case_cw2us(model.__name__),
        )
        relationship_field = testing_create_kwargs.pop(
            '_relationship_field',
            '{}_id'.format(relationship_name),
        )

        for attr_name in (relationship_name, relationship_field):
            if not hasattr(cls, attr_name):
                print(cls, attr_name)
                raise Exception(
                    'testing_set_related expects "{}" on class {}'.format(
                        attr_name,
                        cls.__name__,
                    )
                )

        # generic logic to respect existing kwargs setting on either field
        if not {relationship_name, relationship_field} & set(kwargs.keys()):
            kwargs[relationship_name] = model.testing_create(
                *testing_create_args,
                **testing_create_kwargs
            )

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


class HardDeleteProhibitedError(Exception):
    pass


class SoftDeleteMixin:
    """SoftDeleteMixin alters the way deletes are performed by adding a deleted_utc column

    A soft-delete doesn't actually remove the row, instead, it adds a time to the ``deleted_utc``
    column which indicates when it was deleted.

    .. note (NZ): This can complicate unique constraints, joins, and general business logic, but is
    rather useful when you can't delete an object outright because it is connected to other
    permanent objects which should never be deleted.

    .. note (NZ): ``SoftDeleteMixin`` should appear before ``MethodsMixin`` as the parent class of
    the created entity so that the ``delete`` and ``testing_create`` methods are called in the
    correct order.

        class MyTable(SoftDeleteMixin, MethodsMixin, Model):
            column1 = sa.Column(sa.Numeric)


    .. note (NZ): ``testing_create`` takes a special ``_is_deleted`` flag which enables you to
    create an already deleted record or you can pass ``deleted_utc`` manually.

    .. note (NZ): There is a new event registered within SQLAlchemy to prevent accidental deletions
    of entities that inherit from this class.

    This event is not fired for bulk operations (``session.delete``) and makes it possible to delete
    everything.

    To have finer grained control of this event for every entity, you can override the behavior by
    implementing ``before_delete_event`` on the entity.

        class MyEntity(SoftDeleteMixin, Model):
            column1 = sa.Column(sa.Numeric)

            # `mapper` and `connection` are passed through from the parent handler
            def before_delete_event(self, mapper, connection):
                # .. custom logic
    """

    deleted_utc = sa.Column(ArrowType, nullable=True)

    @might_commit
    @might_flush
    @classmethod
    def delete(cls, oid):
        """Add the deleted_utc timestamp

        :param oid: the object identifier, normally the primary key
        :rtype: bool
        :return: The result of the operation
        """
        return cls.query.filter(cls.id == oid).update(
            {"deleted_utc": arrow.utcnow()},
            synchronize_session=False
        ) > 0

    @might_commit
    @might_flush
    @classmethod
    def testing_create(cls, *args, _is_deleted=False, **kwargs):
        kwargs.setdefault('deleted_utc', arrow.utcnow() if _is_deleted else None)
        return super().testing_create(*args, **kwargs)

    @staticmethod
    def sqla_before_delete_event(mapper, connection, target):
        if hasattr(target, 'before_delete_event'):
            target.before_delete_event(mapper, connection)
        else:
            raise HardDeleteProhibitedError(
                'Unable to completely delete {}, this object implements soft-deletes.'.format(target))  # noqa

    @might_commit
    @classmethod
    def delete_cascaded(cls):
        cls.query.delete(synchronize_session=False)


sa.event.listen(SoftDeleteMixin, 'before_delete', SoftDeleteMixin.sqla_before_delete_event,
                propagate=True)


class LookupMixin(SoftDeleteMixin):
    """Provides a base for id/label pair tables, used in one-to-many relationships.

    Based on SoftDeleteMixin, so any lookup record that is deleted/deactivated is
    still available for existing records.

    A code field is provided for developer reference in code, so a changeable label
    does not need to be hard-coded for lookup.

    Developer expectations:
    - LookupMixin will precede DefaultMixin or MethodsMixin in entity base classes
    - Only active labels will be listed for linking to new related records
    - `include_ids` will be used for ensuring existing records preserve lookup
    """

    label = sa.Column(sa.Unicode(255), nullable=False, unique=True)
    code = sa.Column(sa.Unicode(255))

    @hybrid_property
    def is_active(self):
        return self.deleted_utc is not None

    @is_active.expression
    def is_active(cls):
        return sa.sql.case([(cls.deleted_utc.is_(None), sa.true())], else_=sa.false())

    @classmethod
    def _active_query(cls, include_ids=None, order_by=None):
        if order_by is None:
            order_by = cls.label

        if include_ids:
            include_ids = tolist(include_ids)
            clause = sa.sql.or_(
                cls.is_active == sa.true(),
                cls.id.in_(include_ids)
            )
        else:
            clause = cls.is_active == sa.true()

        return cls.query.filter(clause).order_by(order_by)

    @classmethod
    def list_active(cls, include_ids=None, order_by=None):
        return cls._active_query(include_ids, order_by).all()

    @classmethod
    def pairs_active(cls, include_ids=None, order_by=None):
        query = cls._active_query(include_ids, order_by)
        return cls.pairs('id', 'label', query=query)

    @classmethod
    def get_by_label(cls, label):
        return cls.get_by(label=label)

    @classmethod
    def get_by_code(cls, code):
        return cls.get_by(code=code)

    def __repr__(self):
        return '<{} {}:{}>'.format(self.__class__.__name__, self.id, self.label)
