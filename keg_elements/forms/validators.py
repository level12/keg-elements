from decimal import Decimal

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
