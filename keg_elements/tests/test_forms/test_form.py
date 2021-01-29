from __future__ import absolute_import, unicode_literals

import sys

from keg.db import db
import pytest
from pyquery import PyQuery as pq
import six
from werkzeug.datastructures import MultiDict
import wtforms as wtf
from wtforms import validators
import wtforms_components

import keg_elements.forms as ke_forms
import kegel_app.model.entities as ents
from keg_elements.forms import (
    FieldMeta,
    Form,
    ModelForm,
    RelationshipField,
    RelationshipMultipleField,
    SelectField,
)


class FormBase(object):
    form_cls = None
    entity_cls = None

    def compose_meta(self, fields_meta_cls=None, **data):
        assert self.entity_cls is not None, 'must set entity_cls on {}'\
            .format(self.__class__.__name__)

        class _ComposedForm(ModelForm):
            class Meta:
                model = self.entity_cls
                csrf = False

            if fields_meta_cls:
                FieldsMeta = fields_meta_cls
            else:
                class FieldsMeta:
                    __default__ = FieldMeta
        return _ComposedForm(MultiDict(data))

    def create_form(self, **data):
        form_cls = data.pop('form_cls', self.form_cls)
        return form_cls(MultiDict(data))

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
        form = FruitForm(meta={'csrf': False})
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

    def test_db_enum_default_choices(self):
        class ThingForm(ModelForm):
            class Meta:
                model = ents.Thing
                csrf = False

            class FieldsMeta:
                __default__ = FieldMeta

        form = ThingForm()
        assert form.status.choices == [
            (ents.ThingStatus.open, 'Open'),
            (ents.ThingStatus.closed, 'Closed'),
        ]
        assert form.status.coerce('open') is ents.ThingStatus.open

    def test_db_enum_override_choices(self):
        class ThingForm(ModelForm):
            class Meta:
                model = ents.Thing
                csrf = False

            class FieldsMeta:
                __default__ = FieldMeta
                status = FieldMeta(choices=[('1', 'Foo'), ('2', 'Bar')], coerce=str)

        form = ThingForm()
        assert form.status.choices == [
            ('1', 'Foo'),
            ('2', 'Bar'),
        ]
        assert form.status.coerce(1) == '1'


