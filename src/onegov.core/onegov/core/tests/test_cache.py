from chameleon import PageTemplate
from onegov.core import cache
from onegov.core.framework import Framework
from onegov.core.utils import Bunch
from webtest import TestApp as Client


CALL_COUNT = 0


# cannot be pickled by the builtin pickler
class Point(object):

    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y


def test_cache_connections():

    class IdentityPolicy(object):
        def identify(self, request):
            return None

        def remember(self, response, request, identity):
            pass

        def forget(self, response, request):
            pass

    class App(Framework):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    @App.html(model=Root)
    def view_root(self, request):
        @request.app.cache.cache_on_arguments()
        def call_count():
            global CALL_COUNT
            CALL_COUNT += 1
            return str(CALL_COUNT)

        return call_count()

    @App.identity_policy()
    def identity_policy():
        return IdentityPolicy()

    app = App()
    app.namespace = 'towns'
    app.configure_application(cache_connections=2, disable_memcached=True)

    client = Client(app)

    # with a limit of two connections we'll see that whenever a third
    # applicaiton is used, the last used application is lost
    #
    # we won't necessarily see this with memcached - memcached does it's own
    # lru and we don't try to influence that - here we lose the cache because
    # if we use a memory cache backend we lose the cache when discarding
    # the backend
    app.set_application_id('towns/washington')
    assert client.get('/').text == '1'
    assert client.get('/').text == '1'

    app.set_application_id('towns/arlington')
    assert client.get('/').text == '2'
    assert client.get('/').text == '2'

    app.set_application_id('towns/washington')
    assert client.get('/').text == '1'

    app.set_application_id('towns/detroit')
    assert client.get('/').text == '3'

    app.set_application_id('towns/washington')
    assert client.get('/').text == '1'

    app.set_application_id('towns/detroit')
    assert client.get('/').text == '3'

    app.set_application_id('towns/arlington')
    assert client.get('/').text == '4'


def test_unreachable_backend_proxy():

    region = cache.create_backend('ns', 'onegov.core.memcached', arguments={
        'url': '127.0.0.1:12345'
    })

    region.delete('test')
    region.set('test', 'value')
    assert region.get('test') is cache.NO_VALUE

    region.delete_multi(['foo', 'bar'])
    region.set_multi({
        'foo': 1, 'bar': 2
    })
    assert region.get_multi(['foo', 'bar']) == [cache.NO_VALUE, cache.NO_VALUE]


def test_cache_key():
    region = cache.create_backend('ns', 'onegov.core.memcached', arguments={
        'url': '127.0.0.1:12345'
    })

    region.set('x' * 500, 'y')


def test_cache_page_template():
    region = cache.create_backend('ns', 'onegov.core.memcached', arguments={
        'url': '127.0.0.1:12345'
    })

    region.set('template', PageTemplate('<!DOCTYPE html>'))
    region.get('template')


def test_memcached(memcached_url):
    app = Framework()
    app.namespace = 'towns'
    app.set_application_id('towns/detroit')
    app.configure_application(memcached_url=memcached_url)
    app.cache.set('foobar', Bunch(foo='bar'))

    assert app.cache.get('foobar').foo == 'bar'


def test_store_slots_memory():
    # the following fails without the usage of an advanced pickler
    app = Framework()
    app.namespace = 'towns'
    app.set_application_id('towns/washington')

    app.configure_application(disable_memcached=True)
    app.cache.set('point', Point(0, 0))
    assert app.cache.get('point').x == 0
    assert app.cache.get('point').y == 0


def test_store_slots_memcached(memcached_url):
    # the following fails without the usage of an advanced pickler
    app = Framework()
    app.namespace = 'towns'
    app.set_application_id('towns/washington')

    app.configure_application(memcached_url=memcached_url)
    app.cache.set('point', Point(0, 0))
    assert app.cache.get('point').x == 0
    assert app.cache.get('point').y == 0
