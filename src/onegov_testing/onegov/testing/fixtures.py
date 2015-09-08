import os
import port_for
import pytest
import shutil
import subprocess
import tempfile
import transaction

from elasticsearch import Elasticsearch
from mirakuru import HTTPExecutor
from onegov.core.orm import Base, SessionManager
from sqlalchemy import create_engine
from testing.postgresql import Postgresql
from uuid import uuid4


@pytest.yield_fixture(scope="session")
def postgres():
    """ Starts a postgres server using `testing.postgresql \
    <https://pypi.python.org/pypi/testing.postgresql/>`_ once per test session.

    """

    postgres = Postgresql()
    yield postgres
    postgres.stop()


@pytest.yield_fixture(scope="function")
def postgres_dsn(postgres):
    """ Returns a dsn to a temporary postgres server. Cleans up the database
    after running the tests.

    """
    yield postgres.url()

    transaction.abort()

    manager = SessionManager(postgres.url(), None)
    manager.session().close_all()
    manager.dispose()

    engine = create_engine(postgres.url())
    results = engine.execute(
        "SELECT DISTINCT table_schema FROM information_schema.tables")

    schemas = set(r['table_schema'] for r in results)

    for schema in schemas:
        if schema.startswith('pg_'):
            continue

        if schema in ('information_schema', 'public'):
            continue

        # having a bad day because your test doesn't work if run with others?
        # did you use a session manager? if yes, make sure to use mgr.dispose()
        # before finishing your test, or use the sesion_manager fixture!
        engine.execute('DROP SCHEMA "{}" CASCADE'.format(schema))

    engine.raw_connection().invalidate()
    engine.dispose()


@pytest.yield_fixture(scope="function")
def session_manager(postgres_dsn):
    """ Provides a :class:`onegov.core.orm.session_manager.SessionManager`
    setup with :func:`postgres_dsn`.

    """

    mgr = SessionManager(postgres_dsn, Base)
    yield mgr
    mgr.dispose()


@pytest.yield_fixture(scope="function")
def session(session_manager):
    """ Provides an SQLAlchemy session, scoped to a random schema.

    This is the fixture you usually want to use for ORM tests.

    """
    session_manager.set_current_schema('test_' + uuid4().hex)
    yield session_manager.session()


@pytest.yield_fixture(scope="function")
def temporary_directory():
    """ Provides a temporary directory that is removed after the test. """
    directory = tempfile.mkdtemp()
    yield directory
    shutil.rmtree(directory)


@pytest.yield_fixture(scope="session")
def es_process():
    binary = subprocess.check_output(['which', 'elasticsearch'])
    binary = binary.decode('utf-8').rstrip('\n')

    port = port_for.select_random()
    cluster_name = 'es_cluster_{}'.format(port)

    base = tempfile.mkdtemp()
    home = os.path.join(base, 'home')
    logs = os.path.join(base, 'logs')
    work = os.path.join(base, 'work')
    conf = os.path.join(base, 'conf')
    pid = os.path.join(base, 'cluster.pid')

    for path in (home, logs, work, conf):
        os.mkdir(path)

    # this logging config is required to successfully launch elasticsearch
    with open(os.path.join(conf, 'logging.yml'), 'w') as f:
        f.write("""
            es.logger.level: ERROR
            rootLogger: ERROR, console

            appender:
                console:
                    type: console
                    layout:
                        type: consolePattern
                        conversionPattern: "[%d{ISO8601}][%-5p][%-25c] %m%n"
        """)

    command = """
        {binary} -p {pidfile}
        --http.port={port}
        --path.home={home}
        --default.path.logs={logs}
        --default.path.work={work}
        --default.path.conf={conf}
        --cluster.name={cluster_name}
        --network.publish_host='127.0.0.1'
        --discovery.zen.ping.multicast.enabled=false
        --index.store.type=memory
    """.format(
        binary=binary,
        pidfile=pid,
        port=port,
        home=home,
        logs=logs,
        work=work,
        conf=conf,
        cluster_name=cluster_name,
    )

    url = 'http://127.0.0.1:{}'.format(port)
    executor = HTTPExecutor(command, url)
    executor.start()

    yield executor

    executor.stop()
    shutil.rmtree(base)


@pytest.yield_fixture(scope="function")
def es_url(es_process):
    """ Provides an url to an elasticsearch cluster that is guaranteed to be
    empty at the beginning of each test.

    """

    url = es_process.url.geturl()
    yield url

    es = Elasticsearch(url)
    es.indices.delete(index='*')


@pytest.yield_fixture(scope="function")
def es_client(es_url):
    """ Provides an elasticsearch client. """
    yield Elasticsearch(es_url)
