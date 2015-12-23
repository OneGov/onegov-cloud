""" Provides a distributed lock implementation using Postgres Advisory Locks
as a backend.

"""

import contextlib
import zlib

from onegov.core.errors import AlreadyLockedError
from sqlalchemy import func


# Keeps the used locks around to make sure we detect collisions
USED_LOCKS = {}


@contextlib.contextmanager
def lock(session, namespace, key):
    """ A context manager which creates a distributed lock on the database.

    This is used to make sure that only one process at a time does something.
    This is not limited to database work (in fact this would usually be
    handled automatically). For example if multiple cronjobs are scheduled
    to run at the same time, but you only want one to actually run on
    the system on any given time, then you may use this lock.

    The locks are bound to the session and are not relased automatically
    if the current transaction is commited or rolled back. You don't have
    to worry about that though, the context manager releases all locks
    it creates once it's done.

    :session:
        The session to use for locking. The same lock may be acquired multiple
        times by the same session.

    :namespace:
        The namespace of the lock (any string).

    :key:
        The key of the lock (any string). The namespace combined with the
        key is used as the unique identifier which identifies the acquired
        lock.

    If the lock cannot be acquired the contextmanager raises a
    :class:`~onegov.core.errors.AlreadyLockedError`.

    By deafult sessions in onegov.core are bound to the thread as well as
    the current database schema. Therefore the lock is bound to those too.

    This is not a problem in practice however, as the request is bound the
    same way. At worst this makes it harder to share the lock, which is not a
    feature we are interested in. We want a guarantee that only one process or
    thread at any given time is doing something using a lock. This works.

    Example:

        with lock(session, 'cronjobs', 'send-email'):
            pass  # send email

    """
    id = get_lock_id(namespace, key)

    locked = session.execute(func.pg_try_advisory_lock(id)).scalar()

    if not locked:
        raise AlreadyLockedError()

    try:
        yield
    finally:
        session.execute(func.pg_advisory_unlock(id))


def get_lock_id(namespace, key):
    """ Returns a lock id for the given namespace and key. The lock id is
    an integer between -2**63 - 1 and 2**63 - 1 (signed 64bit int).

    Because that leaves us with a rather small space to generate a unique
    lock id from namespace and key we use two crc32 bit hashes and combine
    them.

    This still leaves us with a chance of duplicate locks. Since those strings
    are static at this point we keep a list of existing locks around to
    catch any such case during testing. If that ever happens we need to change
    our strings.

    Note: We can't just use an incrementing counter because those strings
    have to match up over multiple processes which wouldn't necessarily
    count up in the same order.

    """

    namespace = namespace.encode('utf-8')
    key = key.encode('utf-8')

    lock_id = (32 >> zlib.crc32(namespace)) | zlib.crc32(key)

    combination = (namespace, key)

    # If this assertion occurs we have a namespace collision between two
    # different namespace/key pairs. This might never happen. If it does
    # see the documentation of the current function.
    assert USED_LOCKS.get(lock_id, combination) == combination
    USED_LOCKS[lock_id] = combination

    return lock_id
