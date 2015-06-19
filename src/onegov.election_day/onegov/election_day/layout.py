from cached_property import cached_property
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile


class Layout(ChameleonLayout):

    def __init__(self, request, model):
        super(Layout, self).__init__(request, model)
        self.request.include('common')

    @cached_property
    def homepage_link(self):
        return self.request.link(self.request.app.principal)

    @cached_property
    def font_awesome_path(self):
        static_file = StaticFile.from_application(
            self.app, 'font-awesome/css/font-awesome.min.css')

        return self.request.link(static_file)

    def get_topojson_link(self, canton, year):
        return self.request.link(
            StaticFile('mapdata/{}/{}.json'.format(year, canton)))


class DefaultLayout(Layout):
    pass
