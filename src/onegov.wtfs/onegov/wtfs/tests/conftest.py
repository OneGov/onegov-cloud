from onegov_testing import Client as BaseClient
from onegov_testing.utils import create_app
from onegov.core.crypto import hash_password
from onegov.user import User
from onegov.user import UserGroup
from onegov.wtfs import WtfsApp
from onegov.wtfs.models import Principal
from pytest import fixture
from transaction import commit
from uuid import uuid4


class Client(BaseClient):
    use_intercooler = True

    def login_member(self, to=None):
        return self.login('member@example.org', 'hunter2', to)


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
    group_id = uuid4()
    session.add(UserGroup(id=group_id, name='My Group'))
    session.add(User(
        realname='Admin',
        username='admin@example.org',
        password_hash=request.getfixturevalue('wtfs_password'),
        role='admin'
    ))
    session.add(User(
        realname='Editor',
        username='editor@example.org',
        password_hash=request.getfixturevalue('wtfs_password'),
        role='editor',
        group_id=group_id
    ))
    session.add(User(
        realname='Member',
        username='member@example.org',
        password_hash=request.getfixturevalue('wtfs_password'),
        role='member',
        group_id=group_id
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


@fixture(scope='function')
def client(wtfs_app):
    return Client(wtfs_app)
