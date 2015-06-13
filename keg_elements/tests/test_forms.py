
from pyquery import PyQuery as pq
from keg_elements.forms import Form, SelectField
from werkzeug.datastructures import MultiDict
from wtforms import validators


class FormBase(object):
    form_cls = None

    def assert_invalid(self, data):
        form = self.form_cls(MultiDict(data), csrf_enabled=False)
        assert not form.validate()
        return form

    def assert_valid(self, data):
        form = self.form_cls(MultiDict(data), csrf_enabled=False)
        assert form.validate(), form.errors
        return form


class FruitForm(Form):
    fruit = SelectField(validators=[validators.Optional()],
                        choices=[('apple', 'apple'), ('banana', 'banana')])
    letter = SelectField(validators=[validators.Optional()],
                         choices=[('a', 'a'), ('b', 'b'), ('', 'blank')], add_blank_choice=False)
    number = SelectField(validators=[validators.InputRequired()], choices=[('1', '1'), ('0', '0')])


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
        form = self.assert_valid({'fruit': '', 'letter': '', 'number': '1'})

        assert form.fruit.data is None
        assert form.letter.data == ''

    def test_blank_choice_required(self):
        form = self.assert_invalid({'number': ''})
        assert form.number.errors == ['This field is required.']

        form = self.assert_valid({'number': '0'})
