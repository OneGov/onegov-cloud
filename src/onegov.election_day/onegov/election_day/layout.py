from cached_property import cached_property


class Layout(object):
    """ Contains methods to render a page inheriting from layout.pt. """

    def __init__(self, model, request):
        self.model = model
        self.request = request

    @cached_property
    def template_loader(self):
        """ Returns the chameleon template loader. """
        return self.request.app.registry._template_loaders['.pt']

    @cached_property
    def base(self):
        """ Returns the layout, which defines the base layout of all town
        pages. See ``templates/layout.pt``.

        """
        return self.template_loader['layout.pt']


class DefaultLayout(Layout):
    pass
