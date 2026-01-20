from __future__ import annotations

from dogpile.cache import CacheRegion
from dogpile.cache.api import NO_VALUE
from functools import lru_cache
from onegov.core.custom import msgpack
from redis import ConnectionPool


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from dogpile.cache.api import NoValue


def msgpack_deserialize(value: bytes | NoValue) -> Any:
    if value is NO_VALUE:
        return value

    return msgpack.unpackb(value)


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
            serializer=msgpack.packb,
            deserializer=msgpack_deserialize
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

    def keys(self) -> list[bytes]:
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
