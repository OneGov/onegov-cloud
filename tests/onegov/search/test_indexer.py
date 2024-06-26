import logging
import pytest
import transaction

from datetime import datetime
from onegov.people import Person, PersonCollection
from onegov.search import Searchable, SearchOfflineError, utils
from onegov.search.indexer import parse_index_name, PostgresIndexer
from onegov.search.indexer import (
    Indexer,
    IndexManager,
    ORMEventTranslator,
    TypeMapping,
    TypeMappingRegistry
)
from queue import Queue
from unittest.mock import Mock


def test_index_manager_assertions(es_client):

    with pytest.raises(AssertionError):
        IndexManager(hostname='', es_client=es_client)

    ixmgr = IndexManager(hostname='test.example.org', es_client=es_client)

    page = TypeMapping('page', {
        'title': {'type': 'text'}
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
        'title': {'type': 'text'}
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
        'title': {'type': 'text'}
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
        'title': {'type': 'text'},
        'body': {'type': 'text'}
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
    result = parse_index_name('hostname_org-my_schema-de-posts')
    assert result.hostname == 'hostname_org'
    assert result.schema == 'my_schema'
    assert result.language == 'de'
    assert result.type_name == 'posts'
    assert result.version == None

    result = parse_index_name('hostname_org-my_schema-de-posts-1')
    assert result.hostname == 'hostname_org'
    assert result.schema == 'my_schema'
    assert result.language == 'de'
    assert result.type_name == 'posts'
    assert result.version == '1'

    result = parse_index_name('asdf')
    assert result.hostname is None
    assert result.schema is None
    assert result.language is None
    assert result.type_name is None
    assert result.version is None


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
            'type': 'text',
            'analyzer': 'english'
        },
        'es_public': {
            'type': 'boolean',
        },
        'es_last_change': {
            'type': 'date'
        },
        'es_suggestion': {
            'analyzer': 'autocomplete',
            'contexts': [
                {
                    'name': 'es_suggestion_context',
                    'type': 'category'
                }
            ],
            'type': 'completion'
        },
        'es_tags': {
            'type': 'text',
            'analyzer': 'tags',
        }
    }

    assert mapping.for_language('de') == {
        'title': {
            'type': 'text',
            'analyzer': 'german'
        },
        'es_public': {
            'type': 'boolean',
        },
        'es_last_change': {
            'type': 'date'
        },
        'es_suggestion': {
            'analyzer': 'autocomplete',
            'contexts': [
                {
                    'name': 'es_suggestion_context',
                    'type': 'category'
                }
            ],
            'type': 'completion'
        },
        'es_tags': {
            'type': 'text',
            'analyzer': 'tags',
        }
    }

    mapping = TypeMapping('bar', {
        'title': {
            'properties': {
                'type': 'localized',
            }
        }
    })

    assert mapping.for_language('de') == {
        'title': {
            'properties': {
                'type': 'text',
                'analyzer': 'german',
            }
        },
        'es_public': {
            'type': 'boolean',
        },
        'es_last_change': {
            'type': 'date'
        },
        'es_suggestion': {
            'analyzer': 'autocomplete',
            'contexts': [
                {
                    'name': 'es_suggestion_context',
                    'type': 'category'
                }
            ],
            'type': 'completion'
        },
        'es_tags': {
            'type': 'text',
            'analyzer': 'tags',
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
                'type': 'text',
                'analyzer': 'english_html'
            }
        },
        'es_public': {
            'type': 'boolean',
        },
        'es_last_change': {
            'type': 'date'
        },
        'es_suggestion': {
            'analyzer': 'autocomplete',
            'contexts': [
                {
                    'name': 'es_suggestion_context',
                    'type': 'category'
                }
            ],
            'type': 'completion'
        },
        'es_tags': {
            'type': 'text',
            'analyzer': 'tags',
        }
    }


