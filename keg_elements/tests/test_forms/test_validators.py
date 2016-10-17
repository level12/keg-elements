import pytest
import wtforms
import keg_elements.forms.validators as validators


class Form():
    def __init__(self, obj):
        self.obj = obj

    def get_object_by_field(self, field):
        return 1


class TestUniqueValidator(object):
    def test_unique_validator(self):
        field = wtforms.fields.StringField('thing')
        validator = validators.ValidateUnique(object_html_link=lambda field: 'link')

        assert validator(Form(1), field) is True

        with pytest.raises(wtforms.ValidationError,
                           message=('This valuue must be unique bit is already '
                                    'assigned link.')):
            assert validator(Form(2), field)
