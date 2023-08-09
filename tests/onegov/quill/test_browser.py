from onegov.core import Framework
from onegov.quill import QuillField
from pytest import fixture
from pytest_localserver.http import WSGIServer
from tests.shared.utils import create_app
from wtforms import Form
from onegov.quill import QuillApp


@fixture(scope='function')
def quill_app(request):

    class QuillTestApp(Framework, QuillApp):
        pass

    @QuillTestApp.path(path='')
    class Root:
        pass

    class QuillForm(Form):
        x = QuillField(tags=['strong', 'ol'])
        y = QuillField(tags=['h3'])

    @QuillTestApp.form(model=Root, form=QuillForm)
    def handle_form(self, request, form):
        request.include('quill')
        return f"""
            <!doctype html>
            <html>
                <body>
                    <form>
                        {form.x()}
                        {form.y()}
                    </form>
                    <script>
                        window.addEventListener("load", function() {{
                            loaded = true;
                        }});
                    </script>
                </body>
            </html>
        """

        result = str(form.x()) + str(form.y())
        return result

    app = create_app(QuillTestApp, request, use_maildir=False)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def wsgi_server(request, quill_app):
    quill_app.print_exceptions = True
    server = WSGIServer(application=quill_app)
    server.start()
    yield server
    server.stop()


@fixture(scope='function')
def browser(request, browser, wsgi_server):
    browser.baseurl = wsgi_server.url
    browser.wsgi_server = wsgi_server
    yield browser


def test_init(browser):
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
