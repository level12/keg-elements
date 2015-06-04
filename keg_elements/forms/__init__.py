from __future__ import absolute_import
from __future__ import unicode_literals

import inspect
import logging

import flask
from flask_wtf import Form
from keg.db import db
from wtforms_alchemy import model_form_factory, FormGenerator as FormGeneratorBase

form_element = flask.Blueprint('form_element', __name__)
log = logging.getLogger(__name__)


def to_title_case(x):
    """ underscore or dash to title case notation """
    return x.replace('_', ' ').replace('-', ' ').title()


#sentinel
_not_given = ()


class FieldMeta(object):

    def __init__(self, label_text=_not_given, description=_not_given, label_modifier=_not_given,
                 choices_modifier=_not_given, choices=None):
        self.label_text = label_text
        self.label_modifier = label_modifier
        self.description = description
        self.choices_modifier = choices_modifier
        self.choices = choices

    def apply_to_field(self, field):
        # field is a wtforms.fields.core.UnboundField instance
        self.apply_to_label(field)
        self.apply_to_description(field)
        self.apply_to_choices(field)

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


class FormGenerator(FormGeneratorBase):
    def __init__(self, form_class):
        super(FormGenerator, self).__init__(form_class)
        self.fields_meta = getattr(self.form_class, 'FieldsMeta', None)

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

BaseModelForm = model_form_factory(Form, form_generator=FormGenerator)


class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session




