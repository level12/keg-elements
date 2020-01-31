import codecs
import enum
import random

import sqlalchemy as sa

from keg.db import db
import keg_elements.db.mixins as mixins
import keg_elements.db.columns as columns


many_things_mapper = db.Table(
    'many_things_mapper',
    sa.Column('thing_id', sa.Integer, sa.ForeignKey('things.id')),
    sa.Column('many_id', sa.Integer, sa.ForeignKey('many_things.id'))
)


class Units(enum.Enum):
    feet = 'ft'
    inches = 'in'
    meters = 'm'


def random_scale_check():
    return 12.3456


class Thing(db.Model, mixins.DefaultMixin):
    __tablename__ = 'things'

    name = db.Column(db.Unicode(50), nullable=False)
    color = db.Column(db.Unicode, info=dict(randomdata='random_color'))
    scale_check = db.Column(db.Numeric(8, 4), info=dict(randomdata=random_scale_check))
    float_check = db.Column(db.Float)
    units = db.Column(sa.Enum(Units, name='enum_units'))

    @sa.ext.hybrid.hybrid_property
    def name_and_color(self):
        return '{}-{}'.format(self.name, self.color)

    @name_and_color.expression
    def name_and_color(cls):
        return cls.name + sa.sql.literal('-') + cls.color

    @classmethod
    def random_color(cls):
        return 'blue'


class RelatedThing(db.Model, mixins.DefaultMixin):
    __tablename__ = 'related_things'

    name = db.Column(db.Unicode(50), nullable=False)
    is_enabled = db.Column(db.Boolean, nullable=False, default=False,
                           server_default=sa.text('FALSE'))

    thing_id = sa.Column(sa.Integer, sa.ForeignKey(Thing.id), nullable=False)
    thing = sa.orm.relationship(lambda: Thing, backref=sa.orm.backref(
        'related_things',
        cascade='all, delete-orphan'
    ))

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


def super_secure_encrypt(data, key):
    return codecs.encode(data, 'rot_13').encode()


def super_secure_decrypt(data, key):
    return codecs.encode(data.decode(), 'rot_13')


class ColumnTester(db.Model, mixins.DefaultMixin):
    __tablename__ = 'column_tester'

    time_zone = db.Column(columns.TimeZoneType(length=100))
    encrypted1 = db.Column(columns.EncryptedUnicode(key=lambda: b'a' * 32))
    encrypted2 = db.Column(columns.EncryptedUnicode(key=b'b' * 32))
    encrypted3 = db.Column(columns.EncryptedUnicode(
        key=b'c' * 32,
        encrypt=super_secure_encrypt,
        decrypt=super_secure_decrypt
    ))


class AncillaryA(mixins.DefaultMixin, db.Model):
    __tablename__ = 'ancillary_as'

    thing_id = sa.Column(sa.Integer, sa.ForeignKey(Thing.id), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint('id', thing_id),
    )

    @classmethod
    def testing_create(cls, **kwargs):
        if 'thing_id' not in kwargs:
            kwargs['thing_id'] = Thing.testing_create().id

        return super(AncillaryA, cls).testing_create(**kwargs)


class AncillaryB(mixins.DefaultMixin, db.Model):
    __tablename__ = 'ancillary_bs'

    thing_id = sa.Column(sa.Integer, sa.ForeignKey(Thing.id), nullable=False)

    __table_args__ = (
        sa.UniqueConstraint('id', thing_id),
    )

    @classmethod
    def testing_create(cls, **kwargs):
        if 'thing_id' not in kwargs:
            kwargs['thing_id'] = Thing.testing_create().id

        return super(AncillaryB, cls).testing_create(**kwargs)


class UsesBoth(mixins.DefaultMixin, db.Model):
    __tablename__ = 'uses_boths'
    __table_args__ = (
        sa.ForeignKeyConstraint(
            ('thing_id', 'ancillary_a_id'),
            (AncillaryA.thing_id, AncillaryA.id)
        ),
        sa.ForeignKeyConstraint(
            ('thing_id', 'ancillary_b_id'),
            (AncillaryB.thing_id, AncillaryB.id)
        ),
    )

    thing_id = sa.Column(sa.Integer, nullable=False)
    ancillary_a_id = sa.Column(sa.Integer, nullable=False)
    ancillary_b_id = sa.Column(sa.Integer, nullable=False)

    @classmethod
    def testing_create(cls, **kwargs):
        if 'thing_id' not in kwargs:
            kwargs['thing_id'] = Thing.testing_create().id

        thing_id = kwargs['thing_id']

        if 'ancillary_a_id' not in kwargs:
            kwargs['ancillary_a_id'] = AncillaryA.testing_create(thing_id=thing_id).id

        if 'ancillary_b_id' not in kwargs:
            kwargs['ancillary_b_id'] = AncillaryB.testing_create(thing_id=thing_id).id

        return super(UsesBoth, cls).testing_create(**kwargs)


class ConstraintTester(mixins.DefaultMixin, db.Model):
    unique1 = sa.Column(sa.Integer, nullable=False, unique=True)
    unique2 = sa.Column(sa.Integer, nullable=False)

    check = sa.Column(sa.Integer, nullable=False)

    __tablename__ = 'constraint_tester'
    __table_args__ = (
        sa.UniqueConstraint(unique2, name='uq_constraint_tester_unique2'),
        sa.CheckConstraint(check <= 100, name='ck_constraint_tester_check'),
    )

    @classmethod
    def testing_create(cls, **kwargs):
        kwargs.setdefault('check', random.randint(0, 100))
        return super(ConstraintTester, cls).testing_create(**kwargs)


class HardDeleteParent(mixins.DefaultMixin, db.Model):
    __tablename__ = 'hard_delete_parent'


class SoftDeleteTester(mixins.SoftDeleteMixin, mixins.DefaultMixin, db.Model):
    __tablename__ = 'softdelete_tester'

    hdp_id = sa.Column(
        sa.Integer,
        sa.ForeignKey(HardDeleteParent.id),
        nullable=False
    )
    hdp = sa.orm.relationship(
        HardDeleteParent, backref=sa.orm.backref('sdts', cascade='all,delete-orphan'))

    @classmethod
    def testing_create(cls, **kwargs):
        kwargs['hdp_id'] = kwargs.get('hpd_id') or HardDeleteParent.testing_create().id
        return super().testing_create(**kwargs)
