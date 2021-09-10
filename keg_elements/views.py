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
        """GET method responder. By default, fully processes and renders grid to template."""
        return self.render_grid()

    def allow_post(self, grid):
        """Inspects the grid manager's arg loads to determine if post should be allowed."""
        from webgrid.extensions import RequestFormLoader
        if grid.manager and RequestFormLoader not in grid.manager.args_loaders:
            flask.abort(405)

    def post(self):
        """POST method responder.

        For session-enabled grids (the default), process the args, which will save any form
        args into the grid's session store. Then, redirect to a GET request on the same URL.

        If the grid is not session-enabled, render to the template.

        Note: for request form args to be processed, the grid's manager must be set up with
        an args loader that uses them.
        """
        if not self.grid_cls.session_on:
            return self.render_grid()
        self.allow_post(
            self.process_grid()
        )
        return flask.redirect(flask.request.full_path)

    def init_grid(self):
        """ Create an instance of `grid_cls` """
        return self.grid_cls()

    def process_grid(self):
        """Create grid instance and run args collection/processing for grid state."""
        if self.grid_cls is None:
            raise NotImplementedError(
                'You must set {}.grid_cls to render a grid'.format(self.__class__.__name__)
            )

        grid = self.init_grid()
        grid.apply_qs_args()

        return self.post_args_grid_setup(grid)

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
        grid = self.process_grid()

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
