import functools
import inspect
import logging
import warnings
from decimal import Decimal
from operator import attrgetter

from blazeutils.strings import case_cw2dash
import flask
from flask_wtf import FlaskForm as BaseForm
from keg.db import db
import sqlalchemy as sa
from markupsafe import Markup
from sqlalchemy_utils import ArrowType, get_class_by_table
import wtforms.fields
import wtforms.form
from wtforms.validators import InputRequired, Optional, StopValidation, NumberRange, AnyOf
from wtforms_alchemy import (
    FormGenerator as FormGeneratorBase,
    model_form_factory,
    model_form_meta_factory,
)
from wtforms_components.fields import (
    SelectField as SelectFieldBase,
    SelectMultipleField as SelectMultipleFieldBase,
)

from keg_elements.db.columns import DBEnum
from keg_elements.db.utils import has_column
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
    """Meta information for fields to override model-generated info.

    Rather than forcing all-or-nothing acceptance of model-generated meta info from wtforms,
    FieldMeta may be provided in the FieldsMeta nested class of the form to override specifics.

    All modifications are applied to the field instance during the form generation process.

    Example::

        class PersonForm(ModelForm):
            class Meta:
                model = Person

            class FieldsMeta:
                name = FieldMeta('Full Name')

    :param label_text: Force a label value.
    :param description: Force a description value.
    :param label_modifier: Callable to be called with the default label. label_text takes
        precedence if both are provided. But, this modifier will apply to choices as well if
        applicable and a choices_modifier is not given.
    :param choices_modifier: Callable to be called with the label value for choices.
    :param required: Force validators to be added/removed for requirement.
    :param widget: Force a specific widget to be used for the field in render.
    :param extra_validators: Add the given validators to those existing on the field.
    :param coerce: Applies a specific coerce for field values. Applicable to select fields only.
    :param default: Forces a default value on the field.
    """

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
        default_description = field.kwargs.get('description')
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
            choices = [(v, modifier(l)) for v, l in default_choices]

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
        if 'invalid literal for int()' not in str(e):
            raise
        return str(value)


class SelectMixin:
    def __init__(self, *args, **kwargs):
        self.add_blank_choice = kwargs.pop('add_blank_choice', True)
        coerce_arg = kwargs.pop('coerce', _not_given)
        super().__init__(*args, **kwargs)

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
        for value in super().iter_choices():
            yield value

    @property
    def choice_values(self):
        values = super().choice_values
        if self.add_blank_choice:
            return [''] + values
        return values

    @property
    def selected_choice_label(self):
        value_dict = dict(self.concrete_choices)
        return value_dict.get(self.data)


class SelectField(SelectMixin, SelectFieldBase):
    """
        Provides helpful features above wtforms_components SelectField which it is based on:

        1) Adds a blank choice by default at the front of the choices.  This results in your user
           being forced to select something if the field is required, which avoids initial
           defaulting of the first value in the field getting submitted.
        2) The coerce function used for the choices will automatically convert to int if possible,
           falling back to unicode if the value is not an integer.
    """


class SelectMultipleField(SelectMixin, SelectMultipleFieldBase):
    """
        Provides helpful features above wtforms_components SelectMultipleField which it is
        based on:

        The coerce function used for the choices will automatically convert to int if possible,
        falling back to unicode if the value is not an integer.
    """
    def __init__(self, *args, **kwargs):
        kwargs['add_blank_choice'] = kwargs.get('add_blank_choice', False)
        super().__init__(*args, **kwargs)


