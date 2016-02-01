from __future__ import absolute_import, unicode_literals

from keg.db import db


class Thing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), nullable=False)
    color = db.Column(db.Unicode)
    scale_check = db.Column(db.Numeric(8, 4))


class ThingWithRequiredBoolean(db.Model):
    __tablename__ = 'required_boolean_table'
    id = db.Column(db.Integer, primary_key=True)

    nullable_boolean = db.Column(db.Boolean, nullable=True)
    required_boolean = db.Column(db.Boolean, nullable=False)
    required_boolean_with_default = db.Column(db.Boolean, nullable=False, default=False)
    required_boolean_with_server_default = db.Column(db.Boolean, nullable=False,
                                                     server_default='false')
