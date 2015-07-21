from __future__ import absolute_import, unicode_literals

from keg.db import db


class Thing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(50), nullable=False)
    color = db.Column(db.Unicode)
    scale_check = db.Column(db.Numeric(8, 4))
