from kegel_app.extensions import Grid
from kegel_app.model import entities as ents
from webgrid import Column
from webgrid.filters import TextFilter


class DemoGrid(Grid):
    Column('Name', ents.Thing.name, TextFilter)
