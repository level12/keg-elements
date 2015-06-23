from __future__ import absolute_import, unicode_literals

import json

from pyquery import PyQuery as pq
from keg_elements.forms import FieldMeta, Form, ModelForm, SelectField
import keg_elements.forms as ke_forms
import six
from werkzeug.datastructures import MultiDict
import wtforms as wtf
from wtforms import validators

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
            'csrf_token': {'data': '', '_errors': []},
            'name': {'data': '', '_errors': ['This field is required.']},
            'color': {'data': 'blue', '_errors': []},
        }
        assert form.fields_todict() == expected

    def test_simple_json(self):
        self.form_cls = FeaturesForm
        form = self.assert_invalid(color='blue')
        expected = {
            'csrf_token': {'data': '', '_errors': []},
            'name': {'data': '', '_errors': ['This field is required.']},
            'color': {'data': 'blue', '_errors': []},
        }
        fields_json = form.fields_todict(as_json=True)
        fields_data = json.loads(fields_json)
        assert fields_data == expected

    def test_field_to_dict_field(self):
        form = NumbersSubForm()
        form.validate()
        assert ke_forms.field_to_dict(form.number) == \
            {'data': None, '_errors': ['This field is required.']}

    def test_field_to_dict_fieldlist(self):
        form = NumbersForm()
        form.validate()
        expected = [{'data': None, '_errors': []}, {'data': None, '_errors': []}]
        assert ke_forms.field_to_dict(form.numbers2) == expected

    def test_field_to_dict_form_fieldlist(self):
        data = {
            'numbers-0-number': '123',
            'numbers-1-color': 'blue',
        }
        form = NumbersForm(MultiDict(data))
        form.validate()
        expected = [
            {'number': {'data': '123', '_errors': []}, 'color': {'data': '', '_errors': []}},
            {'number': {'data': '', '_errors': ['This field is required.']},
                'color': {'data': 'blue', '_errors': []}},
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
            'csrf_token': {'data': '', '_errors': []},
            'numbers': [
                {'number': {'data': '123', '_errors': []}, 'color': {'data': '', '_errors': []}},
                {'number': {'data': '', '_errors': ['This field is required.']},
                    'color': {'data': 'blue', '_errors': []}},
            ],
            'numbers2': [{'data': '', '_errors': []}, {'data': '', '_errors': []}]
        }
        fields_dict = form.fields_todict()
        assert fields_dict == expected, fields_dict
