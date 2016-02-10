from __future__ import absolute_import, unicode_literals

from pyquery import PyQuery as pq
from keg_elements.forms import FieldMeta, Form, ModelForm, SelectField
import keg_elements.forms as ke_forms
import six
from werkzeug.datastructures import MultiDict
import wtforms as wtf
from wtforms import validators
import wtforms_components

import kegel_app.model.entities as ents


class FormBase(object):
    form_cls = None
    entity_cls = None

    def compose_meta(self, fields_meta_cls=None, **data):
        assert self.entity_cls is not None, 'must set entity_cls on {}'\
            .format(self.__class__.__name__)

        class _ComposedForm(ModelForm):
            class Meta:
                model = self.entity_cls

            if fields_meta_cls:
                FieldsMeta = fields_meta_cls
            else:
                class FieldsMeta:
                    __default__ = FieldMeta
        return _ComposedForm(MultiDict(data))

    def create_form(self, **data):
        return self.form_cls(MultiDict(data))

    def assert_invalid(self, **data):
        form = self.create_form(**data)
        assert not form.validate()
        return form

    def assert_valid(self, **data):
        form = self.create_form(**data)
        assert form.validate(), form.errors
        return form


class FruitForm(Form):
    fruit = SelectField(validators=[validators.Optional()],
                        choices=[('apple', 'apple'), ('banana', 'banana')])
    letter = SelectField(validators=[validators.Optional()],
                         choices=[('a', 'a'), ('b', 'b'), ('', 'blank')], add_blank_choice=False)
    letter2 = SelectField(validators=[validators.InputRequired()], choices=[('a', 'a'), ('b', 'b')])
    number = SelectField(validators=[validators.Optional()], choices=[(1, '1'), (0, '0')])
    numstr = SelectField(validators=[validators.Optional()], choices=[('1', '1'), ('0', '0')],
                         coerce=six.text_type)


class TestSelectField(FormBase):
    form_cls = FruitForm

    def test_blank_choice_rendering(self):
        form = FruitForm(csrf_enabled=False)
        fruit_options = pq(form.fruit())('option')
        assert fruit_options.length == 3
        assert fruit_options.eq(0).attr('value') == ''
        assert fruit_options.eq(1).attr('value') == 'apple'

        letter_options = pq(form.letter())('option')
        assert letter_options.length == 3

    def test_blank_choice_submit(self):
        form = self.assert_valid(**{'fruit': '', 'letter': '', 'letter2': 'a'})

        assert form.fruit.data is None
        assert form.letter.data == ''

    def test_blank_choice_required(self):
        form = self.assert_invalid(**{'letter2': ''})
        assert form.letter2.errors == ['This field is required.']

        form = self.assert_valid(**{'letter2': 'b'})

    def test_blank_choice_coerce(self):
        self.assert_valid(**{'letter2': 'a', 'number': '1'})

        # make sure we can override the int helper by passing through an explicit coerce
        self.assert_valid(**{'letter2': 'a', 'numstr': '1'})


class TestRequiredBoolRadioField(FormBase):
    class RequiredBoolMockForm(Form):
        is_competent = ke_forms.RequiredBoolRadioField()
        statement_is = ke_forms.RequiredBoolRadioField(true_label='True', false_label='False')

    form_cls = RequiredBoolMockForm

    def test_required_bool_radio_rendering(self):
        form = self.RequiredBoolMockForm(csrf_enabled=False)
        is_competent_labels = pq(form.is_competent())('label')
        assert is_competent_labels.length == 2
        assert is_competent_labels.eq(0).text() == 'Yes'
        assert is_competent_labels.eq(1).text() == 'No'

        statement_is_labels = pq(form.statement_is())('label')
        assert statement_is_labels.length == 2
        assert statement_is_labels.eq(0).text() == 'True'
        assert statement_is_labels.eq(1).text() == 'False'

    def test_required_bool_radio_is_required(self):
        form = self.assert_invalid()
        assert form.is_competent.errors == ['This field is required.']
        assert form.statement_is.errors == ['This field is required.']

        form = self.assert_invalid(**{'is_competent': 'True'})
        assert form.is_competent.errors == []
        assert form.statement_is.errors == ['This field is required.']

        form = self.assert_invalid(**{'statement_is': 'True'})
        assert form.is_competent.errors == ['This field is required.']
        assert form.statement_is.errors == []

        form = self.assert_valid(**{'is_competent': 'False', 'statement_is': 'False'})


class TestDefaultTypeOfRequiredBooleanField(FormBase):
    entity_cls = ents.ThingWithRequiredBoolean

    def test_field_types(self):
        form = self.compose_meta(csrf_enabled=False)
        assert type(form.nullable_boolean) == wtf.fields.BooleanField
        assert type(form.required_boolean) == ke_forms.RequiredBoolRadioField
        assert type(form.required_boolean_with_default) == wtf.fields.BooleanField
        assert type(form.required_boolean_with_server_default) == ke_forms.RequiredBoolRadioField


