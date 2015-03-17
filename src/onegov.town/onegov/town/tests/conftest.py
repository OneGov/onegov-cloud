import more.webassets
import onegov.core
import onegov.town
import pytest
import transaction

from morepath import setup
from onegov.core.orm import Base, SessionManager
from onegov.town.initial_content import add_initial_content
from onegov.user import UserCollection
from testing.postgresql import Postgresql
from uuid import uuid4


@pytest.yield_fixture(scope="session")
def postgres_server_url():
    postgres = Postgresql()
    yield postgres.url()
    postgres.stop()


@pytest.yield_fixture(scope="session")
def session_manager(postgres_server_url):
    mgr = SessionManager(postgres_server_url, Base)

    yield mgr

    mgr.dispose()


@pytest.yield_fixture(scope="function")
def session(session_manager):
    session_manager.set_current_schema('test_' + uuid4().hex)
    yield session_manager.session()


@pytest.yield_fixture(scope="function")
def town_app(postgres_server_url):
    config = setup()
    config.scan(more.webassets)
    config.scan(onegov.core)
    config.scan(onegov.town)
    config.commit()

    app = onegov.town.TownApp()
    app.namespace = 'test_' + uuid4().hex
    app.configure_application(
        dsn=postgres_server_url,
        filestorage='fs.memoryfs.MemoryFS',
        identity_secure=False
    )
    app.set_application_id(app.namespace + '/' + 'test')

    add_initial_content(app.session(), 'Govikon')

    users = UserCollection(app.session())
    users.add('admin@example.org', 'hunter2', 'admin')

    transaction.commit()

    yield app
