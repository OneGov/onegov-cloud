from chameleon import PageTemplate
from onegov.core import cache
from onegov.core.framework import Framework
from onegov.core.utils import Bunch


CALL_COUNT = 0


# cannot be pickled by the builtin pickler
class Point(object):

    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_cache_key(redis_url):
    region = cache.get(namespace='ns', expiration_time=60, redis_url=redis_url)
    region.set('x' * 500, 'y')  # used to fail on the old memcached system


def test_cache_page_template(redis_url):
    region = cache.get(namespace='ns', expiration_time=60, redis_url=redis_url)
    region.set('template', PageTemplate('<!DOCTYPE html>'))
    region.get('template')


def test_redis(redis_url):
    app = Framework()
    app.namespace = 'towns'
    app.set_application_id('towns/detroit')
    app.configure_application(redis_url=redis_url)
    app.cache.set('foobar', Bunch(foo='bar'))

    assert app.cache.get('foobar').foo == 'bar'


def test_store_slots_redis(redis_url):
    # the following fails without the usage of an advanced pickler
    app = Framework()
    app.namespace = 'towns'
    app.set_application_id('towns/washington')

    app.configure_application(redis_url=redis_url)
    app.cache.set('point', Point(0, 0))
    assert app.cache.get('point').x == 0
    assert app.cache.get('point').y == 0


def test_cache_independence(redis_url):
    app = Framework()
    app.namespace = 'towns'
    app.set_application_id('towns/washington')

    app.configure_application(redis_url=redis_url)
    app.cache.set('foo', 'bar')
    assert app.cache.get('foo')

    app.set_application_id('towns/newyork')
    assert not app.cache.get('foo')

    app.namespace = 'cities'
    app.set_application_id('cities/washington')
    assert not app.cache.get('foo')

    app.namespace = 'towns'
    app.set_application_id('towns/washington')
    assert app.cache.get('foo')
