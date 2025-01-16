""" Provides caching methods for onegov.core.

Onegov.core uses dogpile for caching:
`<https://dogpilecache.readthedocs.org/>`_

Unlike dogpile onegov.core does not provide a global region however.
The cache is available through the app::

    request.app.cache.set('key', 'value')

Global caches in a multi-tennant application are a security vulnerability
waiting to be discovered. Therefore we do not do that!

This means that this won't be available::

    from x import cache
    @cache.cache_on_arguments()
    def my_function():
        return 'foobar'

Syntactic sugar like this will be provided through decorators inside this
module in the future. For example, we could write one that is usable
on all morepath views::

    @App.view(...)
    @cache.view()
    def my_view():
        return '<html>...'

But no such method exists yet.

Currently there is one cache per app that never expires (though values will
eventually be discarded by redis if the cache is full).

"""
from __future__ import annotations

import dill  # type:ignore[import-untyped]

from dogpile.cache import CacheRegion
from dogpile.cache.api import NO_VALUE
from functools import cached_property
from functools import lru_cache
from functools import partial
from functools import update_wrapper
from redis import ConnectionPool


from typing import overload, Any, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from dogpile.cache.api import NoValue

    _F = TypeVar('_F', bound=Callable[..., Any])


@overload
def instance_lru_cache(*, maxsize: int | None = ...) -> Callable[[_F], _F]:
    ...


@overload
def instance_lru_cache(method: _F, *, maxsize: int | None = ...) -> _F: ...


def instance_lru_cache(
    method: _F | None = None,
    *,
    maxsize: int | None = 128
) -> _F | Callable[[_F], _F]:
    """ Least-recently-used cache decorator for class methods.

    The cache follows the lifetime of an object (it is stored on the object,
    not on the class) and can be used on unhashable objects.

    This is a wrapper around functools.lru_cache which prevents memory leaks
    when using LRU cache within classes.

    https://stackoverflow.com/a/71663059

    """

    def decorator(wrapped: _F) -> _F:
        def wrapper(self: Any) -> Any:
            return lru_cache(maxsize=maxsize)(
                update_wrapper(partial(wrapped, self), wrapped)
            )

        # NOTE: we are doing some oddball stuff here that the type
        #       checker will have trouble to understand, so we just
        #       pretend we returned a regular decorator, rather than
        #       a cached_property that contains a decorator
        return cached_property(wrapper)  # type:ignore[return-value]

    return decorator if method is None else decorator(method)


def dill_serialize(value: Any) -> bytes:
    if isinstance(value, bytes):
        return value
    return dill.dumps(value, recurse=True)


def dill_deserialize(value: bytes | NoValue) -> Any:
    if value is NO_VALUE:
        return value
    return dill.loads(value)  # nosec:B301


class RedisCacheRegion(CacheRegion):
    """ A slightly more specific CacheRegion that will be configured
    to a single non-clustered Redis backend with name-mangling based
    on a given namespace as well as a couple of additional convenience
    methods specific to Redis.

    It will use dill to serialize/deserialize values.
    """
    def __init__(
        self,
        namespace: str,
        expiration_time: float,
        redis_url: str,
    ):
        super().__init__(
            # FIXME: OGC-1893
            serializer=dill_serialize,
            deserializer=dill_deserialize
        )
        self.namespace = namespace
        self.configure(
            'dogpile.cache.redis',
            arguments={
                'url': redis_url,
                'redis_expiration_time': expiration_time + 1,
                'connection_pool': get_pool(redis_url)
            }
        )
        # remove instance level key_mangler
        if 'key_mangler' in self.__dict__:
            del self.__dict__['key_mangler']

    def key_mangler(self, key: str) -> bytes:  # type:ignore[override]
        return f'{self.namespace}:{key}'.encode('utf-8')

    def keys(self) -> list[str]:
        # note, this cannot be used in a Redis cluster - if we use that
        # we have to keep track of all keys separately
        return self.backend.reader_client.eval(
            "return redis.pcall('keys', ARGV[1])", 0, f'{self.namespace}:*'
        )

    def flush(self) -> int:
        # note, this cannot be used in a Redis cluster - if we use that
        # we have to keep track of all keys separately
        return self.backend.reader_client.eval("""
            local keys = redis.call('keys', ARGV[1])
            for i=1,#keys,5000 do
                redis.call('del', unpack(keys, i, math.min(i+4999, #keys)))
            end
            return #keys
        """, 0, f'{self.namespace}:*')


# TODO: Remove these deprecated aliases
keys = RedisCacheRegion.keys
flush = RedisCacheRegion.flush


@lru_cache(maxsize=1024)
def get(
    namespace: str,
    expiration_time: float,
    redis_url: str
) -> RedisCacheRegion:
    return RedisCacheRegion(
        namespace=namespace,
        expiration_time=expiration_time,
        redis_url=redis_url
    )


@lru_cache(maxsize=16)
def get_pool(redis_url: str) -> ConnectionPool:
    return ConnectionPool.from_url(redis_url)
