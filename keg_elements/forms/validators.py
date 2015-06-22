from wtforms import ValidationError


def validate_numeric(form, field):
    try:
        int(field.data)
    except ValueError:
        raise ValidationError('Value is not numeric.')
