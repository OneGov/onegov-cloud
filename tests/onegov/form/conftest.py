import pytest

from depot.manager import DepotManager
from onegov.core import Framework
from onegov.form import FormApp
from onegov.form.extensions import form_extensions
from onegov.form.utils import disable_required_attribute_in_html_inputs
from pytest_localserver.http import WSGIServer
from tests.shared.utils import create_app


@pytest.fixture(scope='session', autouse=True)
def disable_required_attribute_in_tests():
    disable_required_attribute_in_html_inputs()


@pytest.fixture(scope='function', autouse=True)
def depot():
    DepotManager.configure('default', {
        'depot.backend': 'depot.io.memory.MemoryFileStorage'
    })

    yield DepotManager.get()

    DepotManager._clear()


@pytest.fixture(scope='function', autouse=True)
def extensions():
    # discards form extensions defined in tests
    known_extensions = form_extensions.copy()

    yield

    form_extensions.clear()
    form_extensions.update(known_extensions)


@pytest.fixture(scope='function')
def form_app(request):

    class TestApp(Framework, FormApp):
        pass

    class Content:
        pass

    @TestApp.webasset_path()
    def get_js_path() -> str:
        return 'assets'

    @TestApp.webasset_path()
    def get_css_path() -> str:
        return 'assets'

    @TestApp.webasset_output()
    def get_webasset_output() -> str:
        return 'assets'

    @TestApp.webasset('react')
    def get_react_asset():
        yield 'react-with-addons.min.js'
        yield 'react-dom.min.js'
        yield 'font-awesome.min.css'

    @TestApp.path(path='/snippets')
    class Snippets(Content):
        html = """
            <!doctype html>
            <html>
                <head>
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
        """

    @TestApp.path(path='/registry')
    class Registry(Content):
        html = """
            <!doctype html>
            <html>
                <head></head>
                <body></body>
            </html>
        """

    @TestApp.path(path='/formcode-format')
    class FormcodeFormat(Content):
        html = """
            <!doctype html>
            <html>
                <head></head>
                <body>
                    <div id="container"></div>
                    <textarea></textarea>
                </body>
            </html>
        """

    @TestApp.path(path='/formcode-select')
    class FormcodeSelect(Content):
        html = """
            <!doctype html>
            <html>
                <head></head>
                <body>
                    <div id="container"></div>
                    <textarea></textarea>
                </body>
            </html>
        """

    @TestApp.html(model=Content)
    def view_content(self, request):
        request.include('react')
        request.include('formcode')
        return self.html

    return create_app(TestApp, request, use_maildir=False)


@pytest.fixture(scope='function')
def browser(browser, form_app_url):
    browser.baseurl = form_app_url
    yield browser


@pytest.fixture(scope='function')
def form_app_url(request, form_app):
    form_app.print_exceptions = True
    server = WSGIServer(application=form_app)
    server.start()
    yield server.url
    server.stop()
