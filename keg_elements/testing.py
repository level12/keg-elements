from collections import namedtuple

from keg import current_app
import six
import sqlalchemy as sa
from sqlalchemy_utils import ArrowType

from keg_elements.sentry import SentryClient
from .db.utils import validate_unique_exc
from .db.mixins import DefaultColsMixin

ColumnCheck = namedtuple('ColumnCheck', 'name, required, fk, unique, timestamp')
ColumnCheck.__new__.__defaults__ = (True, None, None, None)


class DontCare(object):  # pragma: no cover
    """A placeholder object that can conform to almost anything and is always
    equal to anything it is compared against.

    Examples:

        assert [1, 2, 3] == [1, DontCare(), 3]
    """
    __eq__ = lambda *_: True
    __ne__ = lambda *_: False
    __repr__ = lambda *_: '_'

    __getattr__ = lambda *_: DontCare()
    __getitem__ = lambda *_: DontCare()
    __call__ = lambda *a, **kw: DontCare()


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
    def column_check_generator(cls):
        for col_check in cls.column_checks or []:
            yield col_check
        if cls.timestamp_cols:
            createdts_col_name, updatedts_col_name = cls.timestamp_cols
            yield ColumnCheck(createdts_col_name, timestamp='create')
            yield ColumnCheck(updatedts_col_name, timestamp='update')

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

    def test_column_null(self):
        for col_check in self.column_check_generator():
            col = getattr(self.entity_cls, col_check.name)
            assert col.nullable != col_check.required, \
                'Expected column "{}" to match null requirement'.format(col.name)

    def test_column_unique(self):
        for col_check in self.column_check_generator():
            col = getattr(self.entity_cls, col_check.name)
            assert col.unique == col_check.unique, 'Expected column "{}" to have unique={}'.format(
                col.name, col_check.unique)

    def test_column_fk(self):
        for col_check in self.column_check_generator():
            col = getattr(self.entity_cls, col_check.name)
            fk_count = len(col.foreign_keys)
            if col_check.fk:
                # normalize `fk` into a set
                if isinstance(col_check.fk, six.string_types):
                    # 'foo.bar' => {'foo.bar'}
                    # 'foo.bar,baz.qux' => {'foo.bar', 'baz.qux'}
                    # 'foo.bar, baz.qux' => {'foo.bar', 'baz.qux'}
                    fk_set = {partial.strip() for partial in col_check.fk.split(',')}

                elif isinstance(col_check.fk, set):
                    fk_set = col_check.fk

                else:
                    # ['foo.bar', 'baz.qux'] => {'foo.bar', 'baz.qux'}
                    fk_set = set(col_check.fk)

                assert fk_count == len(fk_set), 'FK count does not match for {}'.format(col.name)
                assert fk_set == {fk._get_colspec() for fk in col.foreign_keys}, \
                    'FK set does not match for {}'.format(col.name)

            else:
                assert not fk_count, \
                    'Didn\'t expect column "{}" to have a foreign key'.format(col.name)

    def test_column_timestamp(self):
        for col_check in self.column_check_generator():
            if not col_check.timestamp:
                continue
            col = getattr(self.entity_cls, col_check.name)
            if not isinstance(col.type, (ArrowType, sa.DateTime)):
                raise AssertionError(
                    'Column "{}" is not a recognized timestamp type.'.format(col.name))
            assert col.default
            if col_check.timestamp == 'update':
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

    def check_unique_constraint(self, **kwargs):
        self.entity_cls.testing_create(**kwargs)
        try:
            self.entity_cls.testing_create(**kwargs)
            raise AssertionError('Uniqueness error was not encountered.')
        except Exception as e:
            if not validate_unique_exc(e):
                raise


class SentryCapture:
    def __enter__(self):
        SentryClient.__log_reports__ = True
        SentryClient.__report_log__ = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        SentryClient.__log_reports__ = False

    @property
    def reports(self):
        return SentryClient.__report_log__
