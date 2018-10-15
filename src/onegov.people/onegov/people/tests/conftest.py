from onegov_testing.utils import create_app
from onegov.core import Framework
from onegov.file import DepotApp
from pytest import fixture


class TestApp(Framework, DepotApp):
    pass


@fixture(scope='function')
def test_app(request):
    app = create_app(TestApp, request, use_smtp=False)
    yield app
    app.session_manager.dispose()
