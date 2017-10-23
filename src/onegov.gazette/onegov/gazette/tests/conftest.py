from onegov_testing.utils import create_app
from onegov.core.crypto import hash_password
from onegov.gazette import GazetteApp
from onegov.gazette.models.principal import Principal
from onegov.user import User
from onegov.user import UserGroup
from pytest import fixture
from textwrap import dedent
from transaction import commit
from uuid import uuid4


PRINCIPAL = """
    name: Govikon
    color: '#006FB5'
    logo: 'govikon.svg'
    publish_to: 'printer@onegov.org'
    organizations:
        - '100': State Chancellery
        - '200': Civic Community
        - '300': Municipality
        - '400': Evangelical Reformed Parish
        - '500': Catholic Parish
        - '600': Corporation
    categories:
        - '11': Education
        - '12': Submissions
        - '13': Commercial Register
        - '14': Elections
    issues:
        2017:
            40: 2017-10-06 / 2017-10-04T12:00:00
            41: 2017-10-13 / 2017-10-11T12:00:00
            42: 2017-10-20 / 2017-10-18T12:00:00
            43: 2017-10-27 / 2017-10-25T12:00:00
            44: 2017-11-03 / 2017-11-01T12:00:00
            45: 2017-11-10 / 2017-11-08T12:00:00
            46: 2017-11-17 / 2017-11-15T12:00:00
            47: 2017-11-24 / 2017-11-22T12:00:00
            48: 2017-12-01 / 2017-11-29T12:00:00
            49: 2017-12-08 / 2017-12-06T12:00:00
            50: 2017-12-15 / 2017-12-13T12:00:00
            51: 2017-12-22 / 2017-12-20T12:00:00
            52: 2017-12-29 / 2017-12-27T12:00:00
        2018:
            1: 2018-01-05 / 2018-01-03T12:00:00
"""


@fixture(scope="session")
def import_scan():
    """ Scans all the onegov.* sources to make sure that the tables are
    created.

    Include this fixtures as first argument if needed (that is if you run a
    single test and get sqlalchemy relation errors).

    """

    import importscan
    import onegov
    importscan.scan(onegov, ignore=['.test', '.tests'])


@fixture(scope='session')
def gazette_password():
    return hash_password('hunter2')


def create_gazette(request):
    app = create_app(GazetteApp, request, use_smtp=True)
    app.session_manager.set_locale('de_CH', 'de_CH')
    app.filestorage.settext('principal.yml', dedent(PRINCIPAL))

    group_id = uuid4()
    app.session().add(UserGroup(name='TestGroup', id=group_id))

    app.session().add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='admin'
    ))
    app.session().add(User(
        realname='Publisher',
        username='publisher@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='editor'
    ))
    app.session().add(User(
        realname='First Editor',
        username='editor1@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='member',
        group_id=group_id
    ))
    app.session().add(User(
        realname='Second Editor',
        username='editor2@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='member',
        group_id=group_id
    ))
    app.session().add(User(
        realname='Third Editor',
        username='editor3@example.org',
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


@fixture(scope="function")
def principal(request):
    yield Principal.from_yaml(dedent(PRINCIPAL))
