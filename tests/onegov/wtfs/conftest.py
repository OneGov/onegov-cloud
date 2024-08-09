from tests.shared import Client as BaseClient
from tests.shared.utils import create_app
from onegov.core.crypto import hash_password
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.user import User
from onegov.wtfs import WtfsApp
from onegov.wtfs.models import Municipality
from onegov.wtfs.models import PaymentType
from onegov.wtfs.models import Principal
from pytest import fixture
from transaction import commit
from uuid import uuid4


class Client(BaseClient):
    use_intercooler = True

    def login_member(self, to=None):
        return self.login('member@example.org', 'hunter2', to)

    def login_optimo(self, to=None):
        return self.login('optimo@example.org', 'hunter2', to)


def create_wtfs_app(request, temporary_path):
    app = create_app(
        WtfsApp,
        request,
        use_maildir=True,
        depot_backend='depot.io.local.LocalFileStorage',
        depot_storage_path=str(temporary_path),
    )
    app.session_manager.set_locale('de_CH', 'de_CH')

    session = app.session()
    group_id = uuid4()
    session.add(PaymentType(name='normal', _price_per_quantity=700))
    session.add(PaymentType(name='spezial', _price_per_quantity=850))
    session.add(Municipality(
        id=group_id,
        name='My Municipality',
        bfs_number=1,
        payment_type='normal'
    ))
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
        group_id=group_id,
        data={'contact': True}
    ))
    session.add(User(
        realname='Member',
        username='member@example.org',
        password_hash=request.getfixturevalue('wtfs_password'),
        role='member',
        group_id=group_id
    ))
    session.add(User(
        realname='Optimo',
        username='optimo@example.org',
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


@fixture(scope='function')
def client(wtfs_app):
    return Client(wtfs_app)


@fixture(scope="session", autouse=True)
def enter_observer_scope():
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(WtfsApp)
