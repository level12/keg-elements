from keg.db import db

import keg_elements.db.mixins as mixins


class DefaultMixin(mixins.MethodsMixin):
    pass


class Thing(db.Model, DefaultMixin):
    __tablename__ = 'things'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), nullable=False)
    color = db.Column(db.Unicode)
    scale_check = db.Column(db.Numeric(8, 4))


class ThingWithRequiredBoolean(db.Model, DefaultMixin):
    __tablename__ = 'required_boolean_table'

    id = db.Column(db.Integer, primary_key=True)

    nullable_boolean = db.Column(db.Boolean, nullable=True)
    required_boolean = db.Column(db.Boolean, nullable=False)
    required_boolean_with_default = db.Column(db.Boolean, nullable=False, default=False)
    required_boolean_with_server_default = db.Column(db.Boolean, nullable=False,
                                                     server_default='false')
