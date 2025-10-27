from __future__ import annotations

import logging
import pytest
import transaction

from datetime import datetime
from onegov.people import PersonCollection
from onegov.search import Searchable
from onegov.search.indexer import (
    Indexer,
    ORMEventTranslator,
    TypeMappingRegistry
)
from onegov.search.search_index import SearchIndex
from queue import Queue


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager
    from onegov.search.indexer import Task
    from sqlalchemy.orm import Session
    from tests.shared.capturelog import CaptureLogFixture


def test_orm_event_translator_properties() -> None:

    class Page(Searchable):

        __tablename__ = 'my-pages'

        fts_id = 'id'
        fts_properties = {
            'title': {'type': 'localized', 'weight': 'A'},
            'body': {'type': 'localized', 'weight': 'B'},
            'date': {'type': 'date', 'weight': 'B'},
            'published': {'type': 'boolean', 'weight': 'D'},
            'likes': {'type': 'long', 'weight': 'D'}
        }

        def __init__(self, id: int, **kwargs: Any) -> None:
            self.id = id
            self.language = kwargs.pop('language', 'en')
            self.public = kwargs.pop('public', True)

            for k, v in kwargs.items():
                setattr(self, k, v)

        @property
        def fts_language(self) -> str:
            return self.language

        @property
        def fts_public(self) -> bool:
            return self.public

        @property
        def fts_suggestion(self) -> str:
            return self.title  # type: ignore[attr-defined]

        @property
        def fts_last_change(self) -> datetime | None:
            return self.date  # type: ignore[attr-defined]

        @property
        def fts_tags(self) -> list[str]:
            return self.tags  # type: ignore[attr-defined]

    mappings = TypeMappingRegistry()
    mappings.register_type('Page', Page.fts_properties)

    translator = ORMEventTranslator(mappings)

    creation_date = datetime(2015, 9, 11)
    translator.on_insert('my-schema', Page(
        id=1,
        title='About',
        body='We are Pied Piper',
        tags=['aboutus', 'company'],
        date=creation_date,
        published=True,
        likes=1000
    ))

    expected = {
        'action': 'index',
        'schema': 'my-schema',
        'tablename': 'my-pages',
        'id': 1,
        'id_key': 'id',
        'owner_type': 'Page',
        'language': 'en',
        'access': 'public',
        'public': True,
        'suggestion': ['About'],
        'tags': ['aboutus', 'company'],
        'publication_start': None,
        'publication_end': None,
        'last_change': creation_date,
        'properties': {
            'title': 'About',
            'body': 'We are Pied Piper',
            'date': '2015-09-11 00:00:00',
            'likes': '1000',
            'published': 'True',
        }
    }
    assert translator.queue.qsize() == 1
    assert translator.queue.get() == expected
    assert translator.queue.empty()

    translator.on_update('my-schema', Page(
        id=1,
        title='About',
        body='We are Pied Piper',
        tags=['aboutus', 'company'],
        date=datetime(2015, 9, 11),
        published=True,
        likes=1000
    ))
    assert translator.queue.qsize() == 1

    expected = {
        'action': 'index',
        'schema': 'my-schema',
        'tablename': 'my-pages',
        'id': 1,
        'id_key': 'id',
        'owner_type': 'Page',
        'language': 'en',
        'access': 'public',
        'public': True,
        'suggestion': ['About'],
        'tags': ['aboutus', 'company'],
        'publication_start': None,
        'publication_end': None,
        'last_change': creation_date,
        'properties': {
            'title': 'About',
            'body': 'We are Pied Piper',
            'date': '2015-09-11 00:00:00',
            'likes': '1000',
            'published': 'True',
        },
    }
    assert translator.queue.get() == expected
    assert translator.queue.empty()


def test_orm_event_translator_delete() -> None:

    class Page(Searchable):

        __tablename__ = 'my-pages'

        def __init__(self, id: int) -> None:
            self.id = id

        fts_id = 'id'

    mappings = TypeMappingRegistry()
    mappings.register_type('Page', {})

    translator = ORMEventTranslator(mappings)
    translator.on_delete('foobar', Page(123))

    expected = {
        'action': 'delete',
        'schema': 'foobar',
        'tablename': 'my-pages',
        'owner_type': 'Page',
        'id': 123
    }
    assert translator.queue.get() == expected
    assert translator.queue.empty()


def test_orm_event_queue_overflow(capturelog: CaptureLogFixture) -> None:

    capturelog.setLevel(logging.ERROR, logger='onegov.search')

    class Tweet(Searchable):

        __tablename__ = 'my-tweets'

        def __init__(self, id: int) -> None:
            self.id = id

        @property
        def fts_suggestion(self) -> str:
            return str(self.id)

        fts_id = 'id'
        fts_language = 'en'
        fts_public = True
        fts_properties = {}

    mappings = TypeMappingRegistry()
    mappings.register_type('Tweet', {})

    translator = ORMEventTranslator(mappings, max_queue_size=3)
    translator.on_insert('foobar', Tweet(1))
    translator.on_update('foobar', Tweet(2))
    translator.on_delete('foobar', Tweet(3))

    assert len(capturelog.records(logging.ERROR)) == 0

    translator.on_insert('foobar', Tweet(4))

    assert len(capturelog.records(logging.ERROR)) == 1
    assert capturelog.records(logging.ERROR)[0].message == (
        'The orm event translator queue is full!')


