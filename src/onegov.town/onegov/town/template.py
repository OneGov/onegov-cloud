from cached_property import cached_property


class TemplateApi(object):
    """ Passed to all chameleon templates, this object provides access to the
    layout, macros and other variables needed in all templates.

    To render a template with the api do the following::

        @TownApp.html(model=Example, template='example.pt', permission=Public)
        def view_example(self, request):
            return { 'api': TemplateApi(self, request) }

    """

    def __init__(self, model, request):
        self.model = model
        self.request = request

    @cached_property
    def app(self):
        """ Returns the application behind the request. """
        return self.request.app

    @cached_property
    def page_id(self):
        """ Returns the unique page id of the rendered page. Used to have
        a useful id in the body element for CSS/JS.

        """
        page_id = self.request.path_info
        page_id = page_id.lstrip('/')
        page_id = page_id.replace('/', '-')
        page_id = page_id.rstrip('-')

        return page_id or 'root'

    @cached_property
    def template_loader(self):
        """ Returns the chameleon template loader. """
        return self.app.registry._template_loaders['.pt']

    @cached_property
    def layout(self):
        """ Returns the layout, which defines the basic layout of all town
        pages. See ``templates/layout.pt``.

        """
        return self.template_loader['layout.pt']
