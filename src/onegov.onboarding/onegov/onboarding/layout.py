from cached_property import cached_property
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile


class Layout(ChameleonLayout):

    @cached_property
    def font_awesome_path(self):
        static_file = StaticFile.from_application(
            self.app, 'font-awesome/css/font-awesome.min.css')

        return self.request.link(static_file)

    @cached_property
    def logo_path(self):
        static_file = StaticFile.from_application(self.app, 'logo.svg')

        return self.request.link(static_file)


class DefaultLayout(Layout):
    pass
