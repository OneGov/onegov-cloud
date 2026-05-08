from __future__ import annotations

import pytest
from onegov.core import Framework
from onegov.quill import QuillField
from pytest_localserver.http import WSGIServer  # type: ignore[import-untyped]
from tests.shared.utils import create_app
from wtforms import Form
from onegov.quill import QuillApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest
    from tests.shared.browser import ExtendedBrowser


class QuillTestApp(Framework, QuillApp):
    pass


@pytest.fixture(scope='function')
def quill_app(request: pytest.FixtureRequest) -> Iterator[QuillTestApp]:

    class _QuillTestApp(QuillTestApp):
        pass

    @_QuillTestApp.path(path='')
    class Root:
        pass

    class QuillForm(Form):
        x = QuillField(tags=['strong', 'ol'])
        y = QuillField(tags=['h3'])

    @_QuillTestApp.form(model=Root, form=QuillForm)
    def handle_form(self: Root, request: CoreRequest, form: QuillForm) -> str:
        request.include('quill')
        nonce = request.content_security_policy_nonce('script')
        return f"""
            <!doctype html>
            <html>
                <body>
                    <form>
                        {form.x()}
                        {form.y()}
                    </form>
                    <script nonce="{nonce}">
                        window.addEventListener("load", function() {{
                            loaded = true;
                        }});
                    </script>
                </body>
            </html>
        """

    app = create_app(_QuillTestApp, request, use_maildir=False)
    yield app
    app.session_manager.dispose()


@pytest.fixture(scope='function')
def wsgi_server(
    request: pytest.FixtureRequest,
    quill_app: QuillTestApp
) -> Iterator[WSGIServer]:

    quill_app.print_exceptions = True
    server = WSGIServer(application=quill_app)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope='function')
def browser(
    request: pytest.FixtureRequest,
    browser: ExtendedBrowser,
    wsgi_server: WSGIServer
) -> Iterator[ExtendedBrowser]:
    browser.baseurl = wsgi_server.url
    browser.wsgi_server = wsgi_server  # type: ignore[attr-defined]
    yield browser


def test_init(browser: ExtendedBrowser) -> None:
    # FIXME: Getting rid of this error might require updating
    #        to a newer version of quill
    browser.visit('/', expected_errors=[{
        'level': 'WARNING', 'rgxp': 'Consider using MutationObserver'
    }])
    assert 'quill.bundle.js' in browser.html
    browser.wait_for_js_variable('loaded')
    toolbars = browser.find_by_css('.ql-toolbar')
    assert len(toolbars) == 2
    assert toolbars[0].find_by_css('button.ql-bold')
    assert toolbars[0].find_by_css('button.ql-list')
    assert not toolbars[0].find_by_css('button.ql-header')
    assert not toolbars[1].find_by_css('button.ql-bold')
    assert not toolbars[1].find_by_css('button.ql-list')
    assert toolbars[1].find_by_css('button.ql-header')