def test_orm_event_translator_properties():

    class Page(Searchable):

        __tablename__ = 'my-pages'

        es_id = 'id'
        es_type_name = 'page'
        es_properties = {
            'title': {'type': 'localized'},
            'body': {'type': 'localized'},
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

        @property
        def es_last_change(self):
            return self.date

        @property
        def es_tags(self):
            return self.tags

    mappings = TypeMappingRegistry()
    mappings.register_type('page', Page.es_properties)

    translator = ORMEventTranslator(mappings)

    translator.on_insert('my-schema', Page(
        id=1,
        title='About',
        body='We are Pied Piper',
        tags=['aboutus', 'company'],
        date=datetime(2015, 9, 11),
        published=True,
        likes=1000
    ))

    expected = {
        'action': 'index',
        'schema': 'my-schema',
        'tablename': 'my-pages',
        'type_name': 'page',
        'id': 1,
        'id_key': 'id',
        'language': 'en',
        'properties': {
            'title': 'About',
            'body': 'We are Pied Piper',
            'date': '2015-09-11T00:00:00',
            'likes': 1000,
            'published': True,
            'es_tags': ['aboutus', 'company'],
            'es_public': True,
            'es_last_change': '2015-09-11T00:00:00',
            'es_suggestion': {
                'input': ['About'],
                'contexts': {
                    'es_suggestion_context': ['public']
                }
            }
        }
    }
    assert translator.es_queue.get() == expected
    assert translator.psql_queue.get() == expected

    assert translator.es_queue.empty()
    assert translator.psql_queue.empty()

    translator.on_update('my-schema', Page(
        id=1,
        title='About',
        body='We are Pied Piper',
        tags=['aboutus', 'company'],
        date=datetime(2015, 9, 11),
        published=True,
        likes=1000
    ))
    assert translator.es_queue.qsize() == 2
    assert translator.psql_queue.qsize() == 1

    expected = {
        'action': 'delete',
        'schema': 'my-schema',
        'tablename': 'my-pages',
        'type_name': 'page',
        'id': 1
    }
    assert translator.es_queue.get() == expected

    expected = {
        'action': 'index',
        'schema': 'my-schema',
        'tablename': 'my-pages',
        'type_name': 'page',
        'id': 1,
        'id_key': 'id',
        'language': 'en',
        'properties': {
            'title': 'About',
            'body': 'We are Pied Piper',
            'date': '2015-09-11T00:00:00',
            'likes': 1000,
            'published': True,
            'es_tags': ['aboutus', 'company'],
            'es_public': True,
            'es_last_change': '2015-09-11T00:00:00',
            'es_suggestion': {
                'input': ['About'],
                'contexts': {
                    'es_suggestion_context': ['public']
                }
            }
        }
    }
    assert translator.es_queue.get() == expected
    assert translator.psql_queue.get() == expected
    assert translator.es_queue.empty()
    assert translator.psql_queue.empty()


def test_orm_event_translator_delete():

    class Page(Searchable):

        __tablename__ = 'my-pages'

        def __init__(self, id):
            self.id = id

        es_id = 'id'
        es_type_name = 'page'

    mappings = TypeMappingRegistry()
    mappings.register_type('page', {})

    translator = ORMEventTranslator(mappings)
    translator.on_delete('foobar', Page(123))

    expected = {
        'action': 'delete',
        'schema': 'foobar',
        'tablename': 'my-pages',
        'type_name': 'page',
        'id': 123
    }
    assert translator.es_queue.get() == expected
    assert translator.psql_queue.empty()
    assert translator.es_queue.empty()


def test_orm_event_queue_overflow(capturelog):

    capturelog.setLevel(logging.ERROR, logger='onegov.search')

    class Tweet(Searchable):

        __tablename__ = 'my-tweets'

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

    translator = ORMEventTranslator(mappings, max_queue_size=4)
    translator.on_insert('foobar', Tweet(1))
    translator.on_update('foobar', Tweet(2))
    translator.on_delete('foobar', Tweet(3))

    assert len(capturelog.records(logging.ERROR)) == 0

    translator.on_insert('foobar', Tweet(4))

    assert len(capturelog.records(logging.ERROR)) == 1
    assert capturelog.records(logging.ERROR)[0].message == \
        'The orm event translator queue is full!'


def test_type_mapping_registry():

    registry = TypeMappingRegistry()
    registry.register_type('page', {
        'title': {'type': 'text'}
    })
    registry.register_type('comment', {
        'comment': {'type': 'text'}
    })

    assert set(t.name for t in registry) == {'page', 'comment'}

    with pytest.raises(AssertionError):
        registry.register_type('page', {})

    assert registry.registered_fields == {
        'title',
        'comment',
        'es_suggestion',
        'es_public',
        'es_last_change',
        'es_tags',
    }


def test_indexer_process(es_client, session_manager):
    engine = session_manager.engine
    mappings = TypeMappingRegistry()
    mappings.register_type('page', {
        'title': {'type': 'localized'},
    })

    index = "foo_bar-my_schema-en-page"
    es_indexer = Indexer(
        mappings, Queue(), hostname='foo.bar', es_client=es_client)
    psql_indexer = PostgresIndexer(Queue(), engine)

    task = {
        'action': 'index',
        'schema': 'my-schema',
        'tablename': 'my-pages',
        'type_name': 'page',
        'id': 1,
        'language': 'en',
        'properties': {
            'title': 'Go ahead and jump',
            'es_public': True
        }
    }
    es_indexer.queue.put(task)
    psql_indexer.queue.put(task)

    assert es_indexer.process() == 1
    assert es_indexer.process() == 0
    es_client.indices.refresh(index=index)
    assert psql_indexer.process() == 1
    assert psql_indexer.process() == 0

    search = es_client.search(index=index)
    assert search['hits']['total']['value'] == 1
    assert search['hits']['hits'][0]['_id'] == '1'
    assert search['hits']['hits'][0]['_source'] == {
        'title': 'Go ahead and jump',
        'es_public': True
    }
    assert search['hits']['hits'][0]['_type'] == '_doc'
    # TODO: search for psql

    # check if the analyzer was applied correctly (stopword removal)
    search = es_client.search(
        index=index, query={'match': {'title': 'and'}})

    assert search['hits']['total']['value'] == 0

    search = es_client.search(
        index=index, query={'match': {'title': 'go jump'}})

    assert search['hits']['total']['value'] == 1

    # delete the document again
    task = {
        'action': 'delete',
        'schema': 'my-schema',
        'type_name': 'page',
        'id': 1
    }
    es_indexer.queue.put(task)

    assert es_indexer.process() == 1
    assert es_indexer.process() == 0
    es_client.indices.refresh(index=index)

    es_client.search(index=index)
    assert search['hits']['total']['value'] == 1


def test_indexer_bulk_process_mid_transaction(session_manager, session):
    engine = session_manager.engine
    psql_indexer = PostgresIndexer(Queue(), engine)

    people = PersonCollection(session)
    person1 = people.add(first_name='John', last_name='Doe')
    psql_indexer.queue.put({
        'action': 'index',
        'schema': session_manager.current_schema,
        'tablename': 'people',
        'type_name': 'person',
        'id': person1.id,
        'id_key': 'id',
        'language': 'en',
        'properties': {
            'title': person1.title,
            'es_public': True
        }
    })
    person2 = people.add(first_name='Jane', last_name='Doe')
    psql_indexer.queue.put({
        'action': 'index',
        'schema': session_manager.current_schema,
        'tablename': 'people',
        'type_name': 'person',
        'id': person2.id,
        'id_key': 'id',
        'language': 'en',
        'properties': {
            'title': person2.title,
            'es_public': True
        }
    })
    psql_indexer.bulk_process(session)
    person3 = people.add(first_name='Paul', last_name='Atishon')
    psql_indexer.queue.put({
        'action': 'index',
        'schema': session_manager.current_schema,
        'tablename': 'people',
        'type_name': 'person',
        'id': person3.id,
        'id_key': 'id',
        'language': 'en',
        'properties': {
            'title': person3.title,
            'es_public': True
        }
    })
    psql_indexer.bulk_process(session)
    # make sure we can commit
    transaction.commit()
    transaction.begin()
    # make sure the people exist and have their fts_idx column set
    assert people.query().filter(Person.fts_idx.isnot(None)).count() == 3


def test_extra_analyzers(es_client):

    page = TypeMapping('page', {
        'title': {'type': 'text'}
    })

    ixmgr = IndexManager(hostname='foo.bar', es_client=es_client)
    index = ixmgr.ensure_index(
        schema='foo_bar',
        language='en',
        mapping=page
    )

    result = es_client.indices.analyze(
        index=index,
        body={
            'text': 'Do you <em>really</em> want to continue?',
            'analyzer': 'english_html'
        }
    )
    assert [v['token'] for v in result['tokens']] == [
        'do', 'you', 'realli', 'want', 'continu'
    ]

    result = es_client.indices.analyze(
        index=index,
        body={
            'text': 'Möchten Sie <em>wirklich</em> weiterfahren?',
            'analyzer': 'german_html'
        }
    )
    assert [v['token'] for v in result['tokens']] == [
        'mocht', 'wirklich', 'weiterfahr'
    ]


def test_tags(es_client, session_manager):

    mappings = TypeMappingRegistry()
    mappings.register_type('page', {
        'tags': {'type': 'text', 'analyzer': 'tags'}
    })

    index = "foo-bar-en-page"
    es_indexer = Indexer(mappings, Queue(), es_client, hostname='foo')
    psql_indexer = PostgresIndexer(Queue(), session_manager.engine)

    task = {
        'action': 'index',
        'schema': 'bar',
        'tablename': 'my-bar',
        'type_name': 'page',
        'id': 1,
        'language': 'en',
        'properties': {
            'tags': ['foo', 'BAR', 'baz'],
            'es_public': True
        }
    }
    es_indexer.queue.put(task)
    psql_indexer.queue.put(task)

    assert es_indexer.process()
    assert psql_indexer.process()

    es_client.indices.refresh(index=index)
    search = es_client.search(index=index)

    assert search['hits']['total']['value'] == 1
    # TODO search for psql

    search = es_client.search(
        index=index, query={'match': {'tags': 'foo'}})

    assert search['hits']['total']['value'] == 1

    search = es_client.search(
        index=index, query={'match': {'tags': 'bar'}})

    assert search['hits']['total']['value'] == 1

    search = es_client.search(
        index=index, query={'match': {'tags': 'bad'}})

    assert search['hits']['total']['value'] == 0


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

    original = indexer.es_client.transport.perform_request
    indexer.es_client.transport.perform_request = Mock(
        side_effect=SearchOfflineError)

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

    indexer.es_client.transport.perform_request = original

    indexer.es_client.indices.refresh(index='_all')
    assert indexer.es_client\
        .search(index='_all')['hits']['total']['value'] == 0

    assert indexer.process() == 2
    assert indexer.failed_task is None

    indexer.es_client.indices.refresh(index='_all')
    assert indexer.es_client\
        .search(index='_all')['hits']['total']['value'] == 2