class TestFieldMeta(FormBase):
    entity_cls = ents.Thing

    def test_required_unspecified(self):
        form = self.compose_meta()
        assert form.name.flags.required
        assert not form.color.flags.required

    def test_required_true(self):
        class Temp:
            __default__ = FieldMeta(required=True)
        form = self.compose_meta(Temp)
        assert form.name.flags.required
        assert form.color.flags.required

    def test_required_false(self):
        class Temp:
            __default__ = FieldMeta(required=False)
        form = self.compose_meta(Temp)
        assert not form.name.flags.required
        assert not form.color.flags.required

    def test_widget_no_override(self):
        form = self.compose_meta(csrf_enabled=False)
        assert type(form.color.widget) == wtforms_components.widgets.TextInput

    def test_widget_override(self):
        class WidgetOverrideFieldsMeta:
            __default__ = FieldMeta
            color = FieldMeta(widget=wtf.widgets.TextArea())

        form = self.compose_meta(fields_meta_cls=WidgetOverrideFieldsMeta, csrf_enabled=False)
        assert type(form.color.widget) == wtf.widgets.TextArea

    def test_extra_validators(self):
        class ExtraValidatorsFieldsMeta:
            def _is_roy(form, field):
                if field.data not in {'red', 'orange', 'yellow'}:
                    raise wtf.validators.ValidationError('Not a ROY color')

            __default__ = FieldMeta
            color = FieldMeta(extra_validators=[_is_roy])

        form = self.compose_meta(fields_meta_cls=ExtraValidatorsFieldsMeta, csrf_enabled=False,
                                 name='Test', color='red')
        assert form.validate()

        form = self.compose_meta(fields_meta_cls=ExtraValidatorsFieldsMeta, csrf_enabled=False,
                                 name='Test', color='muave')
        assert not form.validate()
        assert set(form.color.errors) == {'Not a ROY color'}


class TestValidators(FormBase):
    entity_cls = ents.Thing

    def test_numeric_scale_check(self):
        # too many places
        form = self.compose_meta(scale_check='0.11111')
        form.validate()
        assert form.scale_check.errors == ['Field must have no more than 4 decimal places.']

        # equal to data type
        form = self.compose_meta(scale_check='0.1111')
        form.validate()
        assert form.scale_check.errors == []

        # fewer places than data type
        form = self.compose_meta(scale_check='0.111')
        form.validate()
        assert form.scale_check.errors == []

        # integer
        form = self.compose_meta(scale_check='5')
        form.validate()
        assert form.scale_check.errors == []

        # test that other validation happens when type is wrong
        form = self.compose_meta(scale_check='aaa')
        form.validate()
        assert form.scale_check.errors == ['Not a valid decimal value']


class FeaturesForm(Form):
    name = wtf.StringField(validators=[validators.required()])
    color = wtf.StringField()


class NumbersSubForm(wtf.Form):
    number = wtf.StringField(validators=[validators.required()])
    color = wtf.StringField()


class NumbersForm(Form):
    numbers = wtf.FieldList(wtf.FormField(NumbersSubForm), min_entries=2)
    numbers2 = wtf.FieldList(wtf.StringField(), min_entries=2)


class TestFieldsToDict(FormBase):

    def test_simple(self):
        self.form_cls = FeaturesForm
        form = self.assert_invalid(color='blue')
        expected = {
            'csrf_token': {'data': '', 'errors': []},
            'name': {'data': '', 'errors': ['This field is required.']},
            'color': {'data': 'blue', 'errors': []},
        }
        assert form.fields_todict() == expected

    def test_simple_json(self):
        self.form_cls = FeaturesForm
        form = self.assert_invalid(color='blue')
        expected = {
            'csrf_token': {'data': '', 'errors': []},
            'name': {'data': '', 'errors': ['This field is required.']},
            'color': {'data': 'blue', 'errors': []},
        }
        fields_data = form.fields_todict()
        assert fields_data == expected

    def test_field_to_dict_field(self):
        form = NumbersSubForm()
        form.validate()
        assert ke_forms.field_to_dict(form.number) == \
            {'data': None, 'errors': ['This field is required.']}

    def test_field_to_dict_select(self):
        form = FruitForm(letter='b')
        form.validate()
        assert ke_forms.field_to_dict(form.letter) == \
            {'data': 'b', 'errors': []}
        assert ke_forms.field_to_dict(form.letter2) == \
            {'data': None, 'errors': ['This field is required.']}

    def test_field_to_dict_fieldlist(self):
        form = NumbersForm()
        form.validate()
        expected = [{'data': None, 'errors': []}, {'data': None, 'errors': []}]
        assert ke_forms.field_to_dict(form.numbers2) == expected

    def test_field_to_dict_form_fieldlist(self):
        data = {
            'numbers-0-number': '123',
            'numbers-1-color': 'blue',
        }
        form = NumbersForm(MultiDict(data))
        form.validate()
        expected = [
            {'number': {'data': '123', 'errors': []}, 'color': {'data': '', 'errors': []}},
            {'number': {'data': '', 'errors': ['This field is required.']},
                'color': {'data': 'blue', 'errors': []}},
        ]
        assert ke_forms.field_to_dict(form.numbers) == expected

    def test_nested(self):
        self.form_cls = NumbersForm
        data = {
            'numbers-0-number': '123',
            'numbers-1-color': 'blue'
        }
        form = self.assert_invalid(**data)
        expected = {
            'csrf_token': {'data': '', 'errors': []},
            'numbers': [
                {'number': {'data': '123', 'errors': []}, 'color': {'data': '', 'errors': []}},
                {'number': {'data': '', 'errors': ['This field is required.']},
                    'color': {'data': 'blue', 'errors': []}},
            ],
            'numbers2': [{'data': '', 'errors': []}, {'data': '', 'errors': []}]
        }
        fields_dict = form.fields_todict()
        assert fields_dict == expected, fields_dict
