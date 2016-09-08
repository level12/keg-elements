from collections import namedtuple

from keg import current_app
import sqlalchemy as sa
from sqlalchemy_utils import ArrowType

from .db.utils import validate_unique_exc
from .db.mixins import DefaultColsMixin

ColumnCheck = namedtuple('ColumnCheck', 'name, required, fk, unique, timestamp')
ColumnCheck.__new__.__defaults__ = (True, None, None, None)


class EntityBase(object):
    entity_cls = None
    column_checks = None
    timestamp_cols = ('created_utc', 'updated_utc')
    # Set to: 'setup_class', 'setup', or None
    delete_all_on = 'setup_class'

    @classmethod
    def setup_class(cls):
        assert current_app.db_enabled, 'app.db_enabled is False'
        assert cls.entity_cls, 'The entity_cls attribute must be set.'
        assert cls.column_checks, 'column_checks should be defined for this entity'
        if cls.timestamp_cols:
            if cls.column_checks is None:
                cls.column_checks = []
            createdts_col_name, updatedts_col_name = cls.timestamp_cols
            cls.column_checks.append(ColumnCheck(createdts_col_name, timestamp='create'))
            cls.column_checks.append(ColumnCheck(updatedts_col_name, timestamp='update'))
        if cls.delete_all_on:
            cls.ent_delete_all()

    @classmethod
    def ent_delete_all(cls):
        if hasattr(cls.entity_cls, 'delete_cascaded'):
            cls.entity_cls.delete_cascaded()
        else:
            cls.entity_cls.delete_all()

    def setup(self):
        if self.delete_all_on == 'setup':
            self.ent_delete_all()

    def test_add(self):
        self.ent_delete_all()
        o = self.entity_cls.testing_create()
        assert self.entity_cls.query.count() == 1
        if hasattr(self.entity_cls, 'id'):
            assert o.id

    def check_column_null(self, col, is_required):
        assert col.nullable != is_required

    def check_column_unique(self, col, is_unique):
        assert col.unique == is_unique, 'Expected column "{}" to have unique={}'.format(
            col.name, is_unique)

    def check_column_fk(self, col, fk):
        fk_count = len(col.foreign_keys)
        if fk:
            assert fk_count == 1, 'check_column_fk() can not handle colums w/ multiple FKs'
            assert fk == list(col.foreign_keys)[0]._get_colspec()
        else:
            assert not fk_count, 'Didn\'t expect column "{}" to have a foreign key'.format(col.name)

    def check_column_timestamp(self, col, ts_type):
        if not isinstance(col.type, (ArrowType, sa.DateTime)):
            raise AssertionError('Column "{}" is not a recognized timestamp type.'.format(col.name))
        assert col.default
        if ts_type == 'update':
            assert col.onupdate, 'Column "{}" should have onupdate set'.format(col.name)
        assert col.server_default, 'Column "{}" should have server_default set'.format(col.name)

    def test_all_columns_are_constraint_tested(self):
        """Checks that all fields declared on entity are in the constraint tests"""

        expected_columns = [col.name for col in self.entity_cls.__table__.columns]
        constraint_columns = [col[0] for col in self.column_checks]
        inherited_columns = []

        # Even if the entity class is based (eventually) on DefaultColsMixin, polymorphic subclasses
        #   will not have the default cols, as the parent entity alone will have them
        if isinstance(self.entity_cls(), DefaultColsMixin) and not \
                getattr(self.entity_cls, '__mapper_args__', {}).get('polymorphic_identity', None):
            # Include columns from common import base classes
            for field in vars(DefaultColsMixin):

                # Ignore the usual __class__, __dict__, blah, blah blah
                if field.startswith('__'):
                    continue

                col = getattr(DefaultColsMixin, field)

                # Only consider SQLAlchemy columns
                if isinstance(col, sa.sql.schema.Column):
                    inherited_columns.append(field)

        combined_columns = set(constraint_columns + inherited_columns)
        if len(combined_columns) != len(expected_columns):

            missing = set(expected_columns) - combined_columns

            raise AssertionError(
                'Missing {} constraint tests for {}.'.format(
                    self.entity_cls.__name__,
                    ', '.join(missing))
            )

    def test_column_checks(self):
        if not self.column_checks:
            return
        for col_check in self.column_checks:
            col = getattr(self.entity_cls, col_check.name)
            yield self.check_column_null, col, col_check.required
            yield self.check_column_unique, col, col_check.unique
            yield self.check_column_fk, col, col_check.fk
            if col_check.timestamp:
                yield self.check_column_timestamp, col, col_check.timestamp

    def check_unique_constraint(self, **kwargs):
        self.entity_cls.testing_create(**kwargs)
        try:
            self.entity_cls.testing_create(**kwargs)
            raise AssertionError('Uniqueness error was not encountered.')
        except Exception as e:
            if not validate_unique_exc(e):
                raise
