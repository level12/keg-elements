from __future__ import absolute_import
from __future__ import unicode_literals

import functools
import inspect
import logging
from collections import namedtuple
from operator import attrgetter

import flask
from decimal import Decimal
from flask_wtf import FlaskForm as BaseForm
from keg.db import db
import sqlalchemy as sa
from sqlalchemy_utils import ArrowType
import six
import wtforms.fields
import wtforms.form
from wtforms.validators import InputRequired, Optional, StopValidation, NumberRange
from wtforms_alchemy import model_form_factory, FormGenerator as FormGeneratorBase
from wtforms_components.fields import SelectField as SelectFieldBase

from keg_elements.extensions import lazy_gettext as _
from keg_elements.forms.validators import NumberScale

form_element = flask.Blueprint('form_element', __name__)
log = logging.getLogger(__name__)


def to_title_case(x):
    """ underscore or dash to title case notation """
    return x.replace('_', ' ').replace('-', ' ').title()


# sentinel
_not_given = ()


class FieldMeta(object):

    def __init__(self, label_text=_not_given, description=_not_given, label_modifier=_not_given,
                 choices_modifier=_not_given, choices=None, required=_not_given, widget=_not_given,
                 extra_validators=tuple(), coerce=_not_given, default=_not_given):
        self.label_text = label_text
        self.label_modifier = label_modifier
        self.description = description
        self.choices_modifier = choices_modifier
        self.choices = choices
        self.required = required
        self.widget = widget
        self.extra_validators = extra_validators
        self.coerce = coerce
        self.default = default

        assert self.required in (_not_given, False, True)

    def apply_to_field(self, field):
        # field is a wtforms.fields.core.UnboundField instance
        self.apply_to_label(field)
        self.apply_to_description(field)
        self.apply_to_choices(field)
        self.apply_required(field)
        self.apply_widget(field)
        self.apply_extra_validators(field)
        self.apply_coerce(field)
        self.apply_default(field)

    def apply_to_label(self, field):
        default_label = field.kwargs['label']
        if self.label_text is not _not_given:
            label_text = self.label_text
        elif self.label_modifier is None:
            label_text = default_label
        elif self.label_modifier is _not_given:
            label_text = to_title_case(default_label)
        else:
            label_text = self.label_modifier(default_label)
        field.kwargs['label'] = self.modify_label(label_text)

    def modify_label(self, label_text):
        """ for subclasses to easily modify the final label text value """
        return label_text

    def apply_to_description(self, field):
        default_description = field.kwargs['description']
        if self.description is _not_given:
            description = default_description
        else:
            description = self.description
        field.kwargs['description'] = self.modify_description(description)

    def modify_description(self, description):
        """ for subclasses to easily modify the final label text value """
        return description

    def apply_to_choices(self, field):
        default_choices = field.kwargs.get('choices', None)
        if default_choices is None:
            # this isn't a field that has choices
            return

        if self.choices_modifier is None:
            modifier = None
        elif self.choices_modifier is not _not_given:
            modifier = self.choices_modifier
        elif self.label_modifier is None:
            # no choices modifier and the label modifier is explicit, so no label modifier
            modifier = None
        elif self.label_modifier is _not_given:
            # title case to labels by default
            modifier = to_title_case
        else:
            # a label modifier was given, use that since no choices modifier was given to override
            modifier = self.label_modifier

        if self.choices is not None:
            choices = self.choices
        elif modifier is None:
            choices = default_choices
        else:
            map_func = lambda pair: (pair[0], modifier(pair[1]))
            choices = map(map_func, default_choices)

        field.kwargs['choices'] = self.modify_choices(choices)

    def modify_choices(self, choices):
        return choices

    def apply_coerce(self, field):
        if self.coerce is _not_given:
            return
        if not issubclass(field.field_class, wtforms.SelectField):
            raise ValueError('`coerce` argument may only be used for select fields')
        field.kwargs['coerce'] = self.coerce

    def apply_default(self, field):
        if self.default is _not_given:
            return
        field.kwargs['default'] = self.default

    def apply_required(self, field):
        validators = field.kwargs.get('validators', [])

        if self.required == _not_given:
            # required value not given on FieldMeta, don't make any changes
            pass
        elif self.required:
            # If a required validator isn't present, we need to add one.
            req_val_test = lambda val: hasattr(val, 'field_flags') and 'required' in val.field_flags
            if not list(filter(req_val_test, validators)):
                validators.append(InputRequired())

            # If an optional validator is present, we need to remove it.
            not_opt_val_test = lambda val: not hasattr(val, 'field_flags') or \
                'optional' not in val.field_flags
            not_opt_validators = list(filter(not_opt_val_test, validators))
            field.kwargs['validators'] = not_opt_validators
        else:
            # If an optional validator isn't present, we need to add one.
            opt_val_test = lambda val: hasattr(val, 'field_flags') and 'optional' in val.field_flags
            if not list(filter(opt_val_test, validators)):
                validators.append(Optional())

            # If a required validator is present, we need to remove it.
            non_req_val_test = lambda val: not hasattr(val, 'field_flags') or \
                'required' not in val.field_flags
            not_req_validators = list(filter(non_req_val_test, validators))
            field.kwargs['validators'] = not_req_validators

    def apply_widget(self, field):
        if self.widget != _not_given:
            field.kwargs['widget'] = self.widget

    def apply_extra_validators(self, field):
        field.kwargs.setdefault('validators', [])
        field.kwargs['validators'] += self.extra_validators