class TestRequiredBoolRadioField(FormBase):
    class RequiredBoolMockForm(Form):
        is_competent = ke_forms.RequiredBoolRadioField()
        statement_is = ke_forms.RequiredBoolRadioField(true_label='True', false_label='False')

    form_cls = RequiredBoolMockForm

    def test_required_bool_radio_rendering(self):
        form = self.RequiredBoolMockForm(meta={'csrf': False})
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
        form = self.compose_meta()
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
        form = self.compose_meta()
        assert type(form.color.widget) == wtforms_components.widgets.TextInput

    def test_widget_override(self):
        class WidgetOverrideFieldsMeta:
            __default__ = FieldMeta
            color = FieldMeta(widget=wtf.widgets.TextArea())

        form = self.compose_meta(fields_meta_cls=WidgetOverrideFieldsMeta)
        assert type(form.color.widget) == wtf.widgets.TextArea

    def test_extra_validators(self):
        class ExtraValidatorsFieldsMeta:
            def _is_roy(form, field):
                if field.data not in {'red', 'orange', 'yellow'}:
                    raise wtf.validators.ValidationError('Not a ROY color')

            __default__ = FieldMeta
            color = FieldMeta(extra_validators=[_is_roy])

        form = self.compose_meta(fields_meta_cls=ExtraValidatorsFieldsMeta,
                                 name='Test', color='red')
        assert form.validate()

        form = self.compose_meta(fields_meta_cls=ExtraValidatorsFieldsMeta,
                                 name='Test', color='mauve')
        assert not form.validate()
        assert set(form.color.errors) == {'Not a ROY color'}

    def test_coerce(self):
        class CoerceFieldsMeta:
            __default__ = FieldMeta
            units = FieldMeta(coerce=lambda x: ents.Units[x.lower()] if x else x,
                              choices=[(x, x.value) for x in ents.Units])

        form = self.compose_meta(fields_meta_cls=CoerceFieldsMeta, name='Test', units='FEET')
        assert isinstance(form.units, wtf.SelectField)
        assert form.validate()
        assert isinstance(form.units.data, ents.Units)
        assert form.units.data == ents.Units.feet

        # coerce not allowed for non-select fields
        class BadCoerceFieldsMeta:
            __default__ = FieldMeta
            name = FieldMeta(coerce=lambda x: x)
        with pytest.raises(ValueError) as exc:
            self.compose_meta(fields_meta_cls=BadCoerceFieldsMeta)
        assert str(exc.value) == '`coerce` argument may only be used for select fields'

    def test_default(self):
        class DefaultFieldsMeta:
            __default__ = FieldMeta
            name = FieldMeta(default='foo')

        form = self.compose_meta(fields_meta_cls=DefaultFieldsMeta)
        assert form.name.default == 'foo'
        assert form.color.default is None


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
        assert 'Not a valid decimal value' in form.scale_check.errors

    def test_numeric_range_check(self):
        message = 'Number must be between -9999.9999 and 9999.9999.'

        # too high
        form = self.compose_meta(scale_check='10000.0000')
        form.validate()
        assert form.scale_check.errors == [message]

        # too low
        form = self.compose_meta(scale_check='-10000.0000')
        form.validate()
        assert form.scale_check.errors == [message]

        # top limit
        form = self.compose_meta(scale_check='9999.9999')
        form.validate()
        assert form.scale_check.errors == []

        # bottom limit
        form = self.compose_meta(scale_check='-9999.9999')
        form.validate()
        assert form.scale_check.errors == []

    def test_validators_not_added_for_float(self):
        form = self.compose_meta(float_check=sys.float_info.max)
        form.validate()
        assert form.float_check.errors == []

        form = self.compose_meta(float_check=sys.float_info.min)
        form.validate()
        assert form.float_check.errors == []

        assert len(form.float_check.validators) == 1

    def test_numeric_scale_precision_required(self):
        with pytest.raises(ValueError, match='Numeric fields must specify precision and scale'):
            class TestForm1(ke_forms.ModelForm):
                class Meta:
                    model = ents.DefaultNumeric

        class TestForm2(ke_forms.ModelForm):
            class Meta:
                model = ents.DefaultNumeric
                exclude = ('number',)

            number = wtf.DecimalField('Number', validators=[])

    def test_length_validation_not_applied_for_enums(self):
        form = self.compose_meta()
        for validator in form.units.validators:
            assert not isinstance(validator, wtf.validators.Length)


class FeaturesForm(Form):
    name = wtf.StringField(validators=[validators.data_required()])
    color = wtf.StringField()


class NumbersSubForm(wtf.Form):
    number = wtf.StringField('Number', validators=[validators.data_required()])
    color = wtf.StringField('Color')


class NumbersForm(Form):
    numbers = wtf.FieldList(wtf.FormField(NumbersSubForm), min_entries=2)
    numbers2 = wtf.FieldList(wtf.StringField('Number'), min_entries=2)


