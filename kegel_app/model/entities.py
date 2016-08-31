import sqlalchemy as sa

from keg.db import db
import keg_elements.db.mixins as mixins
import keg_elements.db.columns as columns


many_things_mapper = db.Table(
    'many_things_mapper',
    sa.Column('thing_id', sa.Integer, sa.ForeignKey('things.id')),
    sa.Column('many_id', sa.Integer, sa.ForeignKey('many_things.id'))
)


class Thing(db.Model, mixins.DefaultMixin):
    __tablename__ = 'things'

    name = db.Column(db.Unicode(50), nullable=False)
    color = db.Column(db.Unicode)
    scale_check = db.Column(db.Numeric(8, 4))

    @sa.ext.hybrid.hybrid_property
    def name_and_color(self):
        return '{}-{}'.format(self.name, self.color)

    @name_and_color.expression
    def name_and_color(cls):
        return cls.name + sa.sql.literal('-') + cls.color


class RelatedThing(db.Model, mixins.DefaultMixin):
    __tablename__ = 'related_things'

    name = db.Column(db.Unicode(50), nullable=False)
    is_enabled = db.Column(db.Boolean, nullable=False, default=False,
                           server_default=sa.text('FALSE'))

    thing_id = sa.Column(sa.Integer, sa.ForeignKey(Thing.id), nullable=False)
    thing = sa.orm.relationship(lambda: Thing, backref='related_things')

    @classmethod
    def testing_create(cls, **kwargs):
        kwargs['thing'] = kwargs.get('thing') or Thing.testing_create()
        return super(RelatedThing, cls).testing_create(**kwargs)


class ManyToManyThing(db.Model, mixins.DefaultMixin):
    __tablename__ = 'many_things'

    name = db.Column(db.Unicode(50), nullable=False)

    things = sa.orm.relationship(lambda: Thing,
                                 secondary=many_things_mapper,
                                 backref='manys')


class ThingWithRequiredBoolean(db.Model, mixins.DefaultMixin):
    __tablename__ = 'required_boolean_table'

    nullable_boolean = db.Column(db.Boolean, nullable=True)
    required_boolean = db.Column(db.Boolean, nullable=False)
    required_boolean_with_default = db.Column(db.Boolean, nullable=False, default=False)
    required_boolean_with_server_default = db.Column(db.Boolean, nullable=False,
                                                     server_default='false')


class MultiplePrimaryKeys(db.Model, mixins.DefaultMixin):
    __tablename__ = 'multikey_table'

    other_pk = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50))


class ColumnTester(db.Model, mixins.DefaultMixin):
    __tablename__ = 'column_tester'

    time_zone = db.Column(columns.TimeZoneType(length=100))
