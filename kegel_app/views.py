from keg_elements.core import keg_element_blueprint
from keg_elements.views import GridView

from kegel_app import grids


class DemoGrid(GridView):
    blueprint = keg_element_blueprint
    grid_cls = grids.DemoGrid
