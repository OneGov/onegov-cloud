from onegov_testing.utils import create_app
from onegov.core.crypto import hash_password
from onegov.wtfs import WtfsApp
from onegov.wtfs.models import Principal

from onegov.user import User
from pytest import fixture
from transaction import commit


def create_wtfs_app(request, temporary_path):
    app = create_app(
        WtfsApp,
        request,
        use_smtp=True,
        depot_backend='depot.io.local.LocalFileStorage',
        depot_storage_path=str(temporary_path),
    )
    app.add_initial_content()
    app.session_manager.set_locale('de_CH', 'de_CH')

    session = app.session()
    session.add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('wtfs_password'),
        role='admin'
    ))
    session.add(User(
        realname='Publisher',
        username='publisher@example.org',
        password_hash=request.getfixturevalue('wtfs_password'),
        role='editor'
    ))
    session.add(User(
        realname='Editor',
        username='editor@example.org',
        password_hash=request.getfixturevalue('wtfs_password'),
        role='member'
    ))

    commit()
    return app


@fixture(scope='session')
def wtfs_password():
    return hash_password('hunter2')


@fixture(scope="function")
def principal():
    yield Principal()


@fixture(scope="function")
def wtfs_app(request, temporary_path):
    app = create_wtfs_app(request, temporary_path)
    yield app
    app.session_manager.dispose()
