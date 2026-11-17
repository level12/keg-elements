import flask
from kegel_app import forms, grids

from keg_elements.core import keg_element_blueprint
from keg_elements.views import FormView, GridView


class DemoGrid(GridView):
    blueprint = keg_element_blueprint
    grid_cls = grids.DemoGrid


class DemoForm(FormView):
    blueprint = keg_element_blueprint
    form_cls = forms.DemoForm

    def form_on_valid(self):
        return flask.redirect('/demo-grid')
