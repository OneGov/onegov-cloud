from onegov.core import Framework
from onegov.core.layout import ChameleonLayout


class FoundationApp(Framework):
    pass


@FoundationApp.webasset_path()
def get_foundation_js_path():
    return 'assets'


@FoundationApp.webasset('foundation6')
def get_foundation_js_assets():
    yield 'jquery.js'
    yield 'what-input.js'
    yield 'foundation.min.js'
    yield 'foundation-init.js'


class FoundationLayout(ChameleonLayout):
    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('foundation6')