def select_coerce(es_pass_thru, coerce, value):
    if es_pass_thru and value == '':
        return value
    if coerce is not _not_given:
        return coerce(value)

    # try coercing to int first.  If not valid, fall back to default behavior
    try:
        return int(value)
    except ValueError as e:
        if 'invalid literal for int()' not in six.text_type(e):
            raise
        return six.text_type(value)


class SelectField(SelectFieldBase):
    """
        Provides helpful features above wtforms_components SelectField which it is based on:

        1) Adds a blank choice by default at the front of the choices.  This results in your user
           being forced to select something if the field is required, which avoids initial
           defaulting of the first value in the field getting submitted.
        2) The coerce function used for the choices will automatically convert to int if possible,
           falling back to unicode if the value is not an integer.
    """
    def __init__(self, *args, **kwargs):
        self.add_blank_choice = kwargs.pop('add_blank_choice', True)
        coerce_arg = kwargs.pop('coerce', _not_given)
        super(SelectField, self).__init__(*args, **kwargs)

        if self.add_blank_choice:
            # If we are adding a blank choice, and it is selected, we want the value that comes back
            # in .data to be None -> as if no value was selected.
            #
            # self.filters is a tuple, so have to do some extra work.
            self.filters = [lambda x: None if x == '' else x] + list(self.filters)

        self.coerce = functools.partial(select_coerce, self.add_blank_choice, coerce_arg)

    def iter_choices(self):
        if self.add_blank_choice:
            yield ('', '', (self.coerce, False))
        for value in super(SelectField, self).iter_choices():
            yield value

    @property
    def choice_values(self):
        values = super(SelectField, self).choice_values
        if self.add_blank_choice:
            return [''] + values
        return values

    @property
    def selected_choice_label(self):
        value_dict = dict(self.concrete_choices)
        return value_dict.get(self.data)


