import flask
from keg.web import BaseView

from keg_elements.extensions import gettext as _


class GridView(BaseView):
    """Base view for simple grid pages."""
    grid_cls = None
    """Grid class to construct, or callable returning a grid instance."""
    template = 'grid_view.html'
    """Template to render. Defaults to grid_view.html, but this is not provided by keg_elements."""
    title = None
    """Page title, will be assigned as title for the template."""

    def get(self):
        return self.render_grid()

    def init_grid(self):
        """ Create an instance of `grid_cls` """
        return self.grid_cls()

    def post_args_grid_setup(self, grid):
        """ Apply changes to grid instance after QS args/session are loaded """
        return grid

    def get_grid_template_args(self, arg_dict):
        """ Return any template arguments needed for render.

        By default, `grid` and `title` arguments are passed in.
        """
        return arg_dict

    def on_render_limit_exceeded(self, grid):
        """ Handles export limit exceeded case. By default, shows a flash message."""
        flask.flash(_('Too many records to export as {}').format(grid.export_to), 'error')

    def render_grid(self):
        """ Build grid, handle loading args and conditional export, and render result."""
        if self.grid_cls is None:
            raise NotImplementedError(
                'You must set {}.grid_cls to render a grid'.format(self.__class__.__name__)
            )

        grid = self.init_grid()
        grid.apply_qs_args()

        grid = self.post_args_grid_setup(grid)

        if grid.export_to:
            import webgrid

            try:
                return grid.export_as_response()
            except webgrid.renderers.RenderLimitExceeded:
                self.on_render_limit_exceeded(grid)

        # args added with self.assign should be passed through here
        template_args = self.get_grid_template_args(dict(self.template_args, **{
            'grid': grid,
            'title': self.title,
        }))

        return flask.render_template(self.template, **template_args)
