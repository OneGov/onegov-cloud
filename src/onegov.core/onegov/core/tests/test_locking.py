import time

from onegov.core.errors import AlreadyLockedError
from onegov.core.locking import lock
from onegov.core.orm import SessionManager
from sqlalchemy.ext.declarative import declarative_base
from threading import Thread


class LockingThread(Thread):

    def __init__(self, mgr, namespace, key, schema):
        Thread.__init__(self)
        self.mgr = mgr
        self.namespace = namespace
        self.key = key
        self.schema = schema

    def run(self):
        self.mgr.set_current_schema(self.schema)

        try:
            with lock(self.mgr.session(), self.namespace, self.key):
                time.sleep(0.1)
        except Exception as e:
            self.exception = e
        else:
            self.exception = None


def test_locking_smoke(session):
    with lock(session, 'foo', 'bar'):
        pass


def test_threaded_locking(postgres_dsn):
    Base = declarative_base()

    session_manager = SessionManager(postgres_dsn, Base)
    session_manager.set_current_schema('foo')

    threads = [
        LockingThread(session_manager, 'namespace', 'key', 'foo'),
        LockingThread(session_manager, 'namespace', 'key', 'foo')
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    exceptions = [t.exception for t in threads if t.exception]

    assert len(exceptions) == 1
    assert isinstance(exceptions[0], AlreadyLockedError)


def test_multischema_threaded_locking(postgres_dsn):
    Base = declarative_base()

    session_manager = SessionManager(postgres_dsn, Base)
    session_manager.set_current_schema('foo')

    threads = [
        LockingThread(session_manager, 'namespace', 'key', 'foo'),
        LockingThread(session_manager, 'namespace', 'key', 'bar')
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    exceptions = [t.exception for t in threads if t.exception]

    assert len(exceptions) == 1
    assert isinstance(exceptions[0], AlreadyLockedError)
