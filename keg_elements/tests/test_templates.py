from __future__ import absolute_import

import keg
from keg_elements.forms import Form
from pyquery import PyQuery
from wtforms import StringField


class TestTemplates(object):
    def setup_method(self, method):
        self.ctx = keg.current_app.test_request_context()
        self.ctx.push()

    def teardown_method(self, method):
        self.ctx.pop()

    def render(self, filename, args=None):
        template = keg.current_app.jinja_env.get_template(filename)
        return template.render(**(args or {}))

    def test_form_field_value_macro(self):
        class TestForm(Form):
            test = StringField()

        response = self.render('form-field-value-macro.html', {
            'form': TestForm(test='ablewasiereisawelba'),
            'field_name': 'test'
        })
        assert 'ablewasiereisawelba'*2 in PyQuery(response.body)('#dynamic')
