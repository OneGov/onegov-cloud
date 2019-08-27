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

from fastcache import clru_cache as lru_cache  # noqa
from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from dogpile.cache.proxy import ProxyBackend
from redis import ConnectionPool


@lru_cache(maxsize=1024)
def get(namespace, expiration_time, redis_url):

    def key_mangler(key):
        return f'{namespace}:{key}'.encode('utf-8')

    return make_region(key_mangler=key_mangler).configure(
        'dogpile.cache.redis',
        arguments={
            'url': redis_url,
            'redis_expiration_time': expiration_time + 1,
            'connection_pool': get_pool(redis_url)
        },
        wrap=(DillSerialized, )
    )


@lru_cache(maxsize=16)
def get_pool(redis_url):
    return ConnectionPool.from_url(redis_url)


class DillSerialized(ProxyBackend):
    """ A proxy backend that pickles all non-byte values using dill. """

    def serialize(self, value):
        if isinstance(value, bytes):
            return value

        return dill.dumps(value, recurse=True)

    def deserialize(self, value):
        if value is NO_VALUE:
            return value

        return dill.loads(value)

    def get(self, key):
        return self.deserialize(self.proxied.get(key))

    def set(self, key, value):
        return self.proxied.set(key, self.serialize(value))

    def get_multi(self, keys):
        return [self.deserialize(v) for v in self.proxied.get_multi(keys)]

    def set_multi(self, mapping):
        mapping = {k: self.serialize(v) for k, v in mapping.items()}
        self.proxied.set_multi(mapping)
