import pytest
from depot.manager import DepotManager
from onegov.core import Framework
from onegov.core.framework import default_content_security_policy
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
        yield 'react.production.min.js'
        yield 'react-dom.production.min.js'
        yield 'create-react-class.min.js'
        yield 'font-awesome.min.css'

    @TestApp.setting(section='content_security_policy', name='default')
    def get_content_security_policy():
        policy = default_content_security_policy()
        policy.script_src.add('cdnjs.cloudflare.com')
        return policy

    @TestApp.path(path='/snippets')
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

    @TestApp.path(path='/registry')
    class Registry(Content):
        html = """
            <!doctype html>
            <html>
                <head><script type="text/javascript" src="{}"></script></head>
                <body></body>
            </html>
        """.format(react)

    @TestApp.path(path='/formcode-format')
    class FormcodeFormat(Content):
        html = """
            <!doctype html>
            <html>
                <head>
                    <script type="text/javascript" src="{}"></script>
                    <script type="text/javascript" src="{}"></script>
                    <link rel="stylesheet" href="{}">
                </head>
                <body>
                    <div id="container"></div>
                    <textarea></textarea>
                </body>
            </html>
        """.format(react, react_dom, fontawesome)

    @TestApp.path(path='/formcode-select')
    class FormcodeSelect(Content):
        html = """
            <!doctype html>
            <html>
                <head>
                    <script type="text/javascript" src="{}"></script>
                    <script type="text/javascript" src="{}"></script>
                </head>
                <body>
                    <div id="container"></div>
                    <textarea></textarea>
                </body>
            </html>
        """.format(react, react_dom)

    @TestApp.html(model=Content)
    def view_content(self, request):
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
