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

import dill

from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from fastcache import clru_cache as lru_cache  # noqa
from redis import ConnectionPool
from types import MethodType


def dill_serialize(value):
    if isinstance(value, bytes):
        return value
    return dill.dumps(value, recurse=True)


def dill_deserialize(value):
    if value is NO_VALUE:
        return value
    return dill.loads(value)


def keys(cache):
    # note, this cannot be used in a Redis cluster - if we use that
    # we have to keep track of all keys separately
    prefix = cache.key_mangler('').decode()
    return cache.backend.reader_client.eval(
        "return redis.pcall('keys', ARGV[1])", 0, f'{prefix}*'
    )


def flush(cache):
    # note, this cannot be used in a Redis cluster - if we use that
    # we have to keep track of all keys separately
    prefix = cache.key_mangler('').decode()
    return cache.backend.reader_client.eval("""
        if #redis.pcall('keys', ARGV[1]) > 0 then
            return redis.pcall('del', unpack(redis.call('keys', ARGV[1])))
        end
    """, 0, f'{prefix}*')


@lru_cache(maxsize=1024)
def get(namespace, expiration_time, redis_url):

    def key_mangler(key):
        return f'{namespace}:{key}'.encode('utf-8')

    region_conf = dict(
        key_mangler=key_mangler,
        serializer=dill_serialize,
        deserializer=dill_deserialize
    )
    result = make_region(**region_conf).configure(
        'dogpile.cache.redis',
        arguments={
            'url': redis_url,
            'redis_expiration_time': expiration_time + 1,
            'connection_pool': get_pool(redis_url)
        }
    )
    result.flush = MethodType(flush, result)
    result.keys = MethodType(keys, result)
    return result


@lru_cache(maxsize=16)
def get_pool(redis_url):
    return ConnectionPool.from_url(redis_url)