class TestFieldsToDict(FormBase):

    def test_simple(self):
        self.form_cls = FeaturesForm
        form = self.assert_invalid(color='blue')
        expected = {
            'name': {
                'data': '',
                'errors': ['This field is required.'],
                'label': 'Name',
                'required': True,
            },
            'color': {
                'data': 'blue',
                'errors': [],
                'label': 'Color',
                'required': False
            },
        }
        assert form.fields_todict() == expected

    def test_simple_json(self):
        self.form_cls = FeaturesForm
        form = self.assert_invalid(color='blue')
        expected = {
            'name': {
                'data': '',
                'errors': ['This field is required.'],
                'label': 'Name',
                'required': True,
            },
            'color': {
                'data': 'blue',
                'errors': [],
                'label': 'Color',
                'required': False
            },
        }
        fields_data = form.fields_todict()
        assert fields_data == expected

    def test_field_to_dict_field(self):
        form = NumbersSubForm()
        form.validate()
        assert ke_forms.field_to_dict(form.number) == {
            'data': None,
            'errors': ['This field is required.'],
            'label': 'Number',
            'required': True
        }

    def test_field_to_dict_select(self):
        form = FruitForm(letter='b')
        form.validate()
        assert ke_forms.field_to_dict(form.letter) == \
            {'data': 'b', 'errors': [], 'label': 'Letter', 'required': False}
        assert ke_forms.field_to_dict(form.letter2) == {
            'data': None,
            'errors': ['This field is required.'],
            'label': 'Letter2',
            'required': True
        }

    def test_field_to_dict_fieldlist(self):
        form = NumbersForm()
        form.validate()
        expected = [
            {
                'data': None,
                'errors': [],
                'label': 'Number',
                'required': False,
            },
            {
                'data': None,
                'errors': [],
                'label': 'Number',
                'required': False,
            }
        ]
        assert ke_forms.field_to_dict(form.numbers2) == expected

    def test_field_to_dict_form_fieldlist(self):
        data = {
            'numbers-0-number': '123',
            'numbers-1-color': 'blue',
        }
        form = NumbersForm(MultiDict(data))
        form.validate()
        expected = [
            {
                'number': {
                    'data': '123',
                    'errors': [],
                    'label': 'Number',
                    'required': True
                },
                'color': {
                    'data': '',
                    'errors': [],
                    'label': 'Color',
                    'required': False
                }
            },
            {
                'number': {
                    'data': '',
                    'errors': ['This field is required.'],
                    'label': 'Number',
                    'required': True
                },
                'color': {
                    'data': 'blue',
                    'errors': [],
                    'label': 'Color',
                    'required': False
                }
            },
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
            'numbers': [
                {
                    'number': {
                        'data': '123',
                        'errors': [],
                        'label': 'Number',
                        'required': True,
                    },
                    'color': {
                        'data': '',
                        'errors': [],
                        'label': 'Color',
                        'required': False,
                    }
                },
                {
                    'number': {
                        'data': '',
                        'errors': ['This field is required.'],
                        'label': 'Number',
                        'required': True,
                    },
                    'color': {
                        'data': 'blue',
                        'errors': [],
                        'label': 'Color',
                        'required': False,
                    }
                },
            ],
            'numbers2': [
                {
                    'data': '',
                    'errors': [],
                    'label': 'Number',
                    'required': False,
                },
                {
                    'data': '',
                    'errors': [],
                    'label': 'Number',
                    'required': False
                }
            ]
        }
        fields_dict = form.fields_todict()
        assert fields_dict == expected, fields_dict


class TestFieldOrder():
    def test_field_missing_in_order(self):
        class MissingFields(Form):
            _field_order = ('num3', 'num2', 'num4')
            num1 = wtf.IntegerField()
            num2 = wtf.IntegerField()
            num3 = wtf.IntegerField()

        form = MissingFields()

        with pytest.raises(ValueError) as e:
            list(form)

        assert 'num1' in str(e.value)
        assert 'num4' in str(e.value)

    def test_with_csrf(self):
        # This whole hullabaloo is to get CSRF enabled for the form since we normally turn it off
        # for testing.
        class CSRFImpl(wtf.csrf.core.CSRF):
            def generate_csrf_token(self, token):
                return 'token'

        class CSRF(Form):
            _field_order = ('num2', 'num1',)

            class Meta:
                csrf = True
                csrf_class = CSRFImpl
                csrf_secret = '123'

            num1 = wtf.IntegerField()
            num2 = wtf.IntegerField()

        form = CSRF()
        assert [x.name for x in form] == ['csrf_token', 'num2', 'num1']

    def test_field_order(self):
        class OrderedForm(Form):
            _field_order = ('num3', 'num1', 'num2',)
            num1 = wtf.IntegerField()
            num2 = wtf.IntegerField()
            num3 = wtf.IntegerField()

        form = OrderedForm()

        assert [x.name for x in form] == ['num3', 'num1', 'num2']

    def test_field_unorder(self):
        class UnorderedForm(Form):
            num1 = wtf.IntegerField()
            num2 = wtf.IntegerField()
            num3 = wtf.IntegerField()

        form = UnorderedForm()

        assert [x.name for x in form] == ['num1', 'num2', 'num3']


