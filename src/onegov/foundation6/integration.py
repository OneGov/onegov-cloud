from onegov.core import Framework
from onegov.core.request import CoreRequest


class FoundationRequest(CoreRequest):
    def __init__(self, *args, **kwargs):
        super(FoundationRequest, self).__init__(*args, **kwargs)
        # self.include('foundation-js')


class FoundationApp(Framework):
    request_class = FoundationRequest


@FoundationApp.webasset_path()
def get_foundation_js_path():
    return 'precompiled'


@FoundationApp.webasset('foundation-js')
def get_foundation_js_assets():
    yield 'foundation.min.js'
