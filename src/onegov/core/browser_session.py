from __future__ import annotations

import transaction

from contextlib import suppress
from dogpile.cache.api import NO_VALUE
from hashlib import blake2b


from typing import overload, Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from transaction.interfaces import ITransaction

    from .cache import RedisCacheRegion

    type OnDirtyCallback = Callable[[BrowserSession, str], None]


class Prefixed:

    def __init__(self, prefix: str, cache: RedisCacheRegion):
        assert len(prefix) >= 24

        self.prefix = prefix
        self.cache = cache

    def mangle(self, key: str) -> str:
        assert key
        return f'{self.prefix}:{key}'

    def get(self, key: str) -> Any:
        return self.cache.get(self.mangle(key))

    def set(self, key: str, value: Any) -> None:
        self.cache.set(self.mangle(key), value)

    def delete(self, key: str) -> None:
        self.cache.delete(self.mangle(key))

    def flush(self) -> int:
        # note, this cannot be used in a Redis cluster - if we use that
        # we have to keep track of all keys separately
        return self.cache.backend.reader_client.eval("""
            if #redis.pcall('keys', ARGV[1]) > 0 then
                return redis.pcall('del', unpack(redis.call('keys', ARGV[1])))
            end
            return 0
        """, 0, f'{self.cache.namespace}:{self.prefix}:*')