class TestFormLevelValidation(FormBase):
    class MyForm(Form):
        num1 = wtf.IntegerField()
        num2 = wtf.IntegerField()
        num3 = wtf.IntegerField()

        @ke_forms.form_validator
        def equal_42(self):
            if self.num1.data + self.num2.data != 42:
                raise wtf.ValidationError('Does not add up')

        @ke_forms.form_validator
        def in_order(self):
            if not (self.num1.data <= self.num2.data <= self.num3.data):
                raise wtf.ValidationError('Out of order')

    form_cls = MyForm

    def test_form_valid(self):
        form = self.assert_valid(num1=5, num2=37, num3=100)
        assert form.form_errors == []
        assert form.field_errors == {}
        assert form.errors == {}

    def test_form_invalid(self):
        form = self.assert_invalid(num1=40, num2=3, num3=50)
        assert form.form_errors == ['Does not add up', 'Out of order']
        assert form.field_errors == {}
        assert form.errors == {'_form': ['Does not add up', 'Out of order']}

    def test_stop_validation_with_error(self):
        class StopValidationForm(Form):
            s1 = wtf.StringField()
            s2 = wtf.StringField()

            @ke_forms.form_validator
            def fields_equal(self):
                if self.s1.data != self.s2.data:
                    raise wtf.validators.StopValidation('not equal')

            @ke_forms.form_validator
            def other_validator(self):
                assert False, 'Validation should have stopped'  # pragma: no cover

        form = self.assert_invalid(form_cls=StopValidationForm, s1='v1', s2='v2')
        assert form.form_errors == ['not equal']
        assert form.field_errors == {}
        assert form.errors == {'_form': ['not equal']}

    def test_stop_validation_no_error(self):
        class StopValidationForm(Form):
            s1 = wtf.StringField()
            s2 = wtf.StringField()

            @ke_forms.form_validator
            def fields_equal(self):
                if self.s1.data != self.s2.data:
                    raise wtf.validators.StopValidation

            @ke_forms.form_validator
            def other_validator(self):
                assert False, 'Validation should have stopped'  # pragma: no cover

        form = self.assert_valid(form_cls=StopValidationForm, s1='v1', s2='v2')
        assert form.form_errors == []
        assert form.field_errors == {}
        assert form.errors == {}

    def test_invalid_with_field_errors(self):
        class InvalidFieldsForm(Form):
            s1 = wtf.StringField(validators=[wtf.validators.Length(max=3)])
            s2 = wtf.StringField()

            @ke_forms.form_validator
            def fields_equal(self):
                if self.s1.data != self.s2.data:
                    raise wtf.ValidationError('not equal')

        form = self.assert_invalid(form_cls=InvalidFieldsForm, s1='1234', s2='4321')
        assert form.form_errors == ['not equal']
        assert form.field_errors == {'s1': ['Field cannot be longer than 3 characters.']}
        assert form.errors == {
            '_form': ['not equal'],
            's1': ['Field cannot be longer than 3 characters.']
        }

    def test_do_not_validate_with_field_errors(self):
        class InvalidFieldsForm(Form):
            s1 = wtf.StringField(validators=[wtf.validators.Length(max=3)])
            s2 = wtf.StringField()

            @ke_forms.form_validator(only_when_fields_valid=True)
            def my_validator(self):
                assert False, 'Validation should not run'  # pragma: no cover

        form = self.assert_invalid(form_cls=InvalidFieldsForm, s1='1234', s2='4321')
        assert form.form_errors == []
        assert form.field_errors == {'s1': ['Field cannot be longer than 3 characters.']}
        assert form.errors == {'s1': ['Field cannot be longer than 3 characters.']}

    def test_validators_inherited(self):
        class SubclassForm(self.MyForm):
            @ke_forms.form_validator
            def num3_is_even(self):
                if self.num3.data % 2:
                    raise wtf.ValidationError('Num3 is odd')

            @ke_forms.form_validator
            def equal_42(self):
                if self.num1.data * self.num2.data != 42:
                    raise wtf.ValidationError('Does not compute')

        form = self.assert_invalid(num1=7, num2=5, num3=51, form_cls=SubclassForm)
        assert form.form_errors == ['Out of order', 'Num3 is odd', 'Does not compute']
        assert form.field_errors == {}
        assert form.errors == {
            '_form': ['Out of order', 'Num3 is odd', 'Does not compute']
        }

        form = self.assert_valid(num1=6, num2=7, num3=50, form_cls=SubclassForm)
        assert form.form_errors == []
        assert form.field_errors == {}
        assert form.errors == {}


