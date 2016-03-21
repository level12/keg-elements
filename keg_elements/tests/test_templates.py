from __future__ import absolute_import

import itertools

import keg
from keg_elements.forms import Form
from pyquery import PyQuery
from wtforms import RadioField, StringField


class TemplateTest(object):
    def render(self, filename, args=None):
        template = keg.current_app.jinja_env.get_template(filename)
        return PyQuery(template.render(**(args or {})))


class TestGenericTemplates(TemplateTest):
    def test_form_field_value_macro(self):
        class TestForm(Form):
            test = StringField()

        value = 'ablewasiereisawelba'

        response = self.render('form-field-value-macro.html', {
            'form': TestForm(test=value),
            'field_name': 'test'
        })

        assert response('#dynamic #default #test')[0].value == value
        assert response('#dynamic #doubled #test')[0].value == value  # dynamic is unaffected

        assert response('#static #default #test').text() == value
        assert response('#static #doubled #test').text() == value * 2   # static is doubled

    def test_section_macro(self):
        class TestForm(Form):
            test = StringField()

        response = self.render('section-macro.html', {
            'form': TestForm(test='test-value'),
            'field_name': 'test'
        })

        assert response('#dynamic #with-caller #test')[0].value == 'test-value'
        assert response('#dynamic #with-field-name #test')[0].value == 'test-value'

        assert response('#static #with-caller #test').text() == 'test-value'
        assert response('#static #with-field-name #test').text() == 'test-value'


class TestReadonlyOrDisabledFormRender(TemplateTest):
    class TestForm(Form):
        radio_options = ['A', 'B', 'C']
        radio_choices = [(x, x) for x in radio_options]

        def field_flag(flags):
            """Creates a no-op validator that has the given field flags."""
            class FlaggedValidator(object):
                field_flags = flags

                def __call__(self, form, field):
                    pass

            return FlaggedValidator()

        text = StringField('Text')
        text_readonly = StringField('Read-only Text', [field_flag({'readonly'})])
        text_disabled = StringField('Disabled Text', [field_flag({'disabled'})])

        radio = RadioField('Radio', choices=radio_choices)
        radio_readonly = RadioField('Read-only Radio', [field_flag({'readonly'})],
                                    choices=radio_choices)
        radio_disabled = RadioField('Disabled Radio', [field_flag({'disabled'})],
                                    choices=radio_choices)

    def test_input_fields(self):
        def assert_string_field_attr(field_name, attr_name, attr_value):
            response = self.render('generic-input-field.html', {
                'form': self.TestForm(**{field_name: 'some-data'}),
                'field_name': field_name
            })

            assert response('#static #' + field_name).attr(attr_name) is None
            assert response('#dynamic #' + field_name).attr(attr_name) == attr_value

        assert_string_field_attr('text', 'readonly', None)
        assert_string_field_attr('text', 'disabled', None)

        assert_string_field_attr('text_readonly', 'readonly', 'readonly')
        assert_string_field_attr('text_readonly', 'disabled', None)

        assert_string_field_attr('text_disabled', 'readonly', None)
        assert_string_field_attr('text_disabled', 'disabled', 'disabled')

    def render_radio_field(self, field_name, field_value):
        return self.render('generic-radio-field.html', {
            'form': self.TestForm(**{field_name: field_value}),
            'field_name': field_name
        })

    def test_normal_radio(self):
        response = self.render_radio_field('radio', 'A')

        assert response('#dynamic input[value=A]').attr.checked == 'checked'

        for root, label in itertools.product({'#static', '#dynamic'},
                                             self.TestForm.radio_options):
            sel = '{} input[value={}]'.format(root, label)
            response(sel).attr.readonly is None
            response(sel).attr.disabled is None
            response(sel).attr.readonly is None
            response(sel).attr.disabled is None

    def test_readonly_radio(self):
        response = self.render_radio_field('radio_readonly', 'B')
        radio_at_value = lambda value: response('#dynamic input[value={}]'.format(value))

        assert radio_at_value('B').attr.checked == 'checked'
        assert not radio_at_value('A').attr.readonly
        assert not radio_at_value('B').attr.readonly
        assert not radio_at_value('C').attr.readonly
        assert radio_at_value('A').attr.disabled
        assert not radio_at_value('B').attr.disabled
        assert radio_at_value('C').attr.disabled

        assert response('#static p').text() == 'B'

    def test_disabled_radio(self):
        response = self.render_radio_field('radio_disabled', 'C')
        radio_at_value = lambda value: response('#dynamic input[value={}]'.format(value))

        assert radio_at_value('C').attr.checked == 'checked'
        assert not radio_at_value('A').attr.readonly
        assert not radio_at_value('B').attr.readonly
        assert not radio_at_value('C').attr.readonly
        assert radio_at_value('A').attr.disabled
        assert radio_at_value('B').attr.disabled
        assert radio_at_value('C').attr.disabled

        assert response('#static p').text() == 'C'


class TestFieldMacros(TemplateTest):
    class TestForm(Form):
        myfield = StringField('My Field')

    def test_div_form_group(self):
        response = self.render('field-macros.html', {
            'form': self.TestForm(myfield='My Data'),
            'field_name': 'myfield',
            'form_group_class': None,
            'field_kwargs': {},
        })

        assert response('#dynamic #div_form_group div.form-group').text() == 'Contents'
        assert response('#static  #div_form_group div.form-group').text() == 'Contents'

        assert response('#dynamic #field_widget #myfield')[0].value == 'My Data'
        assert response('#static  #field_widget #myfield').text() == 'My Data'
