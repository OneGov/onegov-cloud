import os
import port_for
import pytest
import shlex
import shutil
import socket
import subprocess
import tempfile
import transaction
import urllib3

from _pytest.monkeypatch import MonkeyPatch
from fs.tempfs import TempFS
from functools import lru_cache
from mirakuru import HTTPExecutor as HTTPExecutorBase
from mirakuru.compat import HTTPConnection, HTTPException
from onegov.core.crypto import hash_password
from onegov.core.orm import Base, SessionManager
from onegov_testing.browser import ExtendedBrowser
from pathlib import Path
from selenium.webdriver.chrome.options import Options
from splinter import Browser
from sqlalchemy import create_engine
from onegov_testing.postgresql import Postgresql
from uuid import uuid4
from webdriver_manager.chrome import ChromeDriverManager

try:
    from elasticsearch import Elasticsearch
except ImportError:
    def Elasticsearch(*args, **kwargs):
        assert False, "Elasticsearch is not installed"


class HTTPExecutor(HTTPExecutorBase):

    # Ipmlements https://github.com/ClearcodeHQ/mirakuru/issues/181
    def __init__(self, *args, **kwargs):
        self.method = kwargs.pop('method', 'HEAD')
        super().__init__(*args, **kwargs)

    def after_start_check(self):
        """Check if defined URL returns expected status to a HEAD request."""
        try:
            conn = HTTPConnection(self.host, self.port)

            conn.request(self.method, self.url.path)
            status = str(conn.getresponse().status)

            if status == self.status or self.status_re.match(status):
                conn.close()
                return True

        except (HTTPException, socket.timeout, socket.error):
            return False

    def __del__(self):
        try:
            super().__del__()
        except Exception:
            pass


@pytest.fixture(scope='session')
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
    present on the server because onegov_testing is strictly a testing
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


@pytest.fixture(scope="session")
def postgres():
    """ Starts a postgres server using `testing.postgresql \
    <https://pypi.python.org/pypi/testing.postgresql/>`_ once per test session.

    """

    # XXX our tests do not properly release open postgres connections, but
    # I don't know yet where. The following configuration increases the
    # number of allowed connections substantially as a work around.
    postgres_args = ' '.join((
        "-h 127.0.0.1",
        "-F",
        "-c logging_collector=off",
        "-N 1024"
    ))

    postgres = Postgresql(postgres_args=postgres_args)
    yield postgres
    postgres.stop()


@pytest.fixture(scope="function")
def postgres_dsn(postgres):
    """ Returns a dsn to a temporary postgres server. Cleans up the database
    after running the tests.

    """
    postgres.reset_snapshots()

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


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
def session(session_manager):
    """ Provides an SQLAlchemy session, scoped to a random schema.

    This is the fixture you usually want to use for ORM tests.

    """
    session_manager.set_current_schema('test_' + uuid4().hex)
    session_manager.set_locale('de_CH', 'de_CH')

    yield session_manager.session()


@pytest.fixture(scope="function")
def temporary_directory():
    """ Provides a temporary directory that is removed after the test. """
    directory = tempfile.mkdtemp()
    yield directory
    shutil.rmtree(directory)


@pytest.fixture(scope="function")
def temporary_path(temporary_directory):
    """ Same as :func:`temporary_directory`, but providing a ``Path`` instead
    of a string. """

    yield Path(temporary_directory)


@pytest.fixture(scope="session")
def es_default_version():
    return '5.5.1'


@pytest.fixture(scope="session")
def es_version(es_default_version):
    return os.environ.get('ES_VERSION', es_default_version)


@pytest.fixture(scope="session")
def es_archive(es_version):
    archive = '/tmp/elasticsearch-{}.tar.gz'.format(es_version)

    if not os.path.exists(archive):
        if es_version.startswith('5'):
            url = """
                https://artifacts.elastic.co/
                downloads/elasticsearch/elasticsearch-{}.tar.gz
            """
        else:
            url = """
                https://download.elastic.co/
                elasticsearch/elasticsearch/elasticsearch-{}.tar.gz
            """

        url = url.format(es_version).replace(' ', '').replace('\n', '')

        http = urllib3.PoolManager()

        with http.request('GET', url, preload_content=False) as r:
            with open(archive, 'wb') as f:
                shutil.copyfileobj(r, f)

    return archive


@pytest.fixture(scope="session")
def es_binary(es_archive):
    path = tempfile.mkdtemp()

    try:
        process = subprocess.Popen(
            shlex.split("tar xzvf {} --strip-components=1".format(es_archive)),
            cwd=path,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        assert process.wait() == 0
        yield os.path.join(path, 'bin/elasticsearch')
    finally:
        shutil.rmtree(path)


@pytest.fixture(scope="session")
def es_process(es_binary, es_version):
    port = port_for.select_random()
    pid = es_binary + '.pid'

    command = "{binary} -p {pidfile} --http.port={port}"

    if es_version.startswith('5'):
        command = command.replace('--', '-E')

    command = command.format(binary=es_binary, pidfile=pid, port=port)

    url = 'http://127.0.0.1:{}/_cluster/health?wait_for_status=green'
    url = url.format(port)

    executor = HTTPExecutor(command, url, method='GET')
    executor.start()

    yield executor

    executor.stop()
    executor.kill()


@pytest.fixture(scope="function")
def es_url(es_process):
    """ Provides an url to an elasticsearch cluster that is guaranteed to be
    empty at the beginning of each test.

    """

    url = es_process.url.geturl()
    url = url.split('/_cluster')[0]

    yield url

    es = Elasticsearch(url)
    es.indices.delete(index='*')


@pytest.fixture(scope="function")
def es_client(es_url):
    """ Provides an elasticsearch client. """
    yield Elasticsearch(es_url)


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="function")
def smtp(smtp_server):
    yield smtp_server
    del smtp_server.outbox[:]


@pytest.fixture(scope="session")
def test_password():
    return hash_password('hunter2')


@pytest.fixture(scope="session")
def long_lived_filestorage():
    return TempFS()


@pytest.fixture(scope="session")
def webdriver():
    return 'chrome'


@pytest.fixture(scope="session")
def webdriver_options():
    options = Options()

    if os.environ.get('SHOW_BROWSER') != '1':
        options.add_argument('--headless')

    return options


@pytest.fixture(scope="session")
def webdriver_executable_path():
    return ChromeDriverManager().install()


@pytest.fixture(scope="session")
def browser_extension():
    return ExtendedBrowser


@pytest.fixture(scope="function")
def browser(webdriver, webdriver_options, webdriver_executable_path,
            browser_extension):

    config = {
        'executable_path': webdriver_executable_path,
        'options': webdriver_options,

        # preselect a port as selenium picks it in a way that triggers the
        # macos firewall to display a confirmation dialog
        'port': port_for.select_random()
    }

    with browser_extension.spawn(Browser, webdriver, **config) as browser:
        yield browser
