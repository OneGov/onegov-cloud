from onegov.core.crypto import hash_password
from onegov.gazette import GazetteApp
from onegov_testing.utils import create_app
from onegov.user import User
from pytest import fixture
from textwrap import dedent
from transaction import commit


@fixture(scope='session')
def gazette_password():
    return hash_password('hunter2')


def create_gazette(request):
    app = create_app(GazetteApp, request, use_smtp=True)
    app.session_manager.set_locale('de_CH', 'de_CH')
    app.filestorage.settext('principal.yml', dedent("""
        name: Kanton Zug
        color: '#006FB5'
        logo: 'canton-zg.svg'
        publish_to: 'printer@onegov.org'
        organizations:
            - '100': Staatskanzlei Kanton Zug
            - '210': Bürgergemeinde Zug
            - '310': Einwohnergemeinde Zug
            - '400': Evangelisch-reformierte Kirchgemeinde des Kantons Zug
            - '501': Katholische Kirchgemeinde Baar
            - '509': Katholische Kirchgemeinde Zug
            - '609': Korporation Zug
        categories:
            - '12': Weiterbildung
            - '13': Submissionen
            - '14': Kantonale Mitteilungen
            - '16': Bürgergemeinden
            - '17': Kath. Kirchgemeinden
            - '18': Ev.-ref. Kirchgemeinde
            - '19': Korporationen
            - '20': Handelsregister
        issues:
            2017:
                40: 2017-10-06
                41: 2017-10-13
                42: 2017-10-20
                43: 2017-10-27
                44: 2017-11-03
                45: 2017-11-10
                46: 2017-11-17
                47: 2017-11-24
                48: 2017-12-01
                49: 2017-12-08
                50: 2017-12-15
                51: 2017-12-22
                52: 2017-12-29
            2018:
                1: 2018-01-05

    """))

    app.session().add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='admin'
    ))
    app.session().add(User(
        username='publisher@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='editor'
    ))
    app.session().add(User(
        username='editor@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='member'
    ))

    commit()

    return app


@fixture(scope="function")
def gazette_app(request):

    app = create_gazette(request)
    yield app
    app.session_manager.dispose()
