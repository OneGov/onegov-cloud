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
        categories:
            - '14': Kantonale Mitteilungen
              children:
                - '1402': Einberufung Kantonsrat
                - '1403': Wahlen/Abstimmungen
                - '1406': Kant. Gesetzgebung
                - '1411': Mitteilungen Landschreiber
                - '1412': Kant. Stellenangebote
                - '1413': Direktion des Innern
                - '1414': Direktion für Bildung und Kultur
                - '1415': Volkswirtschaftsdirektion
                - '1416': Baudirektion
                - '1418': Gesundheitsdirektion
                - '1421': Finanzdirektion
                - '1426': Gerichtliche Bekanntmachungen
                - '1427': Konkursamt
            - '13': Submissionen
            - '16': Bürgergemeinden
            - '17': Kath. Kirchgemeinden
            - '18': Ev.-ref. Kirchgemeinde
            - '19': Korporationen
            - '12': Weiterbildung
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
