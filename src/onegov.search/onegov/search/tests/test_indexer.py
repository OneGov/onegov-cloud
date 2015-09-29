# -*- coding: utf-8 -*-
import logging
import pytest

from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import TransportError
from mock import Mock
from onegov.search import Searchable, utils
from onegov.search.compat import Queue
from onegov.search.indexer import (
    Indexer,
    IndexManager,
    ORMEventTranslator,
    TypeMapping,
    TypeMappingRegistry
)


def test_index_manager_assertions(es_client):

    with pytest.raises(AssertionError):
        IndexManager(hostname='', es_client=es_client)

    ixmgr = IndexManager(hostname='test.example.org', es_client=es_client)

    page = TypeMapping('page', {
        'title': {'type': 'string'}
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


def test_index_manager_connection(es_client):
    ixmgr = IndexManager(hostname='foobar', es_client=es_client)
    assert ixmgr.es_client.ping()


def test_index_manager_separation(es_client):
    foo = IndexManager(hostname='foo', es_client=es_client)
    bar = IndexManager(hostname='bar', es_client=es_client)

    page = TypeMapping('page', {
        'title': {'type': 'string'}
    })

    foo.ensure_index('foo', 'en', page)
    bar.ensure_index('bar', 'en', page)

    assert foo.query_indices() == {'foo-foo-en-page' + '-' + page.version}
    assert bar.query_indices() == {'bar-bar-en-page' + '-' + page.version}
    assert foo.query_aliases() == {'foo-foo-en-page'}
    assert bar.query_aliases() == {'bar-bar-en-page'}


def test_index_creation(es_client):
    ixmgr = IndexManager(hostname='example.org', es_client=es_client)

    page = TypeMapping('page', {
        'title': {'type': 'string'}
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
        'title': {'type': 'string'},
        'body': {'type': 'string'}
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


def test_parse_index_name(es_client):
    ixmgr = IndexManager('foo', es_client)
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
        'es_public': {
            'type': 'boolean',
            'index': 'not_analyzed',
            'include_in_all': False
        },
        'es_public_categories': {
            'include_in_all': False,
            'index': 'not_analyzed',
            'type': 'string'
        },
        'es_suggestion': {
            'context': {
                'es_public_categories': {
                    'path': 'es_public_categories',
                    'type': 'category'
                }
            },
            'index_analyzer': 'standard',
            'payloads': True,
            'search_analyzer': 'standard',
            'type': 'completion'
        }
    }

    assert mapping.for_language('de') == {
        'title': {
            'type': 'string',
            'analyzer': 'german'
        },
        'es_public': {
            'type': 'boolean',
            'index': 'not_analyzed',
            'include_in_all': False
        },
        'es_public_categories': {
            'include_in_all': False,
            'index': 'not_analyzed',
            'type': 'string'
        },
        'es_suggestion': {
            'context': {
                'es_public_categories': {
                    'path': 'es_public_categories',
                    'type': 'category'
                }
            },
            'index_analyzer': 'standard',
            'payloads': True,
            'search_analyzer': 'standard',
            'type': 'completion'
        }
    }

    mapping = TypeMapping('bar', {
        'title': {
            'properties': {
                'type': 'localized',
                'index': 'not_analyzed'
            }
        }
    })

    assert mapping.for_language('de') == {
        'title': {
            'properties': {
                'type': 'string',
                'analyzer': 'german',
                'index': 'not_analyzed'
            }
        },
        'es_public': {
            'type': 'boolean',
            'index': 'not_analyzed',
            'include_in_all': False
        },
        'es_public_categories': {
            'include_in_all': False,
            'index': 'not_analyzed',
            'type': 'string'
        },
        'es_suggestion': {
            'context': {
                'es_public_categories': {
                    'path': 'es_public_categories',
                    'type': 'category'
                }
            },
            'index_analyzer': 'standard',
            'payloads': True,
            'search_analyzer': 'standard',
            'type': 'completion'
        }
    }

    mapping = TypeMapping('baz', {
        'title': {
            'properties': {
                'type': 'localized_html'
            }
        }
    })

    assert mapping.for_language('en') == {
        'title': {
            'properties': {
                'type': 'string',
                'analyzer': 'english_html'
            }
        },
        'es_public': {
            'type': 'boolean',
            'index': 'not_analyzed',
            'include_in_all': False
        },
        'es_public_categories': {
            'include_in_all': False,
            'index': 'not_analyzed',
            'type': 'string'
        },
        'es_suggestion': {
            'context': {
                'es_public_categories': {
                    'path': 'es_public_categories',
                    'type': 'category'
                }
            },
            'index_analyzer': 'standard',
            'payloads': True,
            'search_analyzer': 'standard',
            'type': 'completion'
        }
    }


def test_orm_event_translator_properties():

    class Page(Searchable):

        es_id = 'id'
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
        def es_language(self):
            return self.language

        @property
        def es_public(self):
            return self.public

        @property
        def es_suggest(self):
            return self.title

    mappings = TypeMappingRegistry()
    mappings.register_type('page', Page.es_properties)

    translator = ORMEventTranslator(mappings)

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
            'type_name': 'page',
            'id': 1,
            'language': 'en',
            'properties': {
                'title': 'About',
                'body': 'We are Pied Piper',
                'tags': ['aboutus', 'company'],
                'date': '2015-09-11T00:00:00',
                'likes': 1000,
                'published': True,
                'es_public': True,
                'es_public_categories': ['public'],
                'es_suggestion': {
                    'input': ['About'],
                    'output': 'About'
                }
            }
        }
        assert translator.queue.empty()


def test_orm_event_translator_delete():

    class Page(Searchable):

        def __init__(self, id):
            self.id = id

        es_id = 'id'
        es_type_name = 'page'

    mappings = TypeMappingRegistry()
    mappings.register_type('page', {})

    translator = ORMEventTranslator(mappings)
    translator.on_delete('foobar', Page(123))

    assert translator.queue.get() == {
        'action': 'delete',
        'schema': 'foobar',
        'type_name': 'page',
        'id': 123
    }
    assert translator.queue.empty()


def test_orm_event_queue_overflow(capturelog):

    capturelog.setLevel(logging.ERROR, logger='onegov.search')

    class Tweet(Searchable):

        def __init__(self, id):
            self.id = id

        @property
        def es_suggestion(self):
            return self.id

        es_id = 'id'
        es_type_name = 'tweet'
        es_language = 'en'
        es_public = True
        es_properties = {}

    mappings = TypeMappingRegistry()
    mappings.register_type('tweet', {})

    translator = ORMEventTranslator(mappings, max_queue_size=3)
    translator.on_insert('foobar', Tweet(1))
    translator.on_update('foobar', Tweet(2))
    translator.on_delete('foobar', Tweet(3))

    assert len(capturelog.records()) == 0

    translator.on_insert('foobar', Tweet(4))

    assert len(capturelog.records()) == 1
    assert capturelog.records()[0].message == \
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


def test_indexer_process(es_client):
    mappings = TypeMappingRegistry()
    mappings.register_type('page', {
        'title': {'type': 'localized'},
    })

    index = "foo_bar-my_schema-en-page"
    indexer = Indexer(
        mappings, Queue(), hostname='foo.bar', es_client=es_client)

    indexer.queue.put({
        'action': 'index',
        'schema': 'my-schema',
        'type_name': 'page',
        'id': 1,
        'language': 'en',
        'properties': {
            'title': 'Go ahead and jump',
            'es_public': True
        }
    })

    assert indexer.process() == 1
    assert indexer.process() == 0
    es_client.indices.refresh(index=index)

    search = es_client.search(index=index)
    assert search['hits']['total'] == 1
    assert search['hits']['hits'][0]['_id'] == '1'
    assert search['hits']['hits'][0]['_source'] == {
        'title': 'Go ahead and jump',
        'es_public': True
    }
    assert search['hits']['hits'][0]['_type'] == 'page'

    # check if the analyzer was applied correctly (stopword removal)
    search = es_client.search(
        index=index, body={'query': {'match': {'title': 'and'}}})

    assert search['hits']['total'] == 0

    search = es_client.search(
        index=index, body={'query': {'match': {'title': 'go jump'}}})

    assert search['hits']['total'] == 1

    # delete the document again
    indexer.queue.put({
        'action': 'delete',
        'schema': 'my-schema',
        'type_name': 'page',
        'id': 1
    })

    assert indexer.process() == 1
    assert indexer.process() == 0
    es_client.indices.refresh(index=index)

    es_client.search(index=index)
    assert search['hits']['total'] == 1


def test_extra_analyzers(es_client):

    page = TypeMapping('page', {
        'title': {'type': 'string'}
    })

    ixmgr = IndexManager(hostname='foo.bar', es_client=es_client)
    index = ixmgr.ensure_index(
        schema='foo_bar',
        language='en',
        mapping=page
    )

    result = es_client.indices.analyze(
        index=index,
        body='Do you <em>really</em> want to continue?',
        analyzer='english_html'
    )
    assert [v['token'] for v in result['tokens']] == [
        'do', 'you', 'realli', 'want', 'continu'
    ]

    result = es_client.indices.analyze(
        index=index,
        body=u'Möchten Sie <em>wirklich</em> weiterfahren?',
        analyzer='german_html'
    )
    assert [v['token'] for v in result['tokens']] == [
        u'mocht', u'wirklich', u'weiterfahr'
    ]


def test_elasticsearch_outage(es_client, es_url):
    mappings = TypeMappingRegistry()
    mappings.register_type('page', {
        'title': {'type': 'localized'},
    })

    indexer = Indexer(
        mappings, Queue(), hostname='foo.bar', es_client=es_client)

    indexer.queue.put({
        'action': 'index',
        'schema': 'my-schema',
        'type_name': 'page',
        'id': 1,
        'language': 'en',
        'properties': {
            'title': 'Foo',
            'es_public': True
        }
    })

    indexer.es_client.index = Mock(side_effect=TransportError)

    for i in range(0, 2):
        assert indexer.process() == 0
        assert indexer.queue.empty()
        assert indexer.failed_task is not None

    indexer.queue.put({
        'action': 'index',
        'schema': 'my-schema',
        'type_name': 'page',
        'id': 2,
        'language': 'en',
        'properties': {
            'title': 'Bar',
            'es_public': True
        }
    })

    for i in range(0, 2):
        assert indexer.process() == 0
        assert not indexer.queue.empty()
        assert indexer.failed_task is not None

    indexer.es_client = Elasticsearch(es_url)

    indexer.es_client.indices.refresh(index='_all')
    assert indexer.es_client.search(index='_all')['hits']['total'] == 0

    assert indexer.process() == 2
    assert indexer.failed_task is None

    indexer.es_client.indices.refresh(index='_all')
    assert indexer.es_client.search(index='_all')['hits']['total'] == 2
