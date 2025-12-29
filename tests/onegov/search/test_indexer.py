from __future__ import annotations

import logging
import pytest
import transaction

from datetime import datetime
from onegov.people import PersonCollection
from onegov.search import Searchable
from onegov.search.datamanager import IndexerDataManager
from onegov.search.indexer import (
    Indexer,
    ORMEventTranslator,
    TypeMappingRegistry
)
from onegov.search.search_index import SearchIndex
from unittest.mock import patch, Mock


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager
    from onegov.search.indexer import Task
    from sqlalchemy.orm import Session
    from unittest.mock import MagicMock
    from tests.shared.capturelog import CaptureLogFixture


@patch('onegov.search.indexer.object_session')
def test_orm_event_translator_properties(object_session: MagicMock) -> None:

    session: Any = Mock()
    object_session.return_value = session

    class Page(Searchable):

        __tablename__ = 'my-pages'

        fts_id = 'id'
        fts_title_property = 'title'
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
    mappings.register_type(
        'Page',
        Page.fts_properties,
        Page.fts_title_property
    )

    indexer = Indexer(mappings)
    translator = ORMEventTranslator(indexer)

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
        'title': 'About',
        'properties': {
            'title': 'About',
            'body': 'We are Pied Piper',
            'date': '2015-09-11 00:00:00',
            'likes': '1000',
            'published': 'True',
        }
    }
    queue = IndexerDataManager.get_queue(session, indexer)
    assert queue is not None
    assert len(queue) == 1
    assert queue.pop() == expected
    assert len(queue) == 0

    translator.on_update('my-schema', Page(
        id=1,
        title='About',
        body='We are Pied Piper',
        tags=['aboutus', 'company'],
        date=datetime(2015, 9, 11),
        published=True,
        likes=1000
    ))
    assert len(queue) == 1

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
        'title': 'About',
        'properties': {
            'title': 'About',
            'body': 'We are Pied Piper',
            'date': '2015-09-11 00:00:00',
            'likes': '1000',
            'published': 'True',
        },
    }
    assert queue.pop() == expected
    assert len(queue) == 0


@patch('onegov.search.indexer.object_session')
def test_orm_event_translator_delete(object_session: MagicMock) -> None:

    session: Any = Mock()
    object_session.return_value = session

    class Page(Searchable):

        __tablename__ = 'my-pages'

        def __init__(self, id: int) -> None:
            self.id = id

        fts_id = 'id'

    mappings = TypeMappingRegistry()
    mappings.register_type('Page', {})

    indexer = Indexer(mappings)
    translator = ORMEventTranslator(indexer)
    translator.on_delete('foobar', session, Page(123))

    expected = {
        'action': 'delete',
        'schema': 'foobar',
        'tablename': 'my-pages',
        'owner_type': 'Page',
        'id': 123
    }
    queue = IndexerDataManager.get_queue(session, indexer)
    assert queue is not None
    assert queue.pop() == expected
    assert len(queue) == 0


@patch('onegov.search.indexer.object_session')
def test_orm_event_queue_overflow(
    object_session: MagicMock,
    capturelog: CaptureLogFixture
) -> None:

    session: Any = Mock()
    object_session.return_value = session

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

    indexer = Indexer(mappings)
    translator = ORMEventTranslator(indexer, max_queue_size=3)
    translator.on_insert('foobar', Tweet(1))
    translator.on_update('foobar', Tweet(2))
    translator.on_delete('foobar', session, Tweet(3))

    assert len(capturelog.records(logging.ERROR)) == 0

    translator.on_insert('foobar', Tweet(4))

    assert len(capturelog.records(logging.ERROR)) == 1
    assert capturelog.records(logging.ERROR)[0].message == (
        'The orm event translator queue is full!')


def test_type_mapping_registry() -> None:

    registry = TypeMappingRegistry()
    registry.register_type('Page', {
        'title': {'type': 'text', 'weight': 'A'}
    }, 'title')
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
    }, 'title')
    indexer = Indexer(mappings)

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
        'title': 'Go ahead and jump',
        'properties': {'title': 'Go ahead and jump'},
    }
    assert indexer.process([task], session) == 1

    # TODO: search indexed entry in search index

    # delete the document again
    task = {
        'action': 'delete',
        'schema': session_manager.current_schema,
        'tablename': 'my-pages',
        'owner_type': 'Page',
        'id': 1
    }
    assert indexer.process([task], session) == 1

    # TODO: search deleted entry in search index


def test_indexer_process_mid_transaction(
    session_manager: SessionManager,
    session: Session
) -> None:

    assert session_manager.current_schema is not None
    mappings = TypeMappingRegistry()
    mappings.register_type('Person', {
        'title': {'type': 'text', 'weight': 'A'},
    }, 'title')
    engine = session_manager.engine
    indexer = Indexer(mappings)
    tasks: list[Task] = []

    people = PersonCollection(session)
    person1 = people.add(first_name='John', last_name='Doe')
    tasks.append({
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
        'title': person1.title,
        'properties': {'title': person1.title},
    })
    person2 = people.add(first_name='Jane', last_name='Doe')
    tasks.append({
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
        'title': person2.title,
        'properties': {'title': person2.title}
    })
    indexer.process(tasks, session)
    tasks.clear()
    person3 = people.add(first_name='Paul', last_name='Atishon')
    tasks.append({
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
        'title': person3.title,
        'properties': {'title': person3.title}
    })
    indexer.process(tasks, session)
    # make sure we can commit
    transaction.commit()
    transaction.begin()
    # make sure the people got indexed and therefore exist in `SearchIndex`
    # having their fts_idx column set
    assert (session.query(SearchIndex).
            filter(SearchIndex.data_vector.isnot(None)).count() == 3)


def test_tags(
    session_manager: SessionManager,
    session: Session
) -> None:

    mappings = TypeMappingRegistry()
    mappings.register_type('Page', {})
    schema = session_manager.current_schema
    assert schema is not None
    indexer = Indexer(mappings)

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
        'title': '',
        'properties': {},
    }
    assert indexer.process([task], session)

    # TODO search indexed entry using search index via tags