def test_type_mapping_registry() -> None:

    registry = TypeMappingRegistry()
    registry.register_type('Page', {
        'title': {'type': 'text', 'weight': 'A'}
    })
    registry.register_type('Comment', {
        'comment': {'type': 'text', 'weight': 'A'}
    })

    assert set(t.name for t in registry) == {'Page', 'Comment'}

    with pytest.raises(AssertionError):
        registry.register_type('Page', {})

    assert registry.registered_fields == {
        'title',
        'comment',
    }


def test_indexer_process(
    session_manager: SessionManager,
    session: Session
) -> None:

    assert session_manager.current_schema is not None
    engine = session_manager.engine
    mappings = TypeMappingRegistry()
    mappings.register_type('Page', {
        'title': {'type': 'localized', 'weight': 'A'},
    })
    indexer = Indexer(mappings, Queue(), engine)

    task: Task = {
        'action': 'index',
        'schema': session_manager.current_schema,
        'tablename': 'my-pages',
        'id': 1,
        'id_key': 'id',
        'owner_type': 'Page',
        'access': 'public',
        'public': True,
        'last_change': None,
        'publication_start': None,
        'publication_end': None,
        'suggestion': [],
        'tags': [],
        'language': 'en',
        'properties': {'title': 'Go ahead and jump'},
    }
    indexer.queue.put(task)
    assert indexer.process() == 1
    assert indexer.process() == 0

    # TODO: search indexed entry in search index

    # delete the document again
    task = {
        'action': 'delete',
        'schema': session_manager.current_schema,
        'tablename': 'my-pages',
        'owner_type': 'Page',
        'id': 1
    }
    indexer.queue.put(task)
    assert indexer.process() == 1
    assert indexer.process() == 0

    # TODO: search deleted entry in search index


def test_indexer_bulk_process_mid_transaction(
    session_manager: SessionManager,
    session: Session
) -> None:

    assert session_manager.current_schema is not None
    mappings = TypeMappingRegistry()
    mappings.register_type('Person', {
        'title': {'type': 'text', 'weight': 'A'},
    })
    engine = session_manager.engine
    indexer = Indexer(mappings, Queue(), engine)

    people = PersonCollection(session)
    person1 = people.add(first_name='John', last_name='Doe')
    indexer.queue.put({
        'action': 'index',
        'schema': session_manager.current_schema,
        'tablename': 'people',
        'id': person1.id,
        'id_key': 'id',
        'owner_type': 'Person',
        'language': 'en',
        'suggestion': ['John Doe'],
        'tags': [],
        'access': 'public',
        'public': True,
        'publication_start': None,
        'publication_end': None,
        'last_change': person1.last_change,
        'properties': {'title': person1.title},
    })
    person2 = people.add(first_name='Jane', last_name='Doe')
    indexer.queue.put({
        'action': 'index',
        'schema': session_manager.current_schema,
        'tablename': 'people',
        'id': person2.id,
        'id_key': 'id',
        'owner_type': 'Person',
        'language': 'en',
        'suggestion': ['Jane Doe'],
        'tags': [],
        'access': 'public',
        'public': True,
        'publication_start': None,
        'publication_end': None,
        'last_change': person2.last_change,
        'properties': {'title': person2.title}
    })
    indexer.process(session)
    person3 = people.add(first_name='Paul', last_name='Atishon')
    indexer.queue.put({
        'action': 'index',
        'schema': session_manager.current_schema,
        'tablename': 'people',
        'id': person3.id,
        'id_key': 'id',
        'owner_type': 'Person',
        'language': 'en',
        'suggestion': ['Paul Atishon', 'Atishon Paul'],
        'tags': [],
        'access': 'public',
        'public': True,
        'publication_start': None,
        'publication_end': None,
        'last_change': person3.last_change,
        'properties': {'title': person3.title}
    })
    indexer.process(session)
    # make sure we can commit
    transaction.commit()
    transaction.begin()
    # make sure the people got indexed and therefore exist in `SearchIndex`
    # having their fts_idx column set
    assert (session.query(SearchIndex).
            filter(SearchIndex.fts_idx.isnot(None)).count() == 3)


def test_tags(
    session_manager: SessionManager,
    session: Session
) -> None:

    mappings = TypeMappingRegistry()
    mappings.register_type('Page', {})
    schema = session_manager.current_schema
    assert schema is not None
    indexer = Indexer(mappings, Queue(), session_manager.engine)

    task: Task = {
        'action': 'index',
        'schema': schema,
        'tablename': 'my-bar',
        'id': 1,
        'id_key': 'id',
        'owner_type': 'Page',
        'language': 'en',
        'suggestion': [],
        'tags': ['foo', 'BAR', 'baz'],
        'access': 'public',
        'public': True,
        'publication_start': None,
        'publication_end': None,
        'last_change': None,
        'properties': {},
    }
    indexer.queue.put(task)
    assert indexer.process()

    # TODO search indexed entry using search index via tags
