from __future__ import absolute_import

import keg
from keg_elements.forms import Form
from pyquery import PyQuery
from wtforms import StringField


class TestTemplates(object):
    def render(self, filename, args=None):
        template = keg.current_app.jinja_env.get_template(filename)
        return PyQuery(template.render(**(args or {})))

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
        assert response('#static #doubled #test').text() == value*2   # static is doubled

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
