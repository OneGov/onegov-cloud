import pytest

from testing.postgresql import Postgresql
from onegov.core.orm import Base, SessionManager
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
