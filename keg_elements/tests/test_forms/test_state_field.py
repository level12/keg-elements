from keg_elements.forms import Form
from keg_elements.forms.state_field import StateField

from .test_form import FormBase


class StateForm(Form):
    short_long = StateField()
    short_short = StateField(short_labels=True)
    long_long = StateField(short_values=False)
    long_short = StateField(short_values=False, short_labels=True)


class TestStateField(FormBase):
    form_cls = StateForm

    def test_state_choices(self):
        form = self.assert_invalid(short_long="ZZ")
        assert form.errors == {"short_long": ["Not a valid choice"]}

        form = self.assert_valid(short_long="MO")
        form = self.assert_invalid(short_long="Missouri")
        assert form.errors == {"short_long": ["Not a valid choice"]}
        assert ('MO', 'Missouri') in form.short_long.choices
        assert ('Missouri', 'MO') not in form.short_long.choices
        assert ('MO', 'MO') not in form.short_long.choices
        assert ('Missouri', 'Missouri') not in form.short_long.choices

        form = self.assert_valid(long_long="Missouri")
        form = self.assert_invalid(long_long="MO")
        assert form.errors == {"long_long": ["Not a valid choice"]}
        assert ('MO', 'Missouri') not in form.long_long.choices
        assert ('Missouri', 'MO') not in form.long_long.choices
        assert ('MO', 'MO') not in form.long_long.choices
        assert ('Missouri', 'Missouri') in form.long_long.choices

        form = self.assert_valid(short_short="MO")
        form = self.assert_invalid(short_short="Missouri")
        assert form.errors == {"short_short": ["Not a valid choice"]}
        assert ('MO', 'Missouri') not in form.short_short.choices
        assert ('Missouri', 'MO') not in form.short_short.choices
        assert ('MO', 'MO') in form.short_short.choices
        assert ('Missouri', 'Missouri') not in form.short_short.choices

        form = self.assert_valid(long_short="Missouri")
        form = self.assert_invalid(long_short="MO")
        assert form.errors == {"long_short": ["Not a valid choice"]}
        assert ('MO', 'Missouri') not in form.long_short.choices
        assert ('Missouri', 'MO') in form.long_short.choices
        assert ('MO', 'MO') not in form.long_short.choices
        assert ('Missouri', 'Missouri') not in form.long_short.choices
