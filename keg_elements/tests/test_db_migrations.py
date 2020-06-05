import io
from contextlib import contextmanager
from copy import copy

import pytest
from alembic import op

import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext

from keg.db import db
from keg_elements.db import migrations


class Context(MigrationContext):
    def statements(self):
        stmts = self.output_buffer.getvalue().splitlines(keepends=False)
        return [s for s in stmts if s]


class TestMigrationUtils:
    @contextmanager
    def get_context(self, dialect_name, engine=None, as_sql=True):
        dialect = getattr(sa.dialects, dialect_name).dialect()
        output = io.StringIO()
        context = Context(
            dialect,
            engine,
            dict(as_sql=as_sql, output_buffer=output, literal_binds=as_sql)
        )
        op._proxy = Operations(context)
        yield context
        del op._proxy

    def test_not_nullable_column_postgres(self):
        with self.get_context('postgresql') as context:
            migrations.add_non_nullable_column(
                op,
                'test_table',
                sa.Column('test_column', sa.Unicode),
                default_value='foo',
                schema='abc'
            )
        assert context.statements() == [
            'ALTER TABLE abc.test_table ADD COLUMN test_column VARCHAR;',
            'UPDATE abc.test_table SET test_column=\'foo\';',
            'ALTER TABLE abc.test_table ALTER COLUMN test_column SET NOT NULL;'
        ]

    def test_not_nullable_column_postgres_default_query(self):
        with self.get_context('postgresql') as context:
            column = sa.Column('test_column', sa.Unicode)

            migrations.add_non_nullable_column(
                op,
                'test_table',
                column,
                default_value_query=sa.table('test_table', copy(column)).update().values(
                    test_column=sa.func.random()),
            )
        assert context.statements() == [
            'ALTER TABLE test_table ADD COLUMN test_column VARCHAR;',
            'UPDATE test_table SET test_column=random();',
            'ALTER TABLE test_table ALTER COLUMN test_column SET NOT NULL;'
        ]

    def test_not_nullable_column_default_query_and_default(self):
        with self.get_context('postgresql'):
            column = sa.Column('test_column', sa.Unicode)

            with pytest.raises(ValueError,
                               match='You may not pass both default_value and default_value_query'):
                migrations.add_non_nullable_column(
                    op,
                    'test_table',
                    column,
                    default_value_query=sa.table('test_table', copy(column)).update().values(
                        test_column=sa.func.random()),
                    default_value='foo'
                )

    def test_not_nullable_column_no_default(self):
        with self.get_context('postgresql'):
            column = sa.Column('test_column', sa.Unicode)

            with pytest.raises(ValueError,
                               match='Must provide either default_value or default_value_query'):
                migrations.add_non_nullable_column(
                    op,
                    'test_table',
                    column
                )

    def test_not_nullable_column_mssql(self):
        with self.get_context('mssql') as context:
            migrations.add_non_nullable_column(
                op,
                'test_table',
                sa.Column('test_column', sa.Unicode),
                default_value='foo',
                schema='abc'
            )
        assert context.statements() == [
            'ALTER TABLE abc.test_table ADD test_column NVARCHAR(max) NULL;',
            'GO',
            'UPDATE abc.test_table SET test_column=N\'foo\';',
            'GO',
            'ALTER TABLE abc.test_table ALTER COLUMN test_column NVARCHAR(max) NOT NULL;',
            'GO'
        ]

    def test_not_nullable_column_sqlite(self):
        with self.get_context('sqlite') as context:
            migrations.add_non_nullable_column(
                op,
                'test_table',
                sa.Column('test_column', sa.Unicode),
                default_value='foo',
                schema='abc'
            )
        assert context.statements() == [
            'ALTER TABLE abc.test_table ADD COLUMN test_column VARCHAR;',
            'UPDATE abc.test_table SET test_column=\'foo\';',
            'ALTER TABLE abc.test_table ALTER COLUMN test_column SET NOT NULL;'
        ]

    def test_postgres_update_enum_options(self):
        with self.get_context('postgresql') as context:
            migrations.postgres_update_enum_options(
                op,
                [
                    ('public', 'test_table1', 'test_column1'),
                    ('abc', 'test_table2', 'test_column2'),
                ],
                'test_enum',
                ['value1', 'value2']
            )

        assert context.statements() == [
            'ALTER TABLE public.test_table1 ALTER COLUMN test_column1 TYPE VARCHAR USING test_column1::text;',  # noqa: E501
            'ALTER TABLE public.test_table1 ALTER COLUMN test_column1 DROP DEFAULT;',
            'ALTER TABLE abc.test_table2 ALTER COLUMN test_column2 TYPE VARCHAR USING test_column2::text;',  # noqa: E501
            'ALTER TABLE abc.test_table2 ALTER COLUMN test_column2 DROP DEFAULT;',
            'DROP TYPE test_enum;',
            "CREATE TYPE test_enum AS ENUM ('value1', 'value2');",
            'ALTER TABLE public.test_table1 ALTER COLUMN test_column1 TYPE test_enum USING test_column1::test_enum;',  # noqa: E501
            'ALTER TABLE abc.test_table2 ALTER COLUMN test_column2 TYPE test_enum USING test_column2::test_enum;',  # noqa: E501
        ]

    @pytest.mark.skipif(db.engine.dialect.name != 'postgresql', reason='Postgres only test')
    def test_postgres_get_enum_values(self):
        with self.get_context('postgresql', engine=db.engine, as_sql=False):
            sa.Enum('value1', 'value2', 'value3', name='test_enum').create(op.get_bind())

            results = migrations.postgres_get_enum_values(
                op,
                'test_enum',
            )
        assert results == ['value1', 'value2', 'value3']