class BrowserSession:
    """ A session bound to a token (session_id cookie). Used to store data
    about a client on the server.

    Instances should be called ``browser_session`` to make sure we don't
    confuse this with the orm sessions.

    Used by :class:`onegov.core.request.CoreRequest`.

    Example::

        browser_session = request.browser_session
        browser_session.name = 'Foo'
        assert client.session.name == 'Foo'
        del client.session.name

    This class can act like an object, through attribute access, or like a
    dict, through square brackets. Whatever you prefer.

    This class also acts as a data manager for ``transaction``, so changes
    are not committed to Redis, until the transaction is commited.

    The ``on_dirty`` callback gets invoked when the first change to the
    session happens, even if it ends up getting rolled back, so use with
    care!

    """

    def __init__(
        self,
        cache: RedisCacheRegion,
        token: str,
        on_dirty: OnDirtyCallback = lambda session, token: None
    ):

        # make it impossible to get the session token through key listing
        prefix = blake2b(token.encode('utf-8'), digest_size=24).hexdigest()
        self._cache = Prefixed(prefix=prefix, cache=cache)
        self._token = token

        # NOTE: Since these take priority over the Redis cache, it's possible
        #       for conflicting changes that happen during our transaction on
        #       a different transaction to be lost, which may result in a mix
        #       of fresh attributes and stale attributes, if we're actually
        #       worried about this, we could check the timestamp of the cached
        #       values against the timestamps when we recorded our overrides
        #       and emit a retryable error, if we detect another transactions'
        #       changes interleaving with ours. Even our best attempt could
        #       still have data races though, unless we depend on Redis
        #       pipelines, which would probably mean having to write a new
        #       `dogpile.cache` backend. It's probably not worth changing,
        #       especially since we've had the same problems before we changed
        #       this into a data manager.
        self._pending_overrides: dict[str, Any] = {}
        self._pending_deletes: set[str] = set()
        self._pending_flush = False

        self._is_dirty = False
        self._on_dirty = on_dirty

    def _get(self, name: str) -> Any:
        value = self._pending_overrides.get(name, NO_VALUE)
        if (
            # value has been overridden
            value is not NO_VALUE
            # ... or deleted
            or self._pending_flush
            or name in self._pending_deletes
        ):
            # ... so we can completely ignore what's inside _cache
            return value
        return self._cache.get(name)

    def set(self, name: str, value: Any) -> None:
        self._pending_overrides[name] = value
        self._pending_deletes.discard(name)
        self.mark_as_dirty()

    def delete(self, name: str) -> None:
        self._pending_deletes.add(name)
        self._pending_overrides.pop(name, None)
        self.mark_as_dirty()

    def has(self, name: str) -> bool:
        return self._get(name) is not NO_VALUE

    def flush(self) -> None:
        self._pending_flush = True
        self._pending_overrides.clear()
        self._pending_deletes.clear()
        self.mark_as_dirty()

    def pop(self, name: str, default: Any = None) -> Any:
        """ Returns the value for the given name, removing the value in
        the process.

        """
        value = self.get(name, default=default)

        # we can run into a race condition here when two requests come in
        # simultaneously - one request will get the value and delete it, the
        # other will get the value and fail with an error when trying to
        # delete it
        #
        # we can be pragmatic - if it's gone, it doesn't need to be deleted
        with suppress(AttributeError):
            delattr(self, name)

        return value

    def mark_as_dirty(self) -> None:
        if not self._is_dirty:
            # NOTE: We only need to join the transaction once we actually
            #       intend to write anything.
            transaction.get().join(self)
            self._is_dirty = True
            # FIXME: We would like to defer calling this until the transaction
            #        has been committed, but since we use this to add headers
            #        to the response via `request.after`, we cannot do that
            #        since those callbacks are invoked on the inner-most layer
            #        so the transaction commit happens after the callbacks run
            self._on_dirty(self, self._token)

    @overload
    def get(self, name: str) -> Any | None: ...

    @overload
    def get[T](self, name: str, default: T) -> Any | T: ...

    def get(self, name: str, default: Any = None) -> Any:
        result = self._get(name)

        if result is NO_VALUE:
            return default

        return result

    def __getitem__(self, name: str) -> Any:
        result = self._get(name)

        if result is NO_VALUE:
            raise KeyError(name)

        return result

    def __getattr__(self, name: str) -> Any:
        result = self._get(name)

        if result is NO_VALUE:
            raise AttributeError(name)

        return result

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_'):
            return super().__setattr__(name, value)

        self.set(name, value)

    def __delattr__(self, name: str) -> None:
        if name.startswith('_'):
            return super().__delattr__(name)

        self.delete(name)

    __setitem__ = __setattr__
    __delitem__ = __delattr__
    __delattr__ = __delattr__
    __contains__ = has

    # DataManager interface
    def sortKey(self) -> str:
        return 'browser_session'

    def commit(self, transaction: ITransaction) -> None:
        pass

    def abort(self, transaction: ITransaction) -> None:
        if self._is_dirty:
            self._finish()

    def _finish(self) -> None:
        self._pending_overrides = {}
        self._pending_flush = False
        self._pending_deletes = set()
        self._pending_transaction = False
        self._is_dirty = False

    def tpc_begin(self, transaction: ITransaction) -> None:
        pass

    def tpc_vote(self, transaction: ITransaction) -> None:
        pass

    def tpc_abort(self, transaction: ITransaction) -> None:
        if self._is_dirty:
            self._finish()

    def tpc_finish(self, transaction: ITransaction) -> None:
        if not self._is_dirty:
            return

        if self._pending_flush:
            self._cache.flush()
        elif self._pending_deletes:
            for key in self._pending_deletes:
                self._cache.delete(key)
        for name, value in self._pending_overrides.items():
            self._cache.set(name, value)
        self._finish()

    def savepoint(self) -> BrowserSessionSavepoint:
        return BrowserSessionSavepoint(self)


class BrowserSessionSavepoint:
    def __init__(self, browser_session: BrowserSession) -> None:
        self.browser_session = browser_session
        self.original_state = (
            browser_session._pending_overrides.copy(),
            browser_session._pending_deletes.copy(),
            browser_session._pending_flush,
            browser_session._is_dirty
        )

    def rollback(self) -> None:
        (
            self.browser_session._pending_overrides,
            self.browser_session._pending_deletes,
            self.browser_session._pending_flush,
            self.browser_session._is_dirty
        ) = self.original_state
