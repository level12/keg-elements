from __future__ import unicode_literals

from decimal import Decimal

import jinja2
from wtforms import ValidationError
import re

from keg_elements.extensions import lazy_gettext as _


class ValidateAlphaNumeric(object):
    """
        A validator to make sure than a form field contains only alphanumeric data

        usage example:
            import keg_elements.forms.validators as validators

            wtforms.StringField('AlphaNumeric', validators=[
                            validators.ValidateAlphaNumeric()
                        ])
    """
    regex = re.compile(r'^[a-zA-Z0-9]+$')

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        value = field.data

        message = self.message
        if message is None:
            message = field.gettext(_("Must only contain alphanumeric data."))

        if not self.regex.match(value):
            raise ValidationError(message)


def numeric(form, field):
    try:
        int(field.data)
    except ValueError:
        raise ValidationError(_('Value is not numeric.'))


class NumberScale(object):
    def __init__(self, scale=-1, message=None):
        self.scale = scale
        if not message:
            message = _(u'Field must have no more than {scale} decimal places.', scale=scale)
        self.message = message

    def __call__(self, form, field):
        # if the data is not decimal, don't do anything with it (could be an alpha string)
        if not isinstance(field.data, Decimal):
            return
        # use decimal's quantization to see if it's equal to field data at the full scale.
        #   If it isn't, user entered too many decimal places
        if field.data != field.data.quantize(Decimal('0.{}1'.format('0' * (self.scale - 1)))):
            raise ValidationError(self.message)


class ValidateUnique(object):
    """Ensure the field's value is unique from other values

    This validator requires a ``get_object_by_field(field)`` on the form which
    returns an object (if one exists) or None to check for uniqueness.

    Pass ``object_html_link`` to this validator's ``__init__`` to get an error
    message which contains a hyperlink to the existing object.

    .. note ::

        Combine with ``wtforms.validators.optional`` when a field is nullable to
        allow for None values.
    """
    field_flags = ('unique',)

    def __init__(self, object_html_link=None):
        self.object_html_link = object_html_link

    def get_obj(self, form):
        if hasattr(form, 'obj'):
            return form.obj
        if hasattr(form, '_obj'):
            return form._obj

        raise AttributeError(_(
            'Form must provide either `obj` or `_obj` property for uniqueness validation.'
        ))

    def __call__(self, form, field):
        obj = self.get_obj(form)
        other = form.get_object_by_field(field)

        both_exist = None not in (obj, other)
        same_record = both_exist and other == obj
        another_exists_with_value = obj is None and other  # new obj with existing object with value

        if (both_exist and not same_record) or another_exists_with_value:
            if self.object_html_link is None:
                text = _('This value must be unique but is already assigned.')
            else:
                text = _('This value must be unique but is already assigned to {link}.',
                         link=self.object_html_link(other))
            msg = jinja2.Markup(text)
            raise ValidationError(msg)
        return True