class TestExcludesDatetimes(FormBase):
    entity_cls = ents.Thing

    def test_exclude_default_cols(self):
        form = self.compose_meta()
        assert 'updated_utc' not in form.fields_todict()
        assert 'created_utc' not in form.fields_todict()


class TestTypeHintingTextInputB4:
    class DemoForm(wtf.Form):
        prefix_field = wtf.StringField(widget=ke_forms.TypeHintingTextInputB4(prefix="foo"))
        suffix_field = wtf.StringField(widget=ke_forms.TypeHintingTextInputB4(suffix="bar"))
        both_field = wtf.StringField(widget=ke_forms.TypeHintingTextInputB4(prefix="a", suffix="z"))

    def test_prefix(self):
        form = self.DemoForm()
        rendered = pq(form.prefix_field())

        group = rendered(".input-group")
        assert len(group) == 1

        children = group.children()
        assert len(children) == 2

        prefix, field = children.items()
        assert prefix.has_class("input-group-prepend")
        assert len(prefix.children(".input-group-text"))
        assert prefix.children(".input-group-text").text() == "foo"

        assert field.is_("input")

    def test_suffix(self):
        form = self.DemoForm()
        rendered = pq(form.suffix_field())

        group = rendered(".input-group")
        assert len(group) == 1

        children = group.children()
        assert len(children) == 2

        field, suffix = children.items()
        assert suffix.has_class("input-group-append")
        assert len(suffix.children(".input-group-text"))
        assert suffix.children(".input-group-text").text() == "bar"

        assert field.is_("input")

    def test_both(self):
        form = self.DemoForm()
        rendered = pq(form.both_field())

        group = rendered(".input-group")
        assert len(group) == 1

        children = group.children()
        assert len(children) == 3

        prefix, field, suffix = children.items()

        assert prefix.has_class("input-group-prepend")
        assert len(prefix.children(".input-group-text"))
        assert prefix.children(".input-group-text").text() == "a"

        assert suffix.has_class("input-group-append")
        assert len(suffix.children(".input-group-text"))
        assert suffix.children(".input-group-text").text() == "z"

        assert field.is_("input")

    def test_text_escaped(self):
        class Form(wtf.Form):
            prefix = wtf.StringField(widget=ke_forms.TypeHintingTextInputB4(prefix="<script>"))
            suffix = wtf.StringField(widget=ke_forms.TypeHintingTextInputB4(suffix="&foo&"))

        form = Form()

        prefix = form.prefix()
        assert "&lt;script&gt;" in prefix

        suffix = form.suffix()
        assert "&amp;foo&amp;" in suffix


