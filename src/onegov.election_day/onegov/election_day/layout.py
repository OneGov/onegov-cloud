from cached_property import cached_property
from onegov.core.layout import ChameleonLayout


class Layout(ChameleonLayout):

    def __init__(self, request, model):
        super(Layout, self).__init__(request, model)
        self.request.include('common')

    @cached_property
    def homepage_link(self):
        return self.request.link(self.request.app.principal)


class DefaultLayout(Layout):
    pass
