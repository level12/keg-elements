from wtforms import ValidationError


def numeric(form, field):
    try:
        int(field.data)
    except ValueError:
        raise ValidationError('Value is not numeric.')
