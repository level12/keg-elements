from wtforms import fields as wtfields
from wtforms.validators import input_required

from keg_elements.forms import Form


class DemoForm(Form):
    my_field = wtfields.StringField('Input field', validators=[input_required()])
