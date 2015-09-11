import logging
import pytest

from datetime import datetime
from onegov.search import Searchable, utils
from onegov.search.indexer import (
    IndexManager,
    ORMEventTranslator,
    TypeMapping,
    TypeMappingRegistry
)


def test_index_manager_assertions(es_url):

    with pytest.raises(AssertionError):
        IndexManager(hostname='', es_url=es_url)

    with pytest.raises(AssertionError):
        IndexManager(hostname='example.org', es_url='')

    ixmgr = IndexManager(hostname='test.example.org', es_url=es_url)

    page = TypeMapping('page', {
        'properties': {
            'title': {'type': 'string'}
        }
    })

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='', language='de', mapping=page)

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='asdf', language='', mapping=page)

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='asdf', language='de', mapping='')

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='asdf', language='deu', mapping=page)

    with pytest.raises(AssertionError):
        ixmgr.ensure_index(schema='asdf', language='de', mapping='')


def test_index_manager_connection(es_url, es_client):
    ixmgr = IndexManager(hostname='foobar', es_client=es_client)
    assert ixmgr.es_client.ping()

    ixmgr = IndexManager(hostname='foobar', es_url=es_url)
    assert ixmgr.es_client.ping()


def test_index_manager_separation(es_url):
    foo = IndexManager(hostname='foo', es_url=es_url)
    bar = IndexManager(hostname='bar', es_url=es_url)

    page = TypeMapping('page', {
        'properties': {
            'title': {'type': 'string'}
        }
    })

    foo.ensure_index('foo', 'en', page)
    bar.ensure_index('bar', 'en', page)

    assert foo.query_indices() == {'foo-foo-en-page' + '-' + page.version}
    assert bar.query_indices() == {'bar-bar-en-page' + '-' + page.version}
    assert foo.query_aliases() == {'foo-foo-en-page'}
    assert bar.query_aliases() == {'bar-bar-en-page'}


def test_index_creation(es_url):
    ixmgr = IndexManager(hostname='example.org', es_url=es_url)

    page = TypeMapping('page', {
        'properties': {
            'title': {'type': 'string'}
        }
    })

    # create an index
    index = ixmgr.ensure_index(
        schema='foo_bar',
        language='en',
        mapping=page
    )
    assert index == 'example_org-foo_bar-en-page'
    assert ixmgr.created_indices == {index + '-' + page.version}
    assert ixmgr.query_indices() == ixmgr.created_indices
    assert ixmgr.query_aliases() == {index}

    # the slight change in the index name should be normalized away
    index = ixmgr.ensure_index(
        schema='foo-bar',
        language='en',
        mapping=page
    )
    assert index == 'example_org-foo_bar-en-page'
    assert ixmgr.created_indices == {index + '-' + page.version}
    assert ixmgr.query_indices() == ixmgr.created_indices
    assert ixmgr.query_aliases() == {index}

    # if we change a mapping (which we won't usually do at runtime), we
    # should get a new index
    new_page = TypeMapping('page', {
        'properties': {
            'title': {'type': 'string'},
            'body': {'type': 'string'}
        }
    })
    index = ixmgr.ensure_index(
        schema='foo-bar',
        language='en',
        mapping=new_page
    )
    assert index == 'example_org-foo_bar-en-page'
    assert ixmgr.created_indices == {
        index + '-' + page.version,
        index + '-' + new_page.version
    }
    assert ixmgr.query_indices() == ixmgr.created_indices
    assert ixmgr.query_aliases() == {index}

    # this leads to some indices no longer being used
    assert ixmgr.remove_expired_indices(current_mappings=[new_page]) == 1


def test_parse_index_name(es_url):
    ixmgr = IndexManager('foo', es_url)
    assert ixmgr.parse_index_name('hostname_org-my_schema-de-posts') == {
        'hostname': 'hostname_org',
        'schema': 'my_schema',
        'language': 'de',
        'type_name': 'posts',
        'version': None
    }

    assert ixmgr.parse_index_name('hostname_org-my_schema-de-posts-1') == {
        'hostname': 'hostname_org',
        'schema': 'my_schema',
        'language': 'de',
        'type_name': 'posts',
        'version': '1'
    }

    assert ixmgr.parse_index_name('asdf') == {
        'hostname': None,
        'schema': None,
        'language': None,
        'type_name': None,
        'version': None
    }


