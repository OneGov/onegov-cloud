import os
import port_for
import pytest
import shutil
import subprocess
import tempfile
import transaction

from _pytest.monkeypatch import MonkeyPatch
from elasticsearch import Elasticsearch
from functools import lru_cache
from mirakuru import HTTPExecutor as HTTPExecutorBase
from onegov.core.crypto import hash_password
from onegov.core.orm import Base, SessionManager
from pathlib import Path
from sqlalchemy import create_engine
from testing.postgresql import Postgresql
from uuid import uuid4


class HTTPExecutor(HTTPExecutorBase):

    def __del__(self):
        try:
            super().__del__()
        except:
            pass


@pytest.yield_fixture(scope='session')
def monkeysession(request):
    mp = MonkeyPatch()
    yield mp
    mp.undo()


@pytest.fixture(scope='session', autouse=True)
def treat_sqlalchemy_warnings_as_errors():
    """ All onegov models treat SQLAlchemy warnings as errors, because usually
    SQLAlchemy warnings are errors waiting to happen.

    """
    import warnings
    from sqlalchemy.exc import SAWarning
    warnings.simplefilter("error", SAWarning)


@pytest.fixture(scope='session', autouse=True)
def cache_password_hashing(monkeysession):
    """ Monkey-patch the password hashing/verification functions during tests
    for a big speed increase (we login with the same password over and over
    again).

    Changes to the auth are delicate, so we make sure this is only done during
    testing by having it here, instead of support some mechanism like this
    in onegov.core itself.

    So this dangerous code is not only inexistant in the core, it is also not
    present on the server because onegov.testing is strictly a testing
    dependency and finally it is only run when invoked through pytest.

    """

    from passlib.hash import bcrypt_sha256

    verify = bcrypt_sha256.verify
    encrypt = bcrypt_sha256.encrypt

    @lru_cache(maxsize=32)
    def cached_verify(password, hash):
        return verify(password, hash)

    @lru_cache(maxsize=32)
    def cached_encrypt(password):
        return encrypt(password)

    monkeysession.setattr(
        'onegov.core.crypto.password.bcrypt_sha256.encrypt', cached_encrypt)
    monkeysession.setattr(
        'onegov.core.crypto.password.bcrypt_sha256.verify', cached_verify)


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

    # in testing we often reuse loaded values after commiting a transaction,
    # so we set expire_on_commit to False. The test applications will still
    # use the default value of True however. This only affects unit tests
    # not working with the app.
    mgr = SessionManager(
        postgres_dsn, Base,
        session_config={
            'expire_on_commit': False
        },
        engine_config={
            'echo': 'ECHO' in os.environ
        }
    )
    yield mgr
    mgr.dispose()


@pytest.yield_fixture(scope="function")
def session(session_manager):
    """ Provides an SQLAlchemy session, scoped to a random schema.

    This is the fixture you usually want to use for ORM tests.

    """
    session_manager.set_current_schema('test_' + uuid4().hex)

    # TODO remove the 'hasattr' once the new onegov.core is out (0.9.0+)
    if hasattr(session_manager, 'set_locale'):
        session_manager.set_locale('de_CH', 'de_CH')

    yield session_manager.session()


@pytest.yield_fixture(scope="function")
def temporary_directory():
    """ Provides a temporary directory that is removed after the test. """
    directory = tempfile.mkdtemp()
    yield directory
    shutil.rmtree(directory)


@pytest.yield_fixture(scope="function")
def temporary_path(temporary_directory):
    """ Same as :func:`temporary_directory`, but providing a ``Path`` instead
    of a string. """

    yield Path(temporary_directory)


@pytest.yield_fixture(scope="session")
def es_process():
    binary = os.environ.get('ES_BINARY', None)

    if not binary:
        binary = subprocess.check_output(['which', 'elasticsearch'])
        binary = binary.decode('utf-8').rstrip('\n')

    assert Path(binary).exists()

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
        --action.auto_create_index=false
        --security.manager.enabled=false
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
    executor.kill()
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


@pytest.yield_fixture(scope="session")
def smtp_server():
    # replacement for smtpserver fixture, which also works on Python 3.5
    # see https://bitbucket.org/pytest-dev/pytest-localserver
    # /issues/13/broken-on-python-35
    from pytest_localserver import smtp

    class Server(smtp.Server):

        def getsockname(self):
            return self.socket.getsockname()

        @property
        def address(self):
            return self.addr[:2]

    server = Server()
    server.start()
    yield server
    server.stop()


@pytest.yield_fixture(scope="function")
def smtp(smtp_server):
    yield smtp_server
    del smtp_server.outbox[:]


@pytest.yield_fixture(scope="session")
def test_password():
    return hash_password('hunter2')
