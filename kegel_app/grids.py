from webgrid import Column
from webgrid.filters import TextFilter

from kegel_app.extensions import Grid
from kegel_app.model import entities as ents


class DemoGrid(Grid):
    Column('Name', ents.Thing.name, TextFilter)
