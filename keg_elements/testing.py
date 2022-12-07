import arrow
from collections import namedtuple
import datetime
from unittest import mock

from keg import current_app
from pyquery import PyQuery
import sqlalchemy as sa
from sqlalchemy_utils import ArrowType
from werkzeug.datastructures import MultiDict

from .db.utils import validate_unique_exc
from .db.mixins import DefaultColsMixin

ColumnCheck = namedtuple('ColumnCheck',
                         'name, required, fk, unique, timestamp, skip_callable_date_check')
"""Validator tuple used in ``EntityBase`` to check column spec for common cases.

:param name: Field name to check.
:param required: Non-nullable status to verify.
:param fk: Foreign key to verify, e.g. "foo.id". Multiple keys can be given as list, set, or CSV.
:param unique: If true, verifies ``unique`` kwarg passed to column.
:param timestamp: Can be ``True`` for creates and ``update`` for updates. Expects column defaults.
:param skip_callable_date_check: If true, date cols won't validate that default vals are callable.
"""
ColumnCheck.__new__.__defaults__ = (True, None, None, None, False)


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
    """Base class for data model tests.

    Class attributes:

        entity_cls: SQLAlchemy entity class to test.

        column_checks: Iterable of ColumnCheck instances to use in tests. An instance
        for every field except id is expected for verification, and a test will fail if that
        expectation is not met. Note, created/updated timestamp columns have checks
        automatically generated and do not need to be specified by the developer.

        timestamp_cols: Defaults to ('created_utc', 'updated_utc'), the timestamp columns.

        delete_all_on: When to delete all records. Default "setup_class". Can also be "setup"
        or None.
    """
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

    def setup_method(self):
        if self.delete_all_on == 'setup':
            self.ent_delete_all()

    def test_add(self):
        self.ent_delete_all()
        o = self.entity_cls.fake()
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
                if isinstance(col_check.fk, str):
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

    def test_column_date_is_callable(self):
        for col_check in self.column_check_generator():
            if col_check.skip_callable_date_check:
                continue
            col = getattr(self.entity_cls, col_check.name)
            if not isinstance(col.type, (sa.Date, sa.DateTime, ArrowType)):
                continue
            datetypes = (datetime.date, datetime.datetime, arrow.Arrow)
            if col.default and isinstance(col.default.arg, datetypes):
                raise AssertionError(f'Column {col.name} default value is set to an instantiated'
                                     f' date type, this is probably not what you want.')
            if col.onupdate and isinstance(col.onupdate.arg, datetypes):
                raise AssertionError(f'Column {col.name} onupdate value is set to an instantiated'
                                     f' date type, this is probably not what you want.')

    def test_column_numeric_scale_precision_set(self):
        for col_check in self.column_check_generator():
            col = getattr(self.entity_cls, col_check.name)
            if isinstance(col.type, sa.Numeric) and not isinstance(col.type, sa.Float):
                assert col.type.precision is not None, \
                    'Column "{}" does not specify precision'.format(col.name)
                assert col.type.scale is not None, \
                    'Column "{}" does not specify scale'.format(col.name)

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
        self.entity_cls.fake(**kwargs)
        try:
            self.entity_cls.fake(**kwargs)
            raise AssertionError('Uniqueness error was not encountered.')
        except Exception as e:
            if not validate_unique_exc(e):
                raise


class FormBase(object):
    """Base class for testing forms. Assumes WTForms framework.

    Class attributes:

        form_cls: Form class to verify
    """
    form_cls = None

    def ok_data(self, **kwargs):
        """Returns data that should pass validation by default.

        Provided kwargs should override the default set of data.
        """
        return kwargs

    def test_disallowed_fields_not_present(self):
        """Most forms will not want to have the record timestamps as fields. Check that here."""
        form = self.create_form()
        assert "created_utc" not in form
        assert "updated_utc" not in form

    def test_ok_data_valid(self):
        """Assert that ``ok_data`` has valid data by default."""
        self.assert_valid()

    def create_form(self, obj=None, **kwargs):
        """Creates a CSRF-less form instance.

        Form data comes from ``ok_data`` with kwargs applied, or from a ``_form_data`` kwarg if
        that is provided (i.e. bypasses ``ok_data`` defaults).

        Object may be provided with the ``obj`` kwarg. Default None.
        """
        data = kwargs.pop('_form_data', self.ok_data(**kwargs))
        # attempt to disable CSRF here with a patch. This covers a majority of cases in testing
        with mock.patch.dict(current_app.config, WTF_CSRF_ENABLED=False):
            form = self.form_cls(MultiDict(data), obj=obj)

        return form

    def assert_invalid(self, **kwargs):
        """Create a form with the given kwargs, assert it is invalid, and return the form."""
        form = self.create_form(**kwargs)
        assert not form.validate(), "expected form errors"
        return form

    def assert_valid(self, **kwargs):
        """Create a form with the given kwargs, assert it is valid, and return the form."""
        form = self.create_form(**kwargs)
        assert form.validate(), form.errors
        return form

    def verify_field(
        self, name, label=None, required=False, choice_values=None, prefix=None, suffix=None
    ):
        """Create a form and verify a field's parameters are configured."""
        if required is not None:
            data = {name: ""}
            form = self.create_form(**data)
            field = form[name]
            form.validate()

            if required:
                assert "This field is required." in field.errors
            else:
                assert not field.errors, field.errors
        else:
            form = self.create_form()
            field = form[name]

        if hasattr(field, "choices"):
            if choice_values:
                assert choice_values == [choice[0] for choice in field.choices]

        if label:
            assert field.label.text == label

        if prefix or suffix:
            form = self.create_form()
            field = form[name]

            pq = PyQuery(field())
            if prefix:
                assert pq(".input-group-prepend").text() == prefix
            if suffix:
                assert pq(".input-group-append").text() == suffix
