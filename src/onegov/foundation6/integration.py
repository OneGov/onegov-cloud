from onegov.core import Framework
from onegov.core.layout import ChameleonLayout


class FoundationApp(Framework):
    pass


@FoundationApp.webasset_path()
def get_foundation_js_path():
    return 'precompiled'


@FoundationApp.webasset('foundation-js')
def get_foundation_js_assets():
    yield 'foundation.min.js'


class FoundationLayout(ChameleonLayout):
    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('foundation.min.js')