class TestTypeHintingTextInputB3:
    class DemoForm(wtf.Form):
        prefix_field = wtf.StringField(widget=ke_forms.TypeHintingTextInputB3(prefix="foo"))
        suffix_field = wtf.StringField(widget=ke_forms.TypeHintingTextInputB3(suffix="bar"))
        both_field = wtf.StringField(widget=ke_forms.TypeHintingTextInputB3(prefix="a", suffix="z"))

    def test_prefix(self):
        form = self.DemoForm()
        rendered = pq(form.prefix_field())

        group = rendered(".input-group")
        assert len(group) == 1

        children = group.children()
        assert len(children) == 2

        prefix, field = children.items()
        assert prefix.has_class("input-group-addon")
        assert prefix.text() == "foo"

        assert field.is_("input")

    def test_suffix(self):
        form = self.DemoForm()
        rendered = pq(form.suffix_field())

        group = rendered(".input-group")
        assert len(group) == 1

        children = group.children()
        assert len(children) == 2

        field, suffix = children.items()
        assert suffix.has_class("input-group-addon")
        assert suffix.text() == "bar"

        assert field.is_("input")

    def test_both(self):
        form = self.DemoForm()
        rendered = pq(form.both_field())

        group = rendered(".input-group")
        assert len(group) == 1

        children = group.children()
        assert len(children) == 3

        prefix, field, suffix = children.items()

        assert prefix.has_class("input-group-addon")
        assert prefix.text() == "a"

        assert suffix.has_class("input-group-addon")
        assert suffix.text() == "z"

        assert field.is_("input")

    def test_text_escaped(self):
        class Form(wtf.Form):
            prefix = wtf.StringField(widget=ke_forms.TypeHintingTextInputB3(prefix="<script>"))
            suffix = wtf.StringField(widget=ke_forms.TypeHintingTextInputB3(suffix="&foo&"))

        form = Form()

        prefix = form.prefix()
        assert "&lt;script&gt;" in prefix

        suffix = form.suffix()
        assert "&amp;foo&amp;" in suffix


class TestModelForm:
    class MyForm(ModelForm):
        class Meta:
            model = ents.LookupTester

        class FieldsMeta:
            pass

    def test_default_title_case(self):
        form = TestModelForm.MyForm(None)
        assert form.label.label.text == 'Label'


def test_fields_meta_inheritance():
    class FormA(ModelForm):
        class FieldsMeta:
            a = 'foo'

    class FormB(FormA):
        class FieldsMeta:
            b = 'bar'

    form = FormB()
    assert form.FieldsMeta.a == 'foo'
    assert form.FieldsMeta.b == 'bar'


class RelationshipMixin:
    def assert_object_options(self, field, option_objects, has_blank=True):
        object_options = [(str(obj.id), obj.name) for obj in option_objects]
        expected_choices = [
            ('', ''),
            *object_options
        ] if has_blank else object_options
        index = 0
        for value, label, selected in field.iter_choices():
            assert expected_choices[index] == (value, label)
            index += 1


