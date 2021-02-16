from onegov.core.utils import Bunch
from onegov.page import Page
from onegov.town6.layout import DefaultLayout


class MockModel(object):
    pass


class MockRequest(object):
    locale = 'en'
    is_logged_in = False
    is_manager = False
    app = Bunch(org=Bunch(geo_provider='geo-mapbox'))

    def include(self, *args, **kwargs):
        pass

    def link(self, model):
        if isinstance(model, Page):
            return model.path

    def exclude_invisible(self, objects):
        return objects


def test_default_layout():
    layout = DefaultLayout(MockModel(), MockRequest())
    assert layout.top_navigation