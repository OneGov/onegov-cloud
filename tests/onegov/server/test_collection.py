import pytest

from onegov.server import errors
from onegov.server.application import Application
from onegov.server.collection import ApplicationCollection, CachedApplication


def test_cached_application():
    cached = CachedApplication(Application, 'ns')
    assert cached.get() is cached.get()


def test_collection():

    class MyApplication(Application):

        def configure_application(self, foo):
            self.foo = foo

    collection = ApplicationCollection()
    collection.register('foo', MyApplication, 'test', {'foo': 'bar'})

    assert collection.get('foo') is collection.get('foo')
    assert collection.get('foo').foo == 'bar'


def test_collection_conflict():
    collection = ApplicationCollection()
    collection.register('foo', Application, 'ns1')

    with pytest.raises(errors.ApplicationConflictError):
        collection.register('foo', Application, 'ns2')


def test_morepath_applications():

    from morepath.app import App as MorepathApplication

    class MorepathApp(Application, MorepathApplication):
        pass

    class WsgiApp(Application):
        pass

    collection = ApplicationCollection()
    collection.register('foo', WsgiApp, 'foo')

    assert len(list(collection.morepath_applications())) == 0

    collection = ApplicationCollection()
    collection.register('foo', MorepathApp, 'bar')

    assert len(list(collection.morepath_applications())) == 1