class ThingForeignKeyRelationshipMixin:
    def setup(self):
        ents.Thing.delete_cascaded()

    def get_field(self, form):
        raise NotImplementedError()  # pragma: no cover

    def create_formdata(self, form):
        raise NotImplementedError()  # pragma: no cover

    def coerce(self, value):
        return value

    def test_relationship_options(self):
        ents.Thing.testing_create(name='Foo')
        thing1 = ents.Thing.testing_create()
        form = self.create_form(
            self.create_relationship(lambda this: this.orm_cls.name != 'Foo')
        )

        self.assert_object_options(self.get_field(form), [thing1])

    def test_options_include_form_obj_value(self):
        foo_thing = ents.Thing.testing_create(name='Foo')
        thing1 = ents.Thing.testing_create(name='Thing 1')
        related_thing = ents.RelatedThing(thing=foo_thing, name='Related')
        db.session.commit()
        form = self.create_form(
            self.create_relationship(lambda this: this.orm_cls.name != 'Foo'),
            obj=related_thing,
        )

        self.assert_object_options(self.get_field(form), [foo_thing, thing1])
        assert self.get_field(form).data == self.coerce(foo_thing.id)

    def test_options_sorted(self):
        thing_b = ents.Thing.testing_create(name='BBB')
        thing_c = ents.Thing.testing_create(name='CCC')
        thing_a = ents.Thing.testing_create(name='AAA')
        form = self.create_form(
            self.create_relationship(lambda this: this.orm_cls.name != 'Foo')
        )

        self.assert_object_options(self.get_field(form), [thing_a, thing_b, thing_c])

    def test_no_query_filter(self):
        foo_thing = ents.Thing.testing_create(name='Foo')
        thing1 = ents.Thing.testing_create(name='Thing 1')
        form = self.create_form(self.create_relationship())

        self.assert_object_options(self.get_field(form), [foo_thing, thing1])


class TestForeignKeyRelationship(ThingForeignKeyRelationshipMixin, RelationshipMixin):
    """Test a foreign key field."""
    def create_relationship(self, query_filter=None):
        return RelationshipField('Thing', ents.Thing, 'name', query_filter=query_filter)

    def create_form(self, relationship, **kwargs):
        class RelatedThingForm(ModelForm):
            thing_id = relationship

            class Meta:
                model = ents.RelatedThing

        return RelatedThingForm(**kwargs)

    def get_field(self, form):
        return form.thing_id

    def test_coerce_formdata(self):
        thing = ents.Thing.testing_create()
        form = self.create_form(self.create_relationship(),
                                formdata=MultiDict({'thing_id': str(thing.id)}))
        assert form.thing_id.data == thing.id


class TestOrmRelationship(ThingForeignKeyRelationshipMixin, RelationshipMixin):
    """Test a relationship field that corresponds to a SA RelationshipProperty."""

    def create_relationship(self, query_filter=None):
        return RelationshipField('Thing', ents.Thing, 'name', query_filter=query_filter,
                                 fk_attr=None)

    def create_form(self, relationship, **kwargs):
        class RelatedThingForm(ModelForm):
            thing = relationship

            class Meta:
                model = ents.RelatedThing

        return RelatedThingForm(**kwargs)

    def coerce(self, value):
        return ents.Thing.query.get(value)

    def get_field(self, form):
        return form.thing

    def test_coerce_formdata(self):
        thing = ents.Thing.testing_create()
        form = self.create_form(self.create_relationship(),
                                formdata=MultiDict({'thing': str(thing.id)}))
        assert form.thing.data == thing


