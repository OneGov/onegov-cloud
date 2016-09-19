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
eventually be discarded by memcache if the cache is full).

"""

import dill
import memcache

from dogpile.cache import make_region, register_backend
from dogpile.cache.backends.memcached import MemcachedBackend as BaseBackend
from dogpile.cache.api import NO_VALUE
from dogpile.cache.proxy import ProxyBackend
from hashlib import sha1
from onegov.core import log


class MemcachedBackend(BaseBackend):
    """ A custom memcached backend with the following improvements:

    * Uses dill instead of pickle, allowing for a wider range of cached objs.

    """

    def _create_client(self):
        return memcache.Client(
            self.url,
            pickler=DillPickler,
            unpickler=DillPickler
        )


register_backend(
    'onegov.core.memcached',
    'onegov.core.cache',
    'MemcachedBackend'
)

dill.settings['recurse'] = True


class DillPickler(object):
    """ A python-memcached pickler that uses dill instead of the builtin
    pickle module.

    Dill is an alternative implementation that supports a wider variety
    of objects which it can pickle.

    """

    def __init__(self, file, protocol=None):
        self.file = file

    def dump(self, value):
        return dill.dump(value, self.file)

    def load(self):
        return dill.load(self.file)


def prefix_key_mangler(prefix):

    prefix = prefix.encode('utf-8')

    def key_mangler(key):
        return sha1(prefix + key.encode('utf-8')).hexdigest()

    return key_mangler


def create_backend(namespace, backend, arguments={}, expiration_time=None):

    prefix = '{}:'.format(namespace)

    return make_region(key_mangler=prefix_key_mangler(prefix)).configure(
        backend,
        expiration_time=expiration_time,
        arguments=arguments,
        wrap=[IgnoreUnreachableBackend]
    )


class IgnoreUnreachableBackend(ProxyBackend):
    """ A proxy backend that logs an error when memcached is down, but keeps
    running, albeit without using any caching.

    The idea is that a memcached outage will result in a slower/degraded
    user experience, not in complete breakage.

    """

    def get(self, key):
        try:
            return self.proxied.get(key)
        except TypeError:
            log.exception("Error reading from memcached")
            return NO_VALUE

    def set(self, key, value):
        try:
            self.proxied.set(key, value)
        except TypeError:
            log.exception("Error writing to memcached")

    def delete(self, key):
        try:
            self.proxied.delete(key)
        except TypeError:
            log.exception("Error deleting from memcached")

    def get_multi(self, keys):
        try:
            return self.proxied.get_multi(keys)
        except TypeError:
            log.exception("Error reading from memcached")
            return [NO_VALUE] * len(keys)

    def set_multi(self, mapping):
        try:
            self.proxied.set_multi(mapping)
        except TypeError:
            log.exception("Error writing to memcached")

    def delete_multi(self, keys):
        try:
            self.proxied.delete_multi(keys)
        except TypeError:
            log.exception("Error deleting from memcached")
