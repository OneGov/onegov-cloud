import pytest

from sqlalchemy import create_engine
from testing.postgresql import Postgresql


@pytest.yield_fixture(scope="function")
def dsn(postgres_server_url):
    yield postgres_server_url

    engine = create_engine(postgres_server_url)
    results = engine.execute(
        "SELECT DISTINCT table_schema FROM information_schema.tables")

    schemas = set(r['table_schema'] for r in results)

    for schema in schemas:
        if schema.startswith('pg_'):
            continue

        if schema in ('information_schema', 'public'):
            continue

        engine.execute('DROP SCHEMA "{}" CASCADE'.format(schema))

    engine.raw_connection().invalidate()
    engine.dispose()


@pytest.yield_fixture(scope="session")
def postgres_server_url():
    postgres = Postgresql()
    yield postgres.url()
    postgres.stop()