class TestRelationshipFieldGenerator:
    def setup(self):
        ents.Thing.delete_cascaded()

    def create_form(self, **kwargs):
        class RelatedThingForm(ModelForm):
            class Meta:
                model = ents.RelatedThing
                include_foreign_keys = True

        return RelatedThingForm(**kwargs)

    def create_custom_form(self, field_kwargs, **kwargs):
        class RelatedThingForm(ModelForm):
            class Meta:
                model = ents.RelatedThing

            thing_id = RelationshipField('Thing', ents.Thing, **field_kwargs)

        return RelatedThingForm(**kwargs)

    def test_field_created(self):
        form = self.create_form()
        assert form.thing_id
        assert form.thing_id.label.text == 'Thing'

    def test_choices(self):
        thing1 = ents.Thing.testing_create(name='foo')
        thing2 = ents.Thing.testing_create(name='bar')
        form = self.create_form()
        assert form.thing_id.choice_values == ['', thing2.id, thing1.id]

    def test_validators_applied(self):
        form = self.create_form()
        assert isinstance(form.thing_id.validators[0], validators.InputRequired)

    def test_custom_label_attr(self):
        thing1 = ents.Thing.testing_create(name='foo', color='blue')
        thing2 = ents.Thing.testing_create(name='bar', color='red')
        form = self.create_custom_form({'label_attr': 'color'})
        assert form.thing_id.choice_values == ['', thing1.id, thing2.id]

    def test_choices_filtered(self):
        ents.Thing.testing_create(name='foo', color='blue')
        thing2 = ents.Thing.testing_create(name='bar', color='red')
        form = self.create_custom_form({'query_filter': ents.Thing.name != 'foo'})
        assert form.thing_id.choice_values == ['', thing2.id]

    def test_choices_included(self):
        thing1 = ents.Thing.testing_create(name='foo', color='blue')
        thing2 = ents.Thing.testing_create(name='bar', color='red')
        related_thing = ents.RelatedThing.testing_create(thing=thing1)
        form = self.create_custom_form({'query_filter': ents.Thing.name != 'foo'},
                                       obj=related_thing)
        assert form.thing_id.choice_values == ['', thing2.id, thing1.id]


class TestCollectionRelationship(RelationshipMixin):
    """Test field that corresponds to a SA collection."""
    def create_relationship(self, query_filter=None):
        return RelationshipMultipleField('Related Things', ents.RelatedThing, 'name',
                                         query_filter=query_filter)

    def assert_object_options(self, field, option_objects):
        return super().assert_object_options(field, option_objects, has_blank=False)

    def create_form(self, relationship, **kwargs):
        class ThingForm(ModelForm):
            related_things = relationship

            class Meta:
                model = ents.Thing

        return ThingForm(**kwargs)

    def setup(self):
        ents.Thing.delete_cascaded()

    def test_relationship_options(self):
        ents.RelatedThing.testing_create(name='Foo')
        thing1 = ents.RelatedThing.testing_create()
        form = self.create_form(
            self.create_relationship(lambda this: this.orm_cls.name != 'Foo')
        )

        self.assert_object_options(form.related_things, [thing1])

    def test_options_include_form_obj_value(self):
        foo_thing = ents.RelatedThing.testing_create(name='Foo')
        thing1 = ents.RelatedThing.testing_create(name='Thing 1')
        thing2 = ents.RelatedThing.testing_create(name='Thing 2')
        thing_obj = ents.Thing.testing_create(related_things=[thing1, thing2])
        form = self.create_form(
            self.create_relationship(lambda this: ~this.orm_cls.id.in_([thing1.id, thing2.id])),
        )
        self.assert_object_options(form.related_things, [foo_thing])

        form = self.create_form(
            self.create_relationship(lambda this: ~this.orm_cls.id.in_([thing1.id, thing2.id])),
            obj=thing_obj,
        )
        self.assert_object_options(form.related_things, [foo_thing, thing1, thing2])

    def test_load_save_data(self):
        class ManyThingsForm(ModelForm):
            things = RelationshipMultipleField('Things', ents.Thing)

            class Meta:
                model = ents.ManyToManyThing

        thing1 = ents.Thing.testing_create()
        thing2 = ents.Thing.testing_create()
        thing3 = ents.Thing.testing_create()
        manything = ents.ManyToManyThing.testing_create(things=[thing1, thing2])

        form = ManyThingsForm(obj=manything)
        # form data level should be ORM instances
        assert form.things.data == [thing1, thing2]

        form = ManyThingsForm(
            obj=manything,
            formdata=MultiDict([
                ('things', str(thing2.id)),
                ('things', str(thing3.id)),
            ])
        )
        assert form.things.data == [thing2, thing3]
        form.populate_obj(manything)
        assert manything.things == [thing2, thing3]
