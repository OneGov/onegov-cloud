from __future__ import annotations

import morepath

from onegov.core import Framework
from onegov.core import filters  # noqa: F401 -> registers webasset filters
from onegov.core.utils import scan_morepath_modules
from onegov.quill import QuillApp
from webtest import TestApp as Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest


def test_integration(temporary_directory: str, redis_url: str) -> None:

    class App(Framework, QuillApp):
        pass

    @App.webasset_output()
    def get_output_path() -> str:
        return temporary_directory

    @App.path(path='')
    class Root:
        pass

    @App.html(model=Root)
    def view_root(self: Root, request: CoreRequest) -> str:
        request.include('quill')
        return '<body></body>'

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'foo'
    app.configure_application(redis_url=redis_url)
    app.set_application_id('foo/bar')

    assert 'quill.bundle.js' in Client(app).get('/')
