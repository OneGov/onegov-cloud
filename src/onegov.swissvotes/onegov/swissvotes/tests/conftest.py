from onegov_testing.utils import create_app
from onegov.core.crypto import hash_password
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.models import Principal
from onegov.user import User
from pytest import fixture
from transaction import commit


def pytest_addoption(parser):
    """ Adds a command line argument to scans all the onegov.* sources to
    make sure that the database tables are created.

    Set this option if you run into  sqlalchemy erorrs like:
        "relation XXX does not exist"

    Run it like this:
        py.test src/onegov.swissvotes/onegov/swissvotes/tests/
            -k test_xxx
            --import-scan

    """
    parser.addoption('--import-scan', action="store_true")


def pytest_cmdline_main(config):
    option = config.getoption('--import-scan')
    if option:
        import importscan
        import onegov
        importscan.scan(onegov, ignore=['.test', '.tests'])


def create_swissvotes_app(request, temporary_path):
    app = create_app(
        SwissvotesApp,
        request,
        use_smtp=True,
        depot_backend='depot.io.local.LocalFileStorage',
        depot_storage_path=str(temporary_path),
    )
    app.session_manager.set_locale('de_CH', 'de_CH')

    session = app.session()
    session.add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('swissvotes_password'),
        role='admin'
    ))
    session.add(User(
        realname='Publisher',
        username='publisher@example.org',
        password_hash=request.getfixturevalue('swissvotes_password'),
        role='editor'
    ))
    session.add(User(
        realname='Editor',
        username='editor@example.org',
        password_hash=request.getfixturevalue('swissvotes_password'),
        role='member'
    ))

    commit()
    return app


@fixture(scope='session')
def swissvotes_password():
    return hash_password('hunter2')


@fixture(scope="function")
def principal():
    yield Principal()


@fixture(scope="function")
def swissvotes_app(request, temporary_path):
    app = create_swissvotes_app(request, temporary_path)
    yield app
    app.session_manager.dispose()
