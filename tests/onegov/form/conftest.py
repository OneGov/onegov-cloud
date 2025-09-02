from __future__ import annotations

import pytest

from depot.manager import DepotManager
from onegov.core import Framework
from onegov.core.framework import default_content_security_policy
from onegov.form import FormApp
from onegov.form.extensions import form_extensions
from onegov.form.utils import disable_required_attribute_in_html_inputs
from pytest_localserver.http import WSGIServer  # type: ignore[import-untyped]
from tests.shared.utils import create_app


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from depot.io.interfaces import FileStorage
    from more.content_security import ContentSecurityPolicy
    from onegov.core.request import CoreRequest
    from tests.shared.browser import ExtendedBrowser


class TestApp(Framework, FormApp):
    __test__ = False


@pytest.fixture(scope='session', autouse=True)
def disable_required_attribute_in_tests() -> None:
    disable_required_attribute_in_html_inputs()


@pytest.fixture(scope='function', autouse=True)
def depot(temporary_directory: str) -> Iterator[FileStorage | None]:
    DepotManager.configure('default', {
        'depot.backend': 'depot.io.memory.MemoryFileStorage'
    })

    yield DepotManager.get()

    DepotManager._clear()  # type: ignore[attr-defined]


@pytest.fixture(scope='function', autouse=True)
def extensions() -> Iterator[None]:
    # discards form extensions defined in tests
    known_extensions = form_extensions.copy()

    yield

    form_extensions.clear()
    form_extensions.update(known_extensions)


@pytest.fixture(scope='function')
def form_app(request: pytest.FixtureRequest) -> TestApp:

    # we do not support react 16 yet, as it basically requires ES6
    react = (
        'https://cdnjs.cloudflare.com/ajax/libs/react/15.6.2/'
        'react-with-addons.min.js'
    )
    react_dom = (
        'https://cdnjs.cloudflare.com/ajax/libs/react-dom/15.6.2/'
        'react-dom.min.js'
    )
    fontawesome = (
        'https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0'
        '/css/font-awesome.min.css'
    )

    class _TestApp(TestApp):
        pass

    class Content:
        html: str

    @_TestApp.setting(section='content_security_policy', name='default')
    def get_content_security_policy() -> ContentSecurityPolicy:
        policy = default_content_security_policy()
        policy.script_src.add('cdnjs.cloudflare.com')
        return policy

    @_TestApp.path(path='/snippets')
    class Snippets(Content):
        html = """
            <!doctype html>
            <html>
                <head>
                    <script type="text/javascript" src="{}"></script>
                    <script type="text/javascript" src="{}"></script>
                    <link rel="stylesheet" href="{}">
                    <style>
                        .formcode-toolbar-element {{
                            height: 10px;
                            width: 10px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="formcode-snippets"
                        data-source='/formcode-snippets'
                        data-target='textarea'
                    />

                    <textarea></textarea>
                </body>
            </html>
        """.format(react, react_dom, fontawesome)

    @_TestApp.path(path='/registry')
    class Registry(Content):
        html = f"""
            <!doctype html>
            <html>
                <head>
                    <script type="text/javascript" src="{react}"></script>
                </head>
                <body></body>
            </html>
        """

    @_TestApp.path(path='/formcode-format')
    class FormcodeFormat(Content):
        html = f"""
            <!doctype html>
            <html>
                <head>
                    <script type="text/javascript" src="{react}"></script>
                    <script type="text/javascript" src="{react_dom}"></script>
                    <link rel="stylesheet" href="{fontawesome}">
                </head>
                <body>
                    <div id="container"></div>
                    <textarea></textarea>
                </body>
            </html>
        """

    @_TestApp.path(path='/formcode-select')
    class FormcodeSelect(Content):
        html = f"""
            <!doctype html>
            <html>
                <head>
                    <script type="text/javascript" src="{react}"></script>
                    <script type="text/javascript" src="{react_dom}"></script>
                </head>
                <body>
                    <div id="container"></div>
                    <textarea></textarea>
                </body>
            </html>
        """

    @_TestApp.html(model=Content)
    def view_content(self: Content, request: CoreRequest) -> str:
        request.include('formcode')
        return self.html

    return create_app(TestApp, request, use_maildir=False)


@pytest.fixture(scope='function')
def form_app_url(
    request: pytest.FixtureRequest,
    form_app: TestApp
) -> Iterator[str]:
    form_app.print_exceptions = True
    server = WSGIServer(application=form_app)
    server.start()
    yield server.url
    server.stop()


@pytest.fixture(scope='function')
def browser(
    browser: ExtendedBrowser,
    form_app_url: str
) -> Iterator[ExtendedBrowser]:
    browser.baseurl = form_app_url
    yield browser
