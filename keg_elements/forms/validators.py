from decimal import Decimal

import jinja2
from wtforms import ValidationError


def numeric(form, field):
    try:
        int(field.data)
    except ValueError:
        raise ValidationError('Value is not numeric.')


class NumberScale(object):
    def __init__(self, scale=-1, message=None):
        self.scale = scale
        if not message:
            message = u'Field must have no more than {} decimal places.'.format(scale)
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

    def __call__(self, form, field):
        obj = getattr(form, 'obj')
        other = form.get_object_by_field(field)

        both_exist = None not in (obj, other)
        same_record = both_exist and other == obj
        another_exists_with_value = obj is None and other  # new obj with existing object with value

        if (both_exist and not same_record) or another_exists_with_value:
            link = (' to {}.'.format(self.object_html_link(other))
                    if hasattr(self, 'object_html_link') else '.')
            msg = jinja2.Markup('This value must be unique but is already assigned'
                                '{}'.format(link))
            raise ValidationError(msg)
        return True
