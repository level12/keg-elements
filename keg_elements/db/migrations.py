import copy

import sqlalchemy as sa


def add_non_nullable_column(op, table_name, column, default_value=None, default_value_query=None,
                            schema=None):
    """
    Create a new non-nullable column

    :param op: The operational module or batch operator imported from alembic.op
    :param table_name: The name of the table to add the column to
    :param column: An SQLAlchemy column declaration (i.e. `sa.Column()` expression)
    :param default_value: The initial value for the column.
        Cannot be used with the `default_value_query`
    :param default_value_query: An update query that sets the column value for all rows.
        Cannot be used with `default_value`
    :param schema: The name of the table's schema
    :return:
    """
    if default_value is None and default_value_query is None:
        raise ValueError('Must provide either default_value or default_value_query')
    if default_value is not None and default_value_query is not None:
        raise ValueError('You may not pass both default_value and default_value_query')

    column = copy.copy(column)
    column.nullable = True

    op.add_column(table_name, column, schema=schema)

    if default_value_query is not None:
        op.execute(default_value_query)
    else:
        op.execute(
            sa.Table(
                table_name,
                sa.MetaData(),
                sa.Column(column.name, column.type),
                schema=schema
            ).update().values({column.name: default_value})
        )

    op.alter_column(
        table_name,
        column.name,
        schema=schema,
        nullable=False,
        existing_type=column.type
    )


def postgres_update_enum_options(op, table_column_list, enum_name, new_values):
    """
    Update an enum's options within the migration transaction. In Postgres updating an enum is
    typically not permitted within a transaction. However, dropping and re-creating the type works.

    Note: this function will remove the default value on every column it updates so you will need
    to reset any server-side defaults after running this function.

    :param op: The operational module or batch operator imported from alembic.op
    :param table_column_list: A list of three item tuples (schema, table_name, column_name) for
        each column where this enum is used
    :param enum_name: The name of the enum type
    :param new_values: A list of the enum's updated values
    """
    old_type = sa.Enum(name=enum_name)
    new_type = sa.Enum(*new_values, name=enum_name)

    for schema, table_name, column_name in table_column_list:
        op.alter_column(
            table_name,
            column_name,
            schema=schema,
            type_=sa.Unicode,
            postgresql_using=f'{column_name}::text',
            server_default=None
        )

    old_type.drop(op.get_bind(), checkfirst=False)
    new_type.create(op.get_bind(), checkfirst=False)

    for schema, table_name, column_name in table_column_list:
        op.alter_column(
            table_name,
            column_name,
            schema=schema,
            type_=new_type,
            postgresql_using=f'{column_name}::{enum_name}'
        )


def postgres_get_enum_values(op, enum_name, schema=None):
    """
    Get a list of values for an existing enum type.

    :param op: The operational module or batch operator imported from alembic.op
    :param enum_name: The name of the enum type
    :return: A list of the enum's values
    """

    if schema:
        enum_name = f'{schema}.{enum_name}'

    results = op.get_bind().execute(
        sa.select([
            sa.func.unnest(
                sa.func.enum_range(
                    sa.text('NULL::{}'.format(enum_name))
                )
            )
        ])
    )
    return [x for x, in results.fetchall()]
