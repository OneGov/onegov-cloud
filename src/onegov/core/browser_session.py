from __future__ import annotations

from contextlib import suppress
from dogpile.cache.api import NO_VALUE
from hashlib import blake2b


from typing import overload, Any, TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Never

    from .cache import RedisCacheRegion

    OnDirtyCallback = Callable[['BrowserSession', str], None]

_T = TypeVar('_T')


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

    def count(self) -> int:
        # note, this cannot be used in a Redis cluster - if we use that
        # we have to keep track of all keys separately
        return self.cache.backend.reader_client.eval("""
            return #redis.pcall('keys', ARGV[1])
        """, 0, f'{self.cache.namespace}:{self.prefix}:*')

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

        self._is_dirty = False
        self._on_dirty = on_dirty

    def has(self, name: str) -> bool:
        return self._cache.get(name) is not NO_VALUE

    def flush(self) -> None:
        self._cache.flush()
        self.mark_as_dirty()

    def count(self) -> int:
        return self._cache.count()

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
            self._on_dirty(self, self._token)
            self._is_dirty = True

    @overload
    def get(self, name: str) -> Any | None: ...

    @overload
    def get(self, name: str, default: _T) -> Any | _T: ...

    def get(self, name: str, default: Any = None) -> Any:
        result = self._cache.get(name)

        if result is NO_VALUE:
            return default

        return result

    # FIXME: What is *args for, why do we allow this? For now we set
    #        it to Never, so we get a mypy error, if there is any code
    #        that uses this, if no code uses it then get rid of it!
    def __getitem__(self, name: str, *args: Never) -> Any:
        result = self._cache.get(name)

        if result is NO_VALUE:
            raise KeyError

        return result

    def __getattr__(self, name: str) -> Any:
        result = self._cache.get(name)

        if result is NO_VALUE:
            raise AttributeError

        return result

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith('_'):
            return super().__setattr__(name, value)

        self._cache.set(name, value)
        self.mark_as_dirty()

    def __delattr__(self, name: str) -> None:
        if name.startswith('_'):
            return super().__delattr__(name)

        self._cache.delete(name)
        self.mark_as_dirty()

    __setitem__ = __setattr__
    __delitem__ = __delattr__
    __delattr__ = __delattr__
    __contains__ = has