class MultiCheckboxField(wtforms.fields.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.
    """


class RequiredBoolRadioField(wtforms.fields.RadioField):
    def __init__(self, *args, **kwargs):
        true_label = kwargs.pop('true_label', _('Yes'))
        false_label = kwargs.pop('false_label', _('No'))

        def bool_coerce(val):
            if val == u'True':
                return True
            if val == u'False':
                return False
            return val

        kwargs['choices'] = [(True, true_label), (False, false_label)]
        kwargs['coerce'] = bool_coerce
        kwargs['validators'] = [InputRequired()] + kwargs.get('validators', [])

        super(RequiredBoolRadioField, self).__init__(*args, **kwargs)
        self.type = 'RadioField'


class _TypeHintingTextInputBase(wtforms.widgets.TextInput):
    def __init__(self, prefix=None, suffix=None):
        self.prefix = prefix
        self.suffix = suffix
        super().__init__()


class TypeHintingTextInputB3(_TypeHintingTextInputBase):
    """
    A text input widget with a prefix and/or suffix to hint at the expected type or units.
    For use with bootstrap 3
    """
    def __call__(self, field, **kwargs):
        def make_addon(txt):
            return wtforms.widgets.HTMLString(
                '<span class="input-group-addon">{}</span>'.format(wtforms.widgets.core.escape(txt))
            )

        return wtforms.widgets.HTMLString(
            '<div class="input-group">{pre}{field}{post}</div>'.format(
                pre=make_addon(self.prefix) if self.prefix else '',
                field=super().__call__(field, **kwargs).__html__(),
                post=make_addon(self.suffix) if self.suffix else ''
            )
        )


class TypeHintingTextInputB4(_TypeHintingTextInputBase):
    """
    A text input widget with a prefix and/or suffix to hint at the expected type or units.
    For use with bootstrap 4
    """
    def __call__(self, field, **kwargs):
        def make_addon(txt, addon_type):
            return wtforms.widgets.HTMLString(
                '<div class="input-group-{type}">'
                '   <span class="input-group-text">{txt}</span>'
                "</div>".format(type=addon_type, txt=wtforms.widgets.core.escape(txt))
            )

        return wtforms.widgets.HTMLString(
            '<div class="input-group">{pre}{field}{post}</div>'.format(
                pre=make_addon(self.prefix, "prepend") if self.prefix else "",
                field=super().__call__(field, **kwargs).__html__(),
                post=make_addon(self.suffix, "append") if self.suffix else "",
            )
        )


def _max_for_numeric(digits, scale):
    return Decimal('{}.{}'.format('9' * (digits - scale), '9' * scale))


class FormGenerator(FormGeneratorBase):
    def __init__(self, form_class):
        super(FormGenerator, self).__init__(form_class)
        self.fields_meta = getattr(self.form_class, 'FieldsMeta', None)

    def skip_column(self, column):
        # Verify the key is not also in exclude=[] so we don't break compatibility with forms
        # that already manually excluded these fields
        if (not self.meta.include_datetimes_with_default
                and isinstance(column.type, ArrowType)
                and column.default
                and column.key not in self.meta.exclude):
            return True

        return super().skip_column(column)

    def get_field_class(self, column):
        field_cls = super(FormGenerator, self).get_field_class(column)
        if field_cls is SelectFieldBase:
            return SelectField

        is_required_boolean = (field_cls is wtforms.fields.BooleanField
                               and not column.nullable
                               and not column.default)

        if is_required_boolean:
            return RequiredBoolRadioField

        return field_cls

    def get_field_modifier(self, prop):

        # is there an entry in FieldMeta?
        if hasattr(self.fields_meta, prop.key):
            field_modifier = getattr(self.fields_meta, prop.key)
        else:
            field_modifier = getattr(self.fields_meta, '__default__', _not_given)
            if field_modifier is _not_given:
                return None

        return field_modifier() if inspect.isclass(field_modifier) else field_modifier

    def create_field(self, prop, column):
        field = super(FormGenerator, self).create_field(prop, column)
        modifier = self.get_field_modifier(prop)
        if modifier is not None:
            modifier.apply_to_field(field)
        return field

    def create_validators(self, prop, column):
        validators = super(FormGenerator, self).create_validators(prop, column)
        if isinstance(column.type, sa.Numeric) and not isinstance(column.type, sa.Float):
            max_ = _max_for_numeric(column.type.precision, column.type.scale)
            validators.append(NumberRange(min=-max_, max=max_))
            validators.append(NumberScale(column.type.scale))
        return validators

    def length_validator(self, column):
        if isinstance(column.type, sa.types.Enum):
            return None
        return super(FormGenerator, self).length_validator(column)


def field_to_dict(field):
    if isinstance(field, wtforms.fields.FormField):
        return form_fields_to_dict(field)
    if isinstance(field, wtforms.fields.FieldList):
        return [field_to_dict(subfield) for subfield in field]
    return {
        'data': field.data,
        'errors': field.errors,
        'label': field.label.text,
        'required': field.flags.required,
    }


def form_fields_to_dict(form):
    return dict((six.text_type(name), field_to_dict(field))
                for name, field in six.iteritems(form._fields))


___validator_creation_counter = 0


def form_validator(func=None, only_when_fields_valid=False):
    """Decorator used to mark a method as a form level validator"""
    if func is None:
        return functools.partial(form_validator, only_when_fields_valid=only_when_fields_valid)

    @functools.wraps(func)
    def wrapper(form):
        if not only_when_fields_valid or not form.errors:
            return func(form)

    global ___validator_creation_counter
    wrapper.___form_validator = True
    ___validator_creation_counter += 1
    wrapper.___creation_counter = ___validator_creation_counter
    return wrapper


class Form(BaseForm):
    """Base form with a bunch of QoL improvements


    :param _field_order: Relying on the default field ordering can lead to unintuitive forms. It is
        possible to override this by adding the ``_field_order`` class attribute. Set this class
        variable to a tuple or list of field names (addressable via Form._fields['name_of_field'])
        and the form will render in that order. You must include all the fields, except CSRF.
        Forgetting a field or adding one which doesn't exist will cause the form to raise a
        ``ValueError`` and the form will not be rendered.

            class MyForm(Form):
                _field_order = ('field1', 'field2',)

                field1 = String('field1_label')  # Note that we don't use the label in the ordering
                field2 = String()
    """
    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        self._form_level_errors = []
        self.after_init(args, kwargs)

    def __iter__(self):
        order = getattr(self, '_field_order', None)

        if order is None:
            return super().__iter__()

        has_csrf = hasattr(self, 'csrf_token')
        order = (['csrf_token'] if has_csrf else []) + list(order)

        declared = set(self._fields.keys())
        ordered = set(order)

        if declared != ordered:
            not_ordered = declared - ordered
            extra_ordered = ordered - declared
            raise ValueError(
                'Custom field ordering for {} is incorrect.'.format(self.__class__.__name__),
                ' Missing fields: {} '.format(not_ordered),
                ' Extra fields: {} '.format(extra_ordered),
            )

        return (self._fields[f] for f in order)

    def after_init(self, args, kwargs):
        pass

    def fields_todict(self):
        """Turns a form into dicts and lists with both data and errors for each field."""
        return form_fields_to_dict(self)

    def validate(self):
        fields_valid = super(Form, self).validate()

        form_validators = {}
        # Traverse the MRO so we can get validators in parent classes.
        # Do so in reverse order so child classes can override parents' validators.
        # WTForms will not include the methods on form instances so we get them from the classes.
        for cls in reversed(self.__class__.__mro__):
            cls_validators = {
                name: attr for name, attr in six.iteritems(cls.__dict__)
                if getattr(attr, '___form_validator', False)
            }
            form_validators.update(cls_validators)

        self._form_level_errors = []
        for validator in sorted(form_validators.values(), key=attrgetter('___creation_counter')):
            try:
                validator(self)
            except StopValidation as e:
                if e.args and e.args[0]:
                    self._form_level_errors.append(e.args[0])
                break
            except ValueError as e:
                self._form_level_errors.append(e.args[0])

        return fields_valid and not self._form_level_errors

    @property
    def form_errors(self):
        return self._form_level_errors

    @property
    def errors(self):
        if self._errors is None:
            self._errors = {name: f.errors for name, f in six.iteritems(self._fields) if f.errors}
        return self._errors

    @property
    def all_errors(self):
        return namedtuple('Errors', ['field', 'form'])(self.errors, self.form_errors)


BaseModelForm = model_form_factory(Form, form_generator=FormGenerator)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(cls):
        return db.session
