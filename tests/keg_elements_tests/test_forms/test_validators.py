import markupsafe
import pytest
from werkzeug.datastructures import MultiDict
import wtforms

from keg_elements.forms import ModelForm
import keg_elements.forms.validators as validators


class UniqueForm(ModelForm):
    uq_field = wtforms.fields.StringField(
        'thing',
        validators=[validators.ValidateUnique(object_html_link=lambda field: 'link')],
    )

    def get_object_by_field(self, field):
        return 1 if field.data == '1' else None


class TestUniqueValidator:
    def test_validation_passes(self):
        form = UniqueForm(MultiDict({'uq_field': '1'}), obj=1)
        assert form.uq_field.validate(form) is True

        form = UniqueForm(MultiDict({'uq_field': '2'}), obj=1)
        assert form.uq_field.validate(form) is True

    def test_validation_fails(self):
        form = UniqueForm(MultiDict({'uq_field': '1'}))
        assert form.uq_field.validate(form) is False
        assert form.uq_field.errors == [
            markupsafe.Markup('This value must be unique but is already assigned to link.'),
        ]

        form = UniqueForm(MultiDict({'uq_field': '1'}), obj=2)
        assert form.uq_field.validate(form) is False
        assert form.uq_field.errors == [
            markupsafe.Markup('This value must be unique but is already assigned to link.'),
        ]

    def test_no_object_link_provided(self):
        class Form(ModelForm):
            uq_field = wtforms.fields.StringField('thing', validators=[validators.ValidateUnique()])

            def get_object_by_field(self, field):
                return 1 if field.data == '1' else None

        form = Form(MultiDict({'uq_field': '1'}))
        assert form.uq_field.validate(form) is False
        assert form.uq_field.errors == [
            markupsafe.Markup('This value must be unique but is already assigned.'),
        ]

    def test_get_obj(self):
        class Form:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        validator = validators.ValidateUnique()

        assert validator.get_obj(Form(obj='foo')) == 'foo'
        assert validator.get_obj(Form(_obj='foo')) == 'foo'

        with pytest.raises(AttributeError) as exc:
            validator.get_obj(Form())

        assert str(exc.value) == (
            'Form must provide either `obj` or `_obj` property for uniqueness validation.'
        )


class TestAlphaNumericValidator:
    def test_alphanumeric(self):
        message = 'Must only contain alphanumeric data.'

        class AlphaNumericMockForm(wtforms.Form):
            alpha_numeric_field = wtforms.StringField(
                'AlphaNumeric',
                validators=[validators.ValidateAlphaNumeric()],
            )

        form = AlphaNumericMockForm(alpha_numeric_field='123456asb')
        form.validate()
        assert form.errors == {}

        form = AlphaNumericMockForm(alpha_numeric_field='123456')
        form.validate()
        assert form.errors == {}

        form = AlphaNumericMockForm(alpha_numeric_field='abcd')
        form.validate()
        assert form.errors == {}

        form = AlphaNumericMockForm(alpha_numeric_field='123456!')
        form.validate()
        assert form.errors['alpha_numeric_field'] == [message]

        form = AlphaNumericMockForm(alpha_numeric_field='123456!')
        form.validate()
        assert form.errors['alpha_numeric_field'] == [message]

        form = AlphaNumericMockForm(alpha_numeric_field='!212')
        form.validate()
        assert form.errors['alpha_numeric_field'] == [message]

        form = AlphaNumericMockForm(alpha_numeric_field=' ')
        form.validate()
        assert form.errors['alpha_numeric_field'] == [message]

        form = AlphaNumericMockForm(alpha_numeric_field='123dsaf4 ')
        form.validate()
        assert form.errors['alpha_numeric_field'] == [message]

        form = AlphaNumericMockForm(alpha_numeric_field=' 123afd4')
        form.validate()
        assert form.errors['alpha_numeric_field'] == [message]

        form = AlphaNumericMockForm(alpha_numeric_field='1 23fdas4')
        form.validate()
        assert form.errors['alpha_numeric_field'] == [message]

        form = AlphaNumericMockForm(alpha_numeric_field='åfasdf')
        form.validate()
        assert form.errors['alpha_numeric_field'] == [message]

    @pytest.mark.parametrize('value', [None, 'abc\n', 'abc\r\n', 'abc\ndef'])
    def test_rejects_none_and_newlines(self, value):
        class AlphaNumericMockForm(wtforms.Form):
            alpha_numeric_field = wtforms.StringField(
                'AlphaNumeric',
                validators=[validators.ValidateAlphaNumeric()],
            )

        form = AlphaNumericMockForm()
        form.alpha_numeric_field.data = value

        assert not form.validate()
        assert form.alpha_numeric_field.errors == ['Must only contain alphanumeric data.']


class TestNumericValidator:
    @pytest.mark.parametrize('value', [None, object(), float('inf'), float('nan'), 'not-a-number'])
    def test_invalid_values_are_validation_errors(self, value):
        class NumericMockForm(wtforms.Form):
            numeric_field = wtforms.Field(validators=[validators.numeric])

        form = NumericMockForm()
        form.numeric_field.data = value

        assert not form.validate()
        assert form.numeric_field.errors == ['Value is not numeric.']

    @pytest.mark.parametrize('value', [-1, 0, 1, '-1', '0', '1'])
    def test_valid_values(self, value):
        class NumericMockForm(wtforms.Form):
            numeric_field = wtforms.Field(validators=[validators.numeric])

        form = NumericMockForm()
        form.numeric_field.data = value

        assert form.validate()
