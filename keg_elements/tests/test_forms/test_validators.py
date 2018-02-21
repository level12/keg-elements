import jinja2
import pytest
import wtforms
from werkzeug.datastructures import MultiDict

import keg_elements.forms.validators as validators
from keg_elements.forms import ModelForm


class UniqueForm(ModelForm):
    uq_field = wtforms.fields.StringField('thing', validators=[
        validators.ValidateUnique(object_html_link=lambda field: 'link')])

    def get_object_by_field(self, field):
        return 1 if field.data == '1' else None


class TestUniqueValidator(object):
    def test_validation_passes(self):
        form = UniqueForm(MultiDict({'uq_field': '1'}), obj=1)
        assert form.uq_field.validate(form) is True

        form = UniqueForm(MultiDict({'uq_field': '2'}), obj=1)
        assert form.uq_field.validate(form) is True

    def test_validation_fails(self):
        form = UniqueForm(MultiDict({'uq_field': '1'}))
        assert form.uq_field.validate(form) is False
        assert form.uq_field.errors == [
            jinja2.Markup('This value must be unique but is already assigned to link.')
        ]

        form = UniqueForm(MultiDict({'uq_field': '1'}), obj=2)
        assert form.uq_field.validate(form) is False
        assert form.uq_field.errors == [
            jinja2.Markup('This value must be unique but is already assigned to link.')
        ]

    def test_no_object_link_provided(self):
        class Form(ModelForm):
            uq_field = wtforms.fields.StringField('thing', validators=[validators.ValidateUnique()])

            def get_object_by_field(self, field):
                return 1 if field.data == '1' else None

        form = Form(MultiDict({'uq_field': '1'}))
        assert form.uq_field.validate(form) is False
        assert form.uq_field.errors == [
            jinja2.Markup('This value must be unique but is already assigned.')
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
