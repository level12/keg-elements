from __future__ import absolute_import
from __future__ import unicode_literals

import functools
import inspect
import logging

import flask
from flask_wtf import Form as BaseForm
from keg.db import db
import sqlalchemy as sa
import six
import wtforms.fields
import wtforms.form
from wtforms.validators import InputRequired, Optional
from wtforms_alchemy import model_form_factory, FormGenerator as FormGeneratorBase
from wtforms_components.fields import SelectField as SelectFieldBase

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
                 extra_validators=[]):
        self.label_text = label_text
        self.label_modifier = label_modifier
        self.description = description
        self.choices_modifier = choices_modifier
        self.choices = choices
        self.required = required
        self.widget = widget
        self.extra_validators = extra_validators

        assert self.required in (_not_given, False, True)

    def apply_to_field(self, field):
        # field is a wtforms.fields.core.UnboundField instance
        self.apply_to_label(field)
        self.apply_to_description(field)
        self.apply_to_choices(field)
        self.apply_required(field)
        self.apply_widget(field)
        self.apply_extra_validators(field)

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
        if 'invalid literal for int()' not in str(e):
            raise
        return six.text_type(value)


class SelectField(SelectFieldBase):
    """
        Provides helpful features above wtforms_components SelectField which it is based on:

        1) Adds a blank choice by default at the front of the choices.  This results in your user
           being forced to select something if the field is required, which avoids unintial
           deaulting of the first value in the field getting submitted.
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


class RequiredBoolRadioField(wtforms.fields.RadioField):
    def __init__(self, *args, **kwargs):
        true_label = kwargs.pop('true_label', 'Yes')
        false_label = kwargs.pop('false_label', 'No')

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


class FormGenerator(FormGeneratorBase):
    def __init__(self, form_class):
        super(FormGenerator, self).__init__(form_class)
        self.fields_meta = getattr(self.form_class, 'FieldsMeta', None)

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
        if isinstance(column.type, sa.Numeric):
            validators.append(NumberScale(column.type.scale))
        return validators


def field_to_dict(field):
    if isinstance(field, wtforms.fields.FormField):
        return form_fields_to_dict(field)
    if isinstance(field, wtforms.fields.FieldList):
        return [field_to_dict(subfield) for subfield in field]
    return dict(data=field.data, errors=field.errors)


def form_fields_to_dict(form):
    return dict((name, field_to_dict(field)) for name, field in six.iteritems(form._fields))


class Form(BaseForm):
    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        self.after_init(args, kwargs)

    def after_init(self, args, kwargs):
        pass

    def fields_todict(self):
        """Turns a form into dicts and lists with both data and errors for each field."""
        return form_fields_to_dict(self)


BaseModelForm = model_form_factory(Form, form_generator=FormGenerator)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session
