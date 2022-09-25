from io import BytesIO
from onegov.core import Framework
from onegov.file import DepotApp
from onegov.pdf import Pdf
from pytest import fixture
from tests.shared.utils import create_app


class TestApp(Framework, DepotApp):
    pass


@fixture(scope='function')
def test_app(request):
    app = create_app(TestApp, request, use_maildir=False)
    app.session_manager.set_locale('de_CH', 'de_CH')
    yield app
    app.session_manager.dispose()


@fixture(scope="function")
def explanations_pdf():
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Erläuterungen")
    pdf.generate()
    result.seek(0)
    return result


@fixture(scope="function")
def upper_apportionment_pdf():
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Oberzuteilung")
    pdf.generate()
    result.seek(0)
    return result


@fixture(scope="function")
def lower_apportionment_pdf():
    result = BytesIO()
    pdf = Pdf(result)
    pdf.init_report()
    pdf.p("Unterzuteilung")
    pdf.generate()
    result.seek(0)
    return result