class MultiCheckboxField(wtforms.fields.SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.
    """


class RequiredBoolRadioField(wtforms.fields.RadioField):
    """A radio group field with true/false labels and a required validator.

    :param true_label: Optional, defaults to Yes.
    :param false_label: Optional, defaults to No.
    :param validators: Optional. Any provided validators will be added to InputRequired.
    """
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


class RelationshipFieldBase:
    """Common base for single/multiple select fields that reference ORM relationships.

    Handles one-to-many and many-to-many patterns.

    Note, must use the wtforms-components fields as a base, because we depend on
    lazy-loaded choices. At import time, a field's choices may not be fully available
    in the data. In addition, when pairing the form with an existing record, we need
    to ensure that the option from the record is present even if it would normally
    be filtered (e.g. an inactive option).
    """
    def __init__(self, label=None, orm_cls=None, label_attr=None, fk_attr='id',
                 query_filter=None, coerce=_not_given, **kwargs):
        label = self.field_label_modifier(label)
        self.orm_cls = orm_cls

        self.label_attr = label_attr
        if self.label_attr is None:
            self.label_attr = self.get_best_label_attr()
        if self.label_attr:
            # compute this once and store on the object, rather than for each option
            self.label_attr_name = self.compute_option_attr_name(self.label_attr)

        self.fk_attr = fk_attr
        if self.fk_attr:
            self.fk_attr_name = self.compute_option_attr_name(self.fk_attr)

        self.query_filter = query_filter
        if not self.fk_attr and not coerce:
            def coerce_to_orm_obj(value):
                """Coerce ID to relationship object."""
                # If coming form formdata, we'll get a string ID.
                if isinstance(value, str):
                    return self.orm_cls.query.get(value)

                # If coming from object data, we'll get an ORM instance.
                return value

            coerce = coerce_to_orm_obj

        super().__init__(label=label, choices=self.get_choices, coerce=coerce, **kwargs)

    def compute_option_attr_name(self, base_attr):
        """To access the label value on an option in the result set, we need to know what
        attribute to use. Based on ``label_attr``, which can be string, SA ORM attr,
        SA hybrid attr, etc., determine a sane attribute."""
        retval = base_attr

        if isinstance(base_attr, sa.orm.InstrumentedAttribute):
            retval = base_attr.name
        else:
            retval = getattr(base_attr, '__name__', str(base_attr))

        return retval

    def field_label_modifier(self, label):
        """Modifies the label to something more human-friendly.

        One-to-many relationships often have a field name like "foo_id", which title cases
        as "Foo Id". Form should only show "Foo", though, so we trim it that way here.
        """
        if label.lower().endswith(' id'):
            return label.rsplit(' ', 1)[0]
        return label

    def build_query(self):
        query = self.query_base()
        query = self.filter_query(query)
        return query

    def query_base(self):
        orm_label_attr = self.label_attr
        if isinstance(self.label_attr, str):
            orm_label_attr = getattr(self.orm_cls, self.label_attr)
        return self.orm_cls.query.order_by(orm_label_attr)

    def get_data_filter(self):
        if self.fk_attr:
            return getattr(self.orm_cls, self.fk_attr_name) == self.data
        else:
            return self.orm_cls.id == self.data.id

    def filter_query(self, query):
        filter_terms = []
        # Get supplied filters.
        if callable(self.query_filter):
            filter_terms.append(self.query_filter(self))
        elif self.query_filter is not None:
            filter_terms.append(self.query_filter)

        # Having an existing value should filter the query.
        if self.data is not None:
            data_filter = self.get_data_filter()
            if data_filter is not None and filter_terms:
                filter_terms.append(data_filter)

        # Apply filter terms with or_, or directly, depending on length.
        if len(filter_terms) == 1:
            query = query.filter(*filter_terms)
        elif len(filter_terms) > 1:
            query = query.filter(sa.sql.or_(*filter_terms))

        return query

    def get_best_label_attr(self):
        if has_column(self.orm_cls, 'label'):
            return 'label'

        if has_column(self.orm_cls, 'name'):
            return 'name'

        return None

    def get_option_label(self, obj):
        if self.label_attr:
            return getattr(obj, self.label_attr_name)

        return str(obj)

    def get_choices(self):
        query = self.build_query()

        def get_value(obj):
            if self.fk_attr:
                return str(getattr(obj, self.fk_attr_name))

            return str(obj.id)

        return [(get_value(obj), self.get_option_label(obj)) for obj in query]

    @property
    def choice_values(self):
        # coerce values used for validation, because the data we're matching will
        # be int type
        return [self.coerce(v) for v in super().choice_values]


class RelationshipField(RelationshipFieldBase, SelectField):
    """SelectField for relationships.

    Args:

        orm_cls (class): Model class of the relationship attribute. Used to query
        records for populating select options.

        label_attr (str): Name of attribute on relationship class to use for select
        option labels.

        fk_attr (str): Optional name of foreign key column of ORM class. If set to
        None, coerce values to instances of ORM class. Otherwise, coerce values to
        the attribute of ORM class the foreign key belongs to. Default is 'id'.

        query_filter (callable): Optional SA query filter criterion for querying select
        options. Can be a function that returns a filter criterion. Function is
        called with the RelationshipField instance it belongs to.

        coerce (callable): Optional function used to coerce form values. By default,
        if fk_attr is set to None, values are coerced to instances of ORM class.
        Otherwise, the default select coersion is applied. Setting this overrides
        default behavior.

        kwargs: Passed to ``SelectField.__init__``.

    Example::
        class Bar(Model):
            name = Column(Unicode(255))
            foos = relationship('Foo', foreign_keys='foos.id')
        class Foo(Model):
            name = Column(Unicode(255))
            bar_id = Column(sa.ForeignKey(Bar.id))
            bar = relationship(Bar, foreign_keys=bar_id)
        class FooForm(ModelForm):
            bar_id = RelationshipField('Bar Label', Bar, 'name')
    """


class RelationshipMultipleField(RelationshipFieldBase, SelectMultipleField):
    """SelectMultipleField for relationships.
    Args:

        orm_cls (class): Model class of the relationship attribute. Used to query
        records for populating select options.

        label_attr (str): Name of attribute on relationship class to use for select
        option labels.

        query_filter (callable): Optional SA query filter criterion for querying select
        options. Can be a function that returns a filter criterion. Function is
        called with the RelationshipField instance it belongs to.

        coerce (callable): Optional function used to coerce form values. By default,
        values are coerced to instances of ORM class. Setting this overrides
        default behavior.

        kwargs: Passed to ``SelectMultipleField.__init__``.

    Example::
        class Bar(Model):
            name = Column(Unicode(255))
            foos = relationship('Foo', foreign_keys='foos.id')
        class Foo(Model):
            name = Column(Unicode(255))
            bar_id = Column(sa.ForeignKey(Bar.id))
            bar = relationship(Bar, foreign_keys=bar_id)
        class BarForm(ModelForm):
            foos = RelationshipMultipleField('Foos', Foo, 'name')
    """
    def __init__(self, label, orm_cls, label_attr=None,
                 query_filter=None, coerce=_not_given, **kwargs):
        coerce = coerce or self.coerce_to_int
        super().__init__(label, orm_cls, label_attr, None, query_filter, coerce, **kwargs)

    def get_data_filter(self):
        if not self.data:
            # Empty set should not add any options. Returning in_ in this case has
            # undesirable results.
            return
        existing_ids = [obj.id for obj in self.data]
        return self.orm_cls.id.in_(existing_ids)

    @staticmethod
    def coerce_to_int(value):
        return int(value)

    def coerce_to_obj(self, value):
        if type(value) in [int, str]:
            return self.orm_cls.query.get(int(value))
        else:
            return value

    def iter_choices(self):
        selected_ids = [v.id for v in self.data or []]
        for value, label in self.choices():
            selected = selected_ids is not None and self.coerce(value) in selected_ids
            yield (value, label, selected)

    def process_formdata(self, valuelist):
        try:
            self.data = list(self.coerce_to_obj(v) for v in valuelist)
        except ValueError:
            raise ValueError(self.gettext('Invalid Choice: could not coerce'))

    def process_data(self, value):
        try:
            self.data = list(v for v in value)
        except (ValueError, TypeError):
            self.data = None

    def pre_validate(self, form):
        if self.data:
            values = list(c[0] for c in self.choices())
            for d in self.data:
                if str(d.id) not in values:
                    raise ValueError(
                        self.gettext("'%(value)s' is not a valid choice for this field")
                        % dict(value=d)
                    )


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
            return Markup(
                '<span class="input-group-addon">{}</span>'.format(wtforms.widgets.core.escape(txt))
            )

        return Markup(
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
            return Markup(
                '<div class="input-group-{type}">'
                '   <span class="input-group-text">{txt}</span>'
                "</div>".format(type=addon_type, txt=wtforms.widgets.core.escape(txt))
            )

        return Markup(
            '<div class="input-group">{pre}{field}{post}</div>'.format(
                pre=make_addon(self.prefix, "prepend") if self.prefix else "",
                field=super().__call__(field, **kwargs).__html__(),
                post=make_addon(self.suffix, "append") if self.suffix else "",
            )
        )


def _max_for_numeric(digits, scale):
    return Decimal('{}.{}'.format('9' * (digits - scale), '9' * scale))


class FormGenerator(FormGeneratorBase):
    """Model form generator that applies field meta info, provides validators, etc.

    Meta nested class directives (in addition to wtforms-alchemy):
    - include_datetimes_with_default
    - include_required_foreign_keys

    Field class overrides:
    - Use our SelectField instead of the WTForms default
    - Use our RequiredBoolRadioField for non-nullable boolean fields
    - Use RelationshipField for foreign key fields

    Meta info modifiers:
    - Use FieldsMeta.<field_name> if provided
    - Falls back to FieldsMeta.__default__
    - If none of the above, uses a blank FieldsMeta object, which will title case the label.

    Validators:
    - Applies range/scale numeric validators when applicable.
    """
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

        # include_foreign_keys will pull in all foreign keys on the object. If we want the
        # form to include only required keys, we use include_required_foreign_keys.
        include_required_fks = getattr(self.meta, 'include_required_foreign_keys', False)
        if (include_required_fks and column.foreign_keys and column.nullable is False):
            return False

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

        # is there an entry in FieldsMeta?
        if hasattr(self.fields_meta, prop.key):
            field_modifier = getattr(self.fields_meta, prop.key)
        else:
            field_modifier = getattr(self.fields_meta, '__default__', _not_given)
            if field_modifier is _not_given:
                field_modifier = FieldMeta

        return field_modifier() if inspect.isclass(field_modifier) else field_modifier

    def create_field(self, prop, column):
        if column.foreign_keys:
            foreign_key = next(iter(column.foreign_keys))
            orm_cls = get_class_by_table(db.Model, foreign_key.column.table)
            validators = self.create_validators(prop, column)
            field = RelationshipField(
                label=to_title_case(str(column.key)),
                orm_cls=orm_cls,
                validators=validators,
            )
        else:
            field = super(FormGenerator, self).create_field(prop, column)

        modifier = self.get_field_modifier(prop)
        if modifier is not None:
            modifier.apply_to_field(field)
        return field

    def create_validators(self, prop, column):
        validators = super(FormGenerator, self).create_validators(prop, column)
        if isinstance(column.type, sa.Numeric) and not isinstance(column.type, sa.Float):
            if column.type.precision is None or column.type.scale is None:
                raise ValueError('Numeric fields must specify precision and scale')
            max_ = _max_for_numeric(column.type.precision, column.type.scale)
            validators.append(NumberRange(min=-max_, max=max_))
            validators.append(NumberScale(column.type.scale))
        return validators

    def length_validator(self, column):
        if isinstance(column.type, sa.types.Enum):
            return None
        return super(FormGenerator, self).length_validator(column)

    def select_field_kwargs(self, column):
        enum_cls = getattr(column.type, 'enum_class', None)
        if enum_cls and issubclass(enum_cls, DBEnum):
            return {
                'coerce': enum_cls.coerce,
                'choices': enum_cls.form_options()
            }
        return super().select_field_kwargs(column)


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
    return dict((str(name), field_to_dict(field))
                for name, field in form._fields.items())


___validator_creation_counter = 0


def form_validator(func=None, only_when_fields_valid=False):
    """Decorator used to mark a method as a form level validator.

    :param only_when_fields_valid: Use to disable validator if form already has errors.
    """
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
    _form_ident_enabled = True
    _form_ident_strict = True

    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        self._form_level_errors = []
        self._errors = None
        self.after_init(args, kwargs)

    def __init_subclass__(cls):
        cls.add_form_ident()
        super().__init_subclass__()

    def __iter__(self):
        custom_field_order = getattr(self, '_field_order', None)

        if custom_field_order is None:
            return super().__iter__()

        order = []
        if hasattr(self, 'csrf_token'):
            order.append('csrf_token')
        if self._form_ident_enabled:
            order.append(self._form_ident_key())
        order.extend(list(custom_field_order))

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
        """Hook for providing customization on the form after fields are initialized."""
        pass

    def fields_todict(self):
        """Turns a form into dicts and lists with both data and errors for each field."""
        return form_fields_to_dict(self)

    def validate(self):
        """Applies validators and returns bool.

        Methods decorated as form-level validators are run after WTForms generic validation.
        """
        fields_valid = super(Form, self).validate()

        form_validators = {}
        # Traverse the MRO so we can get validators in parent classes.
        # Do so in reverse order so child classes can override parents' validators.
        # WTForms will not include the methods on form instances so we get them from the classes.
        for cls in reversed(self.__class__.__mro__):
            cls_validators = {
                name: attr for name, attr in cls.__dict__.items()
                if getattr(attr, '___form_validator', False)
            }
            form_validators.update(cls_validators)

        for validator in sorted(form_validators.values(), key=attrgetter('___creation_counter')):
            try:
                validator(self)
            except StopValidation as e:
                if e.args and e.args[0]:
                    self.form_errors.append(e.args[0])
                break
            except ValueError as e:
                self.form_errors.append(e.args[0])

        return fields_valid and not self.form_errors

    @property
    def field_errors(self):
        """Field-level validator errors come from WTForms' errors."""
        warnings.warn(
            'WTForms has form-level validation now, use form.errors instead', DeprecationWarning, 2
        )
        return self.errors

    @classmethod
    def add_form_ident(cls):
        # may need to clean up from a superclass init, so we have fresh config here
        key = cls._form_ident_key()
        if hasattr(cls, key):
            setattr(cls, key, None)

        if not cls._form_ident_enabled:
            return

        if key.startswith('_'):
            raise Exception('Cannot start form ident name with "_", since WTForms will ignore')

        validators = []
        value = cls._form_ident_value()
        if cls._form_ident_strict:
            validators.append(AnyOf([value]))

        setattr(
            cls,
            key,
            wtforms.fields.HiddenField(
                default=value,
                validators=validators,
            )
        )

    @classmethod
    def _form_ident_key(cls):
        """Field name to embed as a hidden value for form identification. Default is keg_form_ident.

        Note: this cannot start with an underscore, or WTForms will ignore the field.
        """
        return 'keg_form_ident'

    @classmethod
    def _form_ident_value(cls):
        """Field value to embed for form identification. Default is class name converted to
        dash notation."""
        return case_cw2dash(cls.__name__)


BaseModelFormMeta = model_form_meta_factory()


class ModelFormMeta(BaseModelFormMeta):
    """Base model form metaclass that handles nested inheritance issues.

    The default metaclass here will handle the nested Meta class. A form
    subclass with a Meta nested class will treat the form's superclass' Meta
    as a parent.

    This metaclass does the same thing for FieldsMeta, allowing superclasses
    to define a FieldsMeta that may reasonably be passed down to the subclass.
    """
    def __init__(cls, *args, **kwargs):
        bases = []
        for class_ in cls.__mro__:
            if 'FieldsMeta' in class_.__dict__:
                bases.append(getattr(class_, 'FieldsMeta'))

        if object not in bases:
            bases.append(object)

        cls.FieldsMeta = type('FieldsMeta', tuple(bases), {})

        BaseModelFormMeta.__init__(cls, *args, **kwargs)


BaseModelForm = model_form_factory(Form, meta=ModelFormMeta, form_generator=FormGenerator)


class ModelForm(BaseModelForm):
    """Base model-generated form class that applies KegElements generator and meta."""
    @classmethod
    def get_session(cls):
        return db.session