@pytest.mark.parametrize("is_valid", [
    utils.is_valid_index_name,
    utils.is_valid_type_name
])
def test_is_valid_name(is_valid):
    assert is_valid('asdf')
    assert is_valid('asdf.asdf')
    assert is_valid('asdf_asdf')
    assert is_valid('asdf-asdf')
    assert not is_valid('_asdf')
    assert not is_valid('.asdf')
    assert not is_valid('..asdf')
    assert not is_valid('\\')
    assert not is_valid('Abc')
    assert not is_valid('a:b')
    assert not is_valid('a/b')
    assert not is_valid('a*b')
    assert not is_valid('a?b')
    assert not is_valid('a"b')
    assert not is_valid('a<b')
    assert not is_valid('a>b')
    assert not is_valid('a|b')
    assert not is_valid('a b')
    assert not is_valid('a,b')


def test_mapping_for_language():

    mapping = TypeMapping('foo', {
        'title': {
            'type': 'localized'
        }
    })

    assert mapping.for_language('en') == {
        'title': {
            'type': 'string',
            'analyzer': 'english'
        },
        'public': {
            'type': 'boolean'
        }
    }

    mapping = TypeMapping('bar', {
        'title': {
            'properties': {
                'type': 'localized'
            }
        }
    })

    assert mapping.for_language('de') == {
        'title': {
            'properties': {
                'type': 'string',
                'analyzer': 'german'
            }
        },
        'public': {
            'type': 'boolean'
        }
    }


def test_orm_event_translator_properties():

    class Page(Searchable):

        es_type_name = 'page'
        es_properties = {
            'title': {'type': 'localized'},
            'body': {'type': 'localized'},
            'tags': {'type': 'string'},
            'date': {'type': 'date'},
            'published': {'type': 'boolean'},
            'likes': {'type': 'long'}
        }

        def __init__(self, id, **kwargs):
            self.id = id
            self.language = kwargs.pop('language', 'en')
            self.public = kwargs.pop('public', True)

            for k, v in kwargs.items():
                setattr(self, k, v)

        @property
        def es_id(self):
            return self.id

        @property
        def es_language(self):
            return self.language

        @property
        def es_public(self):
            return self.public

    translator = ORMEventTranslator()

    for on_event in (translator.on_insert, translator.on_update):
        on_event('my-schema', Page(
            id=1,
            title='About',
            body='We are Pied Piper',
            tags=['aboutus', 'company'],
            date=datetime(2015, 9, 11),
            published=True,
            likes=1000
        ))

        assert translator.queue.get() == {
            'action': 'index',
            'schema': 'my-schema',
            'type': 'page',
            'id': 1,
            'language': 'en',
            'public': True,
            'properties': {
                'title': 'About',
                'body': 'We are Pied Piper',
                'tags': ['aboutus', 'company'],
                'date': '2015-09-11T00:00:00',
                'likes': 1000,
                'published': True
            }
        }
        assert translator.queue.empty()


def test_orm_event_translator_delete():

    class Page(Searchable):

        es_id = 1
        es_type_name = 'page'

    translator = ORMEventTranslator()
    translator.on_delete('foobar', Page())

    assert translator.queue.get() == {
        'action': 'delete',
        'schema': 'foobar',
        'type': 'page',
        'id': 1
    }
    assert translator.queue.empty()


def test_orm_event_queue_overflow(caplog):

    caplog.setLevel(logging.ERROR, logger='onegov.search')

    class Tweet(Searchable):
        es_id = 1
        es_type_name = 'page'
        es_language = 'en'
        es_public = True
        es_properties = {}

    translator = ORMEventTranslator(max_queue_size=3)
    translator.on_insert('foobar', Tweet())
    translator.on_update('foobar', Tweet())
    translator.on_delete('foobar', Tweet())

    assert len(caplog.records()) == 0

    translator.on_insert('foobar', Tweet())

    assert len(caplog.records()) == 1
    assert caplog.records()[0].message == \
        'The orm event translator queue is full!'


def test_type_mapping_registry():

    registry = TypeMappingRegistry()
    registry.register_type('page', {
        'title': {'type': 'string'}
    })
    registry.register_type('comment', {
        'comment': {'type': 'string'}
    })

    assert set(t.name for t in registry) == {'page', 'comment'}

    with pytest.raises(AssertionError):
        registry.register_type('page', {})
