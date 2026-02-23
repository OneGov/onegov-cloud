from __future__ import annotations

import morepath
import pytest
import pickle
import sqlalchemy
import time
import transaction
import uuid

from collections.abc import Callable, Mapping
from datetime import datetime
from dogpile.cache.api import NO_VALUE
from markupsafe import Markup
from onegov.core.framework import Framework
from onegov.core.orm import (
    ModelBase, SessionManager, as_selectable, translation_hybrid,
    translation_markup_hybrid, find_models)
from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.abstract import Associable, associated
from onegov.core.orm.func import unaccent
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import dict_markup_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm import orm_cached, request_cached
from onegov.core.orm.types import HSTORE, JSON, UTCDateTime
from onegov.core.orm.types import LowercaseText, MarkupText
from onegov.core.security import Private
from onegov.core.utils import scan_morepath_modules
from psycopg2.extensions import TransactionRollbackError
from pytz import timezone
from sedate import utcnow
from sqlalchemy import and_, func, inspect, select, text, ForeignKey, Integer
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import mapped_column, registry, relationship
from sqlalchemy.orm import DeclarativeBase, Mapped
from sqlalchemy_utils import aggregated
from threading import Thread
from webob.exc import HTTPUnauthorized, HTTPConflict
from webtest import TestApp as Client


from typing import Any, NamedTuple, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.core.types import JSON_ro
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql import ColumnElement
    from webob import Response

    _F = TypeVar('_F', bound=Callable[..., Any])


class PicklePage(AdjacencyList):
    __tablename__ = 'picklepages'


def test_is_valid_schema(postgres_dsn: str) -> None:
    mgr = SessionManager(postgres_dsn, None)  # type: ignore[arg-type]
    assert not mgr.is_valid_schema('pg_test')
    assert not mgr.is_valid_schema('-- or 1=1')
    assert not mgr.is_valid_schema('0')
    assert not mgr.is_valid_schema('information_schema')
    assert not mgr.is_valid_schema('public')
    assert not mgr.is_valid_schema('my--schema')
    assert mgr.is_valid_schema('my_schema')
    assert mgr.is_valid_schema('my-schema')


def test_independent_sessions(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'document'
        id: Mapped[int] = mapped_column(primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)

    mgr.set_current_schema('foo')
    s1 = mgr.session()

    s1.add(Document())
    s1.flush()

    mgr.set_current_schema('bar')
    s2 = mgr.session()

    assert s1 is not s2

    assert s1.query(Document).count() == 1
    assert s2.query(Document).count() == 0

    mgr.dispose()


def test_independent_managers(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'document'
        id: Mapped[int] = mapped_column(primary_key=True)

    one = SessionManager(postgres_dsn, Base)
    two = SessionManager(postgres_dsn, Base)

    one.set_current_schema('foo')
    two.set_current_schema('foo')

    assert one.session() is not two.session()
    assert one.session() is one.session()
    assert two.session() is two.session()

    one.session().add(Document())
    one.session().flush()

    assert one.session().query(Document).count() == 1
    assert two.session().query(Document).count() == 0

    one.set_current_schema('bar')
    assert one.session().info == {'schema': 'bar'}
    assert two.session().info == {'schema': 'foo'}

    one.dispose()
    two.dispose()


def test_create_schema(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'document'

        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str | None]

    mgr = SessionManager(postgres_dsn, Base)

    # we need a schema to use the session manager and it can't be 'public'
    mgr.set_current_schema('testing')

    def existing_schemas() -> set[str]:
        # DO NOT copy this query, it's insecure (which is fine in testing)
        with mgr.engine.connect() as conn:
            return {
                schema_name for schema_name, in conn.execute(text(
                    'SELECT schema_name FROM information_schema.schemata'
                ))
            }

    def schema_tables(schema: str) -> set[str]:
        # DO NOT copy this query, it's insecure (which is fine in testing)
        with mgr.engine.connect() as conn:
            return {
                tablename for tablename, in conn.execute(text(
                    "SELECT tablename FROM pg_catalog.pg_tables "
                    "WHERE schemaname = '{}'".format(schema)
                ))
            }

    assert 'testing' in existing_schemas()
    assert 'new' not in existing_schemas()

    mgr.ensure_schema_exists('new')

    assert 'new' in existing_schemas()
    assert 'document' in schema_tables('new')

    mgr.dispose()


def test_schema_bound_session(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'

        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str | None]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')
    session = mgr.session()

    session.add(Document(title='Welcome to Foo'))
    transaction.commit()

    assert session.query(Document).one().title == 'Welcome to Foo'

    mgr.set_current_schema('bar')
    session = mgr.session()

    assert session.query(Document).first() is None

    mgr.set_current_schema('foo')
    session = mgr.session()

    assert session.query(Document).one().title == 'Welcome to Foo'

    mgr.dispose()


def test_session_scope(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    mgr = SessionManager(postgres_dsn, Base)

    mgr.set_current_schema('foo')
    foo_session = mgr.session()

    mgr.set_current_schema('bar')
    bar_session = mgr.session()

    assert foo_session is not bar_session

    mgr.set_current_schema('foo')
    foo_session_2 = mgr.session()

    mgr.set_current_schema('bar')
    bar_session_2 = mgr.session()

    assert foo_session is foo_session_2
    assert bar_session is bar_session_2

    mgr.dispose()


def test_orm_scenario(postgres_dsn: str, redis_url: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class App(Framework):
        pass

    class Document(Base):
        __tablename__ = 'documents'

        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str]

    class DocumentCollection:

        def __init__(self, session: Session) -> None:
            self.session = session

        def query(self) -> Query[Document]:
            return self.session.query(Document)

        def all(self) -> list[Document]:
            return self.query().all()

        def get(self, id: int) -> Document | None:
            return self.query().filter(Document.id == id).first()

        def add(self, title: str) -> Document:
            document = Document(title=title)
            self.session.add(document)
            self.session.flush()

            return document

    @App.path(model=DocumentCollection, path='documents')
    def get_documents(app: App) -> DocumentCollection:
        return DocumentCollection(app.session())

    @App.json(model=DocumentCollection)
    def documents_default(
        self: DocumentCollection,
        request: CoreRequest
    ) -> JSON_ro:
        return {str(d.id): d.title for d in self.all()}

    @App.json(model=DocumentCollection, name='add', request_method='POST')
    def documents_add(self: DocumentCollection, request: CoreRequest) -> None:
        self.add(title=request.params.get('title'))  # type: ignore[arg-type]

    @App.json(model=DocumentCollection, name='error')
    def documents_error(
        self: DocumentCollection,
        request: DocumentCollection
    ) -> None:
        # tries to create a document that should not be created since the
        # request as a whole fails
        self.add('error')

        raise HTTPUnauthorized()

    # this is required for the transactions to actually work, usually this
    # would be onegov.server's job
    scan_morepath_modules(App)

    app = App()
    app.namespace = 'municipalities'
    app.configure_application(dsn=postgres_dsn, base=Base, redis_url=redis_url)
    # remove ORMBase
    app.session_manager.bases.pop()

    c = Client(app)

    # let's try to add some documents to new york
    app.set_application_id('municipalities/new-york')

    assert c.get('/documents').json == {}
    c.post('/documents/add', {'title': 'Welcome to the big apple!'})

    assert c.get('/documents').json == {
        '1': "Welcome to the big apple!"
    }

    # after that, we switch to chicago, where a different set of documents
    # should exist
    app.set_application_id('municipalities/chicago')

    assert c.get('/documents').json == {}
    c.post('/documents/add', {'title': 'Welcome to the windy city!'})

    assert c.get('/documents').json == {
        '1': "Welcome to the windy city!"
    }

    # finally, let's see if the transaction is rolled back if there's an
    # error during the course of the request
    c.get('/documents/error', expect_errors=True)
    assert c.get('/documents').json == {
        '1': "Welcome to the windy city!"
    }

    app.session_manager.dispose()


def test_i18n_with_request(postgres_dsn: str, redis_url: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class App(Framework):
        pass

    class Document(Base):
        __tablename__ = 'documents'

        id: Mapped[int] = mapped_column(primary_key=True)

        title_translations: Mapped[Mapping[str, str]] = mapped_column(HSTORE)
        title = translation_hybrid(title_translations)
        html_translations: Mapped[Mapping[str, str]] = mapped_column(HSTORE)
        html = translation_markup_hybrid(html_translations)

    @App.path(model=Document, path='document')
    def get_document(app: App) -> Document:
        return app.session().query(Document).first() or Document(id=1)

    @App.json(model=Document)
    def view_document(self: Document, request: CoreRequest) -> JSON_ro:
        # ensure we get the correct type
        assert not self.html or isinstance(self.html, Markup)
        return {'title': self.title, 'html': self.html}

    @App.json(model=Document, request_method='PUT')
    def put_document(self: Document, request: CoreRequest) -> None:
        self.title = request.params.get('title')  # type: ignore[assignment]
        if 'unsafe' in request.params:
            self.html = request.params['unsafe']  # type: ignore[assignment]
        elif 'markup' in request.params:
            self.html = Markup(request.params['markup'])
        app.session().merge(self)

    @App.setting(section='i18n', name='default_locale')
    def get_i18n_default_locale() -> str:
        return 'de_CH'

    scan_morepath_modules(App)

    app = App()
    app.namespace = 'municipalities'
    app.configure_application(dsn=postgres_dsn, base=Base, redis_url=redis_url)
    # remove ORMBase
    app.session_manager.bases.pop()
    app.set_application_id('municipalities/new-york')
    app.locales = {'de_CH', 'en_US'}

    c = Client(app)
    c.put('/document?title=Dokument&unsafe=<script>')
    assert c.get('/document').json == {
        'title': 'Dokument',
        'html': '&lt;script&gt;'
    }

    c.set_cookie('locale', 'en_US')
    c.put('/document?title=Document&markup=<b>bold</b>')
    assert c.get('/document').json == {
        'title': 'Document',
        'html': '<b>bold</b>'
    }

    c.set_cookie('locale', '')
    assert c.get('/document').json == {
        'title': 'Dokument',
        'html': '&lt;script&gt;'
    }

    app.session_manager.dispose()


def test_json_type(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'

        id: Mapped[int] = mapped_column(primary_key=True)
        data: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test(id=1, data=None)
    session.add(test)
    transaction.commit()

    # our json type automatically coreces None to an empty dict
    assert session.query(Test).filter(Test.id == 1).one().data == {}
    assert session.execute(text(
        'SELECT data::text from test')).scalar() == '{}'

    test = Test(id=2, data={'foo': 'bar'})
    session.add(test)
    transaction.commit()

    assert session.query(Test).filter(Test.id == 2).one().data == {
        'foo': 'bar'
    }

    test = session.query(Test).filter(Test.id == 2).one()
    assert test.data is not None
    test.data['foo'] = 'rab'
    transaction.commit()

    assert session.query(Test).filter(Test.id == 2).one().data == {
        'foo': 'rab'
    }

    test = Test(id=3, data={})
    session.add(test)
    transaction.commit()

    assert session.query(Test).filter(Test.id == 3).one().data == {}

    mgr.dispose()


def test_session_manager_sharing(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'
        id: Mapped[int] = mapped_column(primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    test = Test(id=1)

    # session_manager is a weakref proxy so we need to go through some hoops
    # to get the actual instance for a proper identity test
    assert test.session_manager.__repr__.__self__ is mgr  # type: ignore[attr-defined]

    session = mgr.session()
    session.add(test)
    transaction.commit()

    assert session.query(Test).one().session_manager.__repr__.__self__ is mgr  # type: ignore[attr-defined]
    mgr.dispose()


def test_session_manager_i18n(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'
        id: Mapped[int] = mapped_column(primary_key=True)

        text_translations: Mapped[Mapping[str, str] | None] = mapped_column(
            HSTORE
        )
        text = translation_hybrid(text_translations)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')
    mgr.set_locale(default_locale='en_us', current_locale='en_us')

    test = Test(id=1, text='no')
    assert test.text == 'no'

    mgr.set_locale(default_locale='en_us', current_locale='de_ch')
    assert test.text == 'no'

    test.text_translations['de_ch'] = 'nein'  # type: ignore[index]
    assert test.text == 'nein'

    mgr.set_locale(default_locale='en_us', current_locale='en_us')
    assert test.text == 'no'

    session = mgr.session()
    session.add(test)
    transaction.commit()

    test = session.query(Test).one()
    assert test.text == 'no'

    mgr.set_locale(default_locale='en_us', current_locale='de_ch')
    assert test.text == 'nein'

    # make sure the locale is shared with the query as well
    assert mgr.session().query(Test).order_by(Test.text).first()

    assert mgr.session().query(Test).filter_by(text='nein').first()
    assert not mgr.session().query(Test).filter_by(text='no').first()

    mgr.set_locale(default_locale='en_us', current_locale='en_us')

    assert not mgr.session().query(Test).filter_by(text='nein').first()
    assert mgr.session().query(Test).filter_by(text='no').first()

    # make sure session managers are independent
    sec = SessionManager(postgres_dsn, Base)
    sec.set_current_schema('testing')

    mgr.set_locale(default_locale='en_us', current_locale='en_us')
    sec.set_locale(default_locale='en_us', current_locale='de_ch')

    sec.activate()
    assert sec.session().query(Test).one().text == 'nein'

    mgr.activate()
    assert mgr.session().query(Test).one().text == 'no'

    sec.activate()
    assert sec.session().query(Test).filter_by(text='nein').first()

    mgr.activate()
    assert mgr.session().query(Test).filter_by(text='no').first()

    sec.dispose()
    mgr.dispose()


def test_uuid_type(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'

        id: Mapped[uuid.UUID] = mapped_column(
            primary_key=True,
            default=uuid.uuid4
        )

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test()
    session.add(test)
    transaction.commit()

    assert isinstance(session.query(Test).one().id, uuid.UUID)

    mgr.dispose()


def test_lowercase_text(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'

        id = mapped_column(LowercaseText, primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test()
    test.id = 'Foobar'
    session.add(test)
    transaction.commit()

    assert session.query(Test).one().id == 'foobar'
    assert session.query(Test).filter(Test.id == 'Foobar').one().id == 'foobar'
    assert session.query(Test).filter(Test.id == 'foobar').one().id == 'foobar'

    mgr.dispose()


def test_markup_text(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'

        id: Mapped[int] = mapped_column(primary_key=True)
        html: Mapped[Markup | None] = mapped_column(MarkupText)

    class Nbsp:
        def __html__(self) -> str:
            return '&nbsp;'

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test1 = Test()
    test1.id = 1
    test1.html = '<script>unvetted</script>'  # type: ignore[assignment]
    session.add(test1)
    test2 = Test()
    test2.id = 2
    test2.html = Markup('<b>this is fine</b>')
    session.add(test2)
    # NOTE: This use-case will technically not pass type checking
    #       but it still should work correctly
    test3 = Test()
    test3.id = 3
    test3.html = Nbsp()  # type: ignore[assignment]
    session.add(test3)
    transaction.commit()

    test1 = session.get(Test, 1)  # type: ignore[assignment]
    assert test1.html == Markup('&lt;script&gt;unvetted&lt;/script&gt;')
    test2 = session.get(Test, 2)  # type: ignore[assignment]
    assert test2.html == Markup('<b>this is fine</b>')
    test3 = session.get(Test, 3)  # type: ignore[assignment]
    assert test3.html == Markup('&nbsp;')

    mgr.dispose()


def test_utc_datetime_naive(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'

        id: Mapped[int] = mapped_column(primary_key=True)
        date: Mapped[datetime | None] = mapped_column(UTCDateTime)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    with pytest.raises(sqlalchemy.exc.StatementError):
        test = Test(date=datetime.now())
        session.add(test)
        session.flush()

    mgr.dispose()


def test_utc_datetime_aware(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'

        id: Mapped[int] = mapped_column(primary_key=True)
        date: Mapped[datetime | None] = mapped_column(UTCDateTime)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    tz = timezone('Europe/Zurich')
    date = datetime(2015, 3, 5, 12, 0).replace(tzinfo=tz)
    test = Test(date=date)
    session.add(test)
    session.flush()
    transaction.commit()

    assert session.query(Test).one().date == date

    mgr.dispose()


def test_timestamp_mixin(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base, TimestampMixin):
        __tablename__ = 'test'

        id: Mapped[int] = mapped_column(primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test()
    session.add(test)
    session.flush()
    transaction.commit()

    now = utcnow()

    assert session.query(Test).one().created.year == now.year
    assert session.query(Test).one().created.month == now.month
    assert session.query(Test).one().created.day == now.day

    assert session.query(Test).one().modified is None

    test = session.query(Test).one()
    test.id = 2
    session.flush()

    assert session.query(Test).one().modified.year == now.year  # type: ignore[union-attr]
    assert session.query(Test).one().modified.month == now.month  # type: ignore[union-attr]
    assert session.query(Test).one().modified.day == now.day  # type: ignore[union-attr]

    mgr.dispose()


def test_content_mixin(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry(type_annotation_map={dict[str, Any]: JSON})

    class Test(Base, ContentMixin):
        __tablename__ = 'test'

        id: Mapped[int] = mapped_column(primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test(meta={'filename': 'rtfm'}, content={'text': 'RTFM'})
    session.add(test)
    session.flush()
    transaction.commit()

    assert session.query(Test).one().meta == {'filename': 'rtfm'}
    assert session.query(Test).one().content == {'text': 'RTFM'}

    mgr.dispose()


def test_extensions_schema(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Data(Base):
        __tablename__ = 'data'

        id: Mapped[int] = mapped_column(primary_key=True)
        data: Mapped[dict[str, Any] | None] = mapped_column(
            MutableDict.as_mutable(HSTORE)
        )

    mgr = SessionManager(postgres_dsn, Base)

    for ix, schema in enumerate(('foo', 'bar')):
        mgr.set_current_schema(schema)

        obj = Data()
        obj.data = {}
        obj.data['index'] = str(ix)
        obj.data['schema'] = schema

        mgr.session().add(obj)
        mgr.session().flush()

        transaction.commit()

    for ix, schema in enumerate(('foo', 'bar')):
        mgr.set_current_schema(schema)

        obj = mgr.session().query(Data).one()
        assert obj.data is not None
        assert obj.data['index'] == str(ix)
        assert obj.data['schema'] == schema

    assert mgr.created_extensions == {'btree_gist', 'hstore', 'unaccent'}


def test_serialization_failure(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Data(Base):
        __tablename__ = 'data'
        id: Mapped[int] = mapped_column(primary_key=True)

    class MayFailThread(Thread):

        def __init__(self, dsn: str, base: type[Base], schema: str) -> None:
            Thread.__init__(self)
            self.dsn = dsn
            self.base = base
            self.schema = schema
            self.exception: Exception | None

        def run(self) -> None:
            mgr = SessionManager(self.dsn, self.base)
            mgr.set_current_schema(self.schema)

            session = mgr.session()

            session.add(Data())
            session.query(Data).delete('fetch')

            time.sleep(0.1)

            try:
                transaction.commit()
            except Exception as e:
                self.exception = e
            else:
                self.exception = None

    # make sure the schema exists already, its creation is not threadsafe
    SessionManager(postgres_dsn, Base).set_current_schema('foo')

    threads = [
        MayFailThread(postgres_dsn, Base, 'foo'),
        MayFailThread(postgres_dsn, Base, 'foo')
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    exceptions = [t.exception for t in threads]

    # one will have failed with a rollback error
    rollbacks = [e for e in exceptions if e]
    assert len(rollbacks) == 1
    assert isinstance(rollbacks[0].orig, TransactionRollbackError)  # type: ignore[attr-defined]


@pytest.mark.flaky(reruns=3, only_rerun=None)
@pytest.mark.parametrize("number_of_retries", range(1, 10))
def test_application_retries(
    number_of_retries: int,
    postgres_dsn: str,
    redis_url: str
) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Record(Base):
        __tablename__ = 'records'
        id: Mapped[int] = mapped_column(primary_key=True)

    class App(Framework):
        pass

    @App.path(path='/foo/{id}/{uid}')
    class Document:
        def __init__(self, id: str, uid: str) -> None:
            self.id = id
            self.uid = uid

    @App.path(path='/')
    class Root:
        pass

    @App.view(model=Root, name='init')
    def init_schema(self: Root, request: CoreRequest) -> None:
        pass  # the schema is initialized by the application

    @App.view(model=Root, name='login')
    def login(self: Root, request: CoreRequest) -> None:
        @request.after
        def remember(response: Response) -> None:
            identity = morepath.Identity(
                uid='1',
                userid='admin',
                groupids=frozenset({'admins'}),
                role='editor',
                application_id=request.app.application_id
            )

            request.app.remember_identity(response, request, identity)

    @App.view(model=Document, permission=Private)
    def provoke_serialization_failure(
        self: Document,
        request: CoreRequest
    ) -> None:

        session = request.app.session()
        session.add(Record())
        session.query(Record).delete('fetch')

        # we sleep in small increments, as this might increase the chance of
        # these threads actually running concurrently (depending on postgres
        # latencies we might otherwise be scheduled serially)
        for _ in range(0, 10):
            time.sleep(0.01)

    @App.view(model=OperationalError)
    def operational_error_handler(
        self: OperationalError,
        request: CoreRequest
    ) -> None:

        if not hasattr(self, 'orig'):
            return

        if not isinstance(self.orig, TransactionRollbackError):
            return

        raise HTTPConflict()

    @App.setting(section='transaction', name='attempts')
    def get_retry_attempts() -> int:
        return number_of_retries

    scan_morepath_modules(App)

    app = App()
    app.namespace = 'municipalities'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        identity_secure=False,
        redis_url=redis_url
    )
    # remove ORMBase
    app.session_manager.bases.pop()

    # make sure the schema exists already
    app.set_application_id('municipalities/new-york')
    Client(app).get('/init')

    class RequestThread(Thread):
        def __init__(self, app: App, path: str) -> None:
            Thread.__init__(self)
            self.app = app
            self.path = path
            self.exception: Exception | None

        def run(self) -> None:
            try:
                client = Client(self.app)
                client.get('/login')
                self.response = client.get(self.path, expect_errors=True)
            except Exception as e:
                self.exception = e
            else:
                self.exception = None

    # the number of threads that succeed are the number of retries - 1
    threads = [
        RequestThread(app, '/foo/bar/baz')
        for i in range(number_of_retries + 1)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # no exceptions should happen, we want proper http return codes
    assert len([t.exception for t in threads if t.exception]) == 0
    assert len([t.response for t in threads if t.response]) == len(threads)

    # all responses should be okay, but for one which gets a 409 Conflict
    status_codes = [t.response.status_code for t in threads]
    assert sum(1 for c in status_codes if c == 200) == len(threads) - 1
    assert sum(1 for c in status_codes if c == 409) == 1


def test_orm_signals_independence(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'
        id: Mapped[int] = mapped_column(primary_key=True)

    m1 = SessionManager(postgres_dsn, Base)
    m2 = SessionManager(postgres_dsn, Base)

    m1.set_current_schema('foo')
    m2.set_current_schema('foo')

    m1_inserted, m2_inserted = [], []

    @m1.on_insert.connect
    def on_m1_insert(schema: str, obj: object) -> None:
        m1_inserted.append((obj, schema))

    @m2.on_insert.connect
    def on_m2_insert(schema: str, obj: object) -> None:
        m2_inserted.append((obj, schema))

    m1.session().add(Document())
    m1.session().flush()

    assert len(m1_inserted) == 1
    assert len(m2_inserted) == 0

    m2.session().add(Document())
    m2.session().flush()

    assert len(m1_inserted) == 1
    assert len(m2_inserted) == 1


def test_orm_signals_schema(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'
        id: Mapped[int] = mapped_column(primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)

    inserted = []

    @mgr.on_insert.connect
    def on_insert(schema: str, obj: object) -> None:
        inserted.append((obj, schema))

    mgr.set_current_schema('foo')
    session = mgr.session()
    session.add(Document())
    session.flush()

    assert inserted[0][1] == 'foo'

    mgr.set_current_schema('bar')
    session.add(Document())
    session.flush()

    assert inserted[1][1] == 'bar'


def test_scoped_signals(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'
        id: Mapped[int] = mapped_column(primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)

    inserted = []

    @mgr.on_insert.connect_via('bar')
    def on_insert(schema: str, obj: object) -> None:
        inserted.append((obj, schema))

    mgr.set_current_schema('foo')
    mgr.session().add(Document())
    mgr.session().flush()

    assert len(inserted) == 0

    mgr.set_current_schema('bar')
    mgr.session().add(Document())
    mgr.session().flush()

    assert len(inserted) == 1


def test_orm_signals_data_flushed(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'
        id: Mapped[int] = mapped_column(primary_key=True)
        body: Mapped[str | None] = mapped_column(default=lambda: 'asdf')

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    inserted = []

    @mgr.on_insert.connect
    def on_insert(schema: str, obj: Document) -> None:
        inserted.append((obj, schema))

    mgr.session().add(Document())
    mgr.session().flush()

    assert inserted[0][0].id > 0
    assert inserted[0][0].body == 'asdf'


def test_pickle_model(postgres_dsn: str) -> None:

    # pickling doesn't work with inline classes, so we need to use the
    # PicklePage class defined in thos module
    from onegov.core.orm import Base
    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    # pickling will fail if the session_manager is still attached
    page = PicklePage(name='foobar', title='Foobar')
    assert page.session_manager.__repr__.__self__ is mgr  # type: ignore[attr-defined]

    # this is why we automatically remove it internally when we pickle
    page = pickle.loads(pickle.dumps(page))

    assert page.name == 'foobar'
    assert page.title == 'Foobar'

    # make sure the session manager is set after restore
    page = mgr.session().merge(page)
    assert page.session_manager.__repr__.__self__ is mgr


def test_orm_signals(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'
        id: Mapped[int] = mapped_column(primary_key=True)
        body: Mapped[str | None]

    class Comment(Base):
        __tablename__ = 'comments'
        id: Mapped[int] = mapped_column(primary_key=True)
        document_id: Mapped[int] = mapped_column(primary_key=True)
        body: Mapped[str | None]

    mgr = SessionManager(postgres_dsn, Base)

    inserted: list[tuple[Document | Comment, str]] = []
    updated: list[tuple[Document | Comment, str]] = []
    deleted: list[tuple[Document | Comment, str]] = []

    @mgr.on_insert.connect
    def on_insert(schema: str, obj: Document | Comment) -> None:
        inserted.append((obj, schema))

    @mgr.on_update.connect
    def on_update(schema: str, obj: Document | Comment) -> None:
        updated.append((obj, schema))

    @mgr.on_delete.connect
    def on_delete(
        schema: str,
        session: Session,
        obj: Document | Comment
    ) -> None:
        deleted.append((obj, schema))

    mgr.set_current_schema('foo')
    session = mgr.session()

    # test on_insert
    session.add(Document(id=1))
    session.add(Comment(id=1, document_id=1))
    assert len(inserted) == 0

    session.flush()
    assert len(inserted) == 2

    # the event order is random
    doc = hasattr(inserted[0][0], 'document_id') and inserted[1] or inserted[0]
    com = hasattr(inserted[0][0], 'document_id') and inserted[0] or inserted[1]

    assert doc[0].id == 1
    assert doc[1] == 'foo'

    assert com[0].id == 1
    assert com[0].document_id == 1  # type: ignore[union-attr]
    assert com[1] == 'foo'

    transaction.commit()
    assert len(inserted) == 2

    # test on_update
    document = session.query(Document).filter(Document.id == 1).one()
    document.id = 3
    assert len(updated) == 0

    session.flush()
    assert len(updated) == 1
    assert updated[0][0].id == 3
    assert updated[0][1] == 'foo'

    transaction.commit()
    assert len(updated) == 1

    # test on_delete
    session.delete(document)
    assert len(deleted) == 0

    session.flush()
    assert len(deleted) == 1

    session.flush()
    assert len(deleted) == 1
    assert deleted[0][0].id == 3
    assert deleted[0][1] == 'foo'

    # test on_update with bulk update
    del inserted[:]
    del updated[:]
    del deleted[:]

    session.add(Document(id=1))
    session.add(Document(id=2))
    session.flush()

    assert len(inserted) == 2

    session.query(Document).update({'body': 'hello world'})
    session.expire_all()
    assert len(updated) == 2
    assert updated[0][0].body == 'hello world'
    assert updated[0][1] == 'foo'
    assert updated[1][0].body == 'hello world'
    assert updated[1][1] == 'foo'

    transaction.commit()

    # test on_delete with bulk delete
    session.add(Comment(id=1, document_id=2, body='foo'))
    session.add(Comment(id=2, document_id=2, body='bar'))
    transaction.commit()
    session.query(Comment).filter(Comment.document_id == 2).delete()
    assert len(deleted) == 2
    assert deleted[0][0].id == 1
    assert deleted[0][0].document_id == 2  # type: ignore[union-attr]
    assert deleted[0][1] == 'foo'
    assert deleted[1][0].id == 2
    assert deleted[1][0].document_id == 2  # type: ignore[union-attr]
    assert deleted[1][1] == 'foo'

    # ensure these objects are detached
    assert inspect(deleted[0][0]).detached  # type: ignore[attr-defined]
    assert inspect(deleted[1][0]).detached  # type: ignore[attr-defined]

    # and stay deleted
    transaction.commit()
    assert session.query(Comment).filter(Comment.document_id == 2).all() == []


def test_get_polymorphic_class() -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Plain(Base):
        __tablename__ = 'plain'
        id: Mapped[int] = mapped_column(primary_key=True)

    class PolyBase(Base):
        __tablename__ = 'polymorphic'

        id: Mapped[int] = mapped_column(primary_key=True)
        type: Mapped[str | None]

        __mapper_args__ = {
            'polymorphic_on': 'type'
        }

    class ChildA(PolyBase):
        __mapper_args__ = {'polymorphic_identity': 'A'}

    class ChildB(PolyBase):
        __mapper_args__ = {'polymorphic_identity': 'B'}

    assert Plain.get_polymorphic_class('A', None) is None
    assert Plain.get_polymorphic_class('B', None) is None
    assert Plain.get_polymorphic_class('C', None) is None

    assert Plain.get_polymorphic_class('A', 1) == 1
    assert Plain.get_polymorphic_class('B', 2) == 2
    assert Plain.get_polymorphic_class('C', 3) == 3

    assert PolyBase.get_polymorphic_class('A') is ChildA
    assert ChildA.get_polymorphic_class('A') is ChildA
    assert ChildB.get_polymorphic_class('A') is ChildA  # type: ignore[comparison-overlap]

    assert PolyBase.get_polymorphic_class('B') is ChildB
    assert ChildA.get_polymorphic_class('B') is ChildB  # type: ignore[comparison-overlap]
    assert ChildB.get_polymorphic_class('B') is ChildB

    assert PolyBase.get_polymorphic_class('C', None) is None
    assert ChildA.get_polymorphic_class('C', None) is None
    assert ChildB.get_polymorphic_class('C', None) is None

    with pytest.raises(AssertionError) as assertion_info:
        PolyBase.get_polymorphic_class('C')

    assert "No such polymorphic_identity: C" in str(assertion_info.value)


def test_dict_properties(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Site(Base):
        __tablename__ = 'sites'
        id: Mapped[int] = mapped_column(primary_key=True)
        users: Mapped[dict[str, Any]] = mapped_column(
            JSON,
            default=dict
        )
        group: dict_property[str | None]
        group = dict_property('users', value_type=str)
        names: dict_property[list[str]] = dict_property('users', default=list)
        html1 = dict_markup_property('users')
        html2 = dict_markup_property('users')

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    site = Site(id=1)
    assert site.names == []
    assert site.group is None
    site.names += ['foo', 'bar']
    site.group = 'test'
    site.html1 = '<script>unvetted</script>'
    site.html2 = Markup('<b>safe</b>')
    session.add(site)
    assert site.users == {
        'group': 'test',
        'names': ['foo', 'bar'],
        'html1': '&lt;script&gt;unvetted&lt;/script&gt;',
        'html2': '<b>safe</b>'
    }

    # try to query for a dict property
    group, names, html1, html2 = session.query(
        Site.group,
        Site.names,
        Site.html1,
        Site.html2
    ).one()
    assert group == 'test'
    assert names == ['foo', 'bar']
    assert isinstance(html1, Markup)
    assert html1 == Markup('&lt;script&gt;unvetted&lt;/script&gt;')
    assert html2 == Markup('<b>safe</b>')

    # try to filter by a dict property
    assert Site.names is not None
    query = session.query(Site).filter(Site.names.contains('foo'))
    query = query.filter(Site.group == 'test')
    assert query.one() == site


def test_content_properties(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry(type_annotation_map={dict[str, Any]: JSON})

    class Content(Base, ContentMixin):
        __tablename__ = 'content'
        id: Mapped[int] = mapped_column(primary_key=True)
        # different attribute name than key
        _type: dict_property[str | None] = meta_property('type')
        # explicitly set value_type
        name: dict_property[str | None] = content_property(value_type=str)
        # implicitly set value type from default
        value: dict_property[int] = meta_property('value', default=1)

        @name.inplace.setter
        def _set_name(self, value: str | None) -> None:
            self.content['name'] = value
            self.content['name2'] = value

        @name.inplace.deleter
        def _delete_name(self) -> None:
            del self.content['name']
            del self.content['name2']

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    assert Content.name is not None
    assert Content.name.hybrid.value_type is str
    assert Content.value is not None
    assert Content.value.hybrid.value_type is int

    content = Content(id=1)
    session.add(content)
    # NOTE: mypy incorrectly keeps content._type narrowed
    #       so we create a new name which remains unnarrowed
    content2 = content
    assert content._type is None
    assert content.name is None
    assert content.value == 1

    content._type = 'page'
    assert content._type == 'page'
    assert content.meta['type'] == 'page'
    del content._type
    assert content2._type is None

    content.name = 'foobar'
    assert content.name == 'foobar'
    assert content.content['name'] == 'foobar'
    assert content.content['name2'] == 'foobar'

    del content.name

    assert content2.name is None
    assert content.content == {}

    content.value = 2
    assert content.value == 2
    assert content.meta['value'] == 2
    del content.value
    assert content.value == 1

    content.meta = None  # type: ignore[assignment]
    assert content2._type is None
    assert content.value == 1
    content._type = 'Foobar'
    assert content._type == 'Foobar'

    with pytest.raises(AssertionError):
        content.invalid = meta_property('invalid', default=[])  # type: ignore[attr-defined]
    with pytest.raises(AssertionError):
        content.invalid = meta_property('invalid', default={})  # type: ignore[attr-defined]


def test_find_models() -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Mixin:
        pass

    class A(Base):
        __tablename__ = 'plain'
        id: Mapped[int] = mapped_column(primary_key=True)

    class B(Base, Mixin):
        __tablename__ = 'polymorphic'
        id: Mapped[int] = mapped_column(primary_key=True)

    results = list(find_models(Base, lambda cls: issubclass(cls, Mixin)))
    assert results == [B]

    results = list(find_models(Base, lambda cls: not issubclass(cls, Mixin)))
    assert results == [A]

    results = list(find_models(Base, lambda cls: True))
    assert results == [A, B]


def test_sqlalchemy_aggregate(postgres_dsn: str) -> None:

    called = 0

    def count_calls(fn: _F) -> _F:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal called
            called += 1
            return fn(*args, **kwargs)
        return wrapper  # type: ignore[return-value]

    from sqlalchemy_utils.aggregates import manager
    manager.construct_aggregate_queries = count_calls(  # type: ignore[method-assign]
        manager.construct_aggregate_queries)

    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Thread(Base):
        __tablename__ = 'thread'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str | None]

        @aggregated('comments', mapped_column(Integer))
        def comment_count(self) -> ColumnElement[int]:
            return func.count(text('1'))

        comments: Mapped[list[Comment]] = relationship(back_populates='thread')

    class Comment(Base):
        __tablename__ = 'comment'

        id: Mapped[int] = mapped_column(primary_key=True)
        content: Mapped[str | None]
        thread_id: Mapped[int | None] = mapped_column(ForeignKey(Thread.id))
        thread: Mapped[Thread | None] = relationship(back_populates='comments')

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    session = mgr.session()

    thread = Thread(name='SQLAlchemy development')
    thread.comments.append(Comment(content='Going good!'))
    thread.comments.append(Comment(content='Great new features!'))

    session.add(thread)

    transaction.commit()

    result = session.query(Thread).first()
    assert result is not None
    assert result.comment_count == 2

    # if this goes up, we need to remove our custom fix
    assert called == 1

    # make sure that bulk queries are prohibited on aggregated models
    with pytest.raises(AssertionError):
        session.query(Comment).delete()

    with pytest.raises(AssertionError):
        session.query(Comment).update({'content': 'foobar'})


def test_orm_cache(postgres_dsn: str, redis_url: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'

        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str | None]
        body: Mapped[str | None]

    if TYPE_CHECKING:
        class DocumentRow(NamedTuple):
            id: int
            title: str | None

    class App(Framework):

        @orm_cached(policy='on-table-change:documents')
        def documents(self) -> Query[DocumentRow]:
            return self.session().query(  # type: ignore[return-value]
                Document.id,
                Document.title
            )

        @orm_cached(policy='on-table-change:documents')
        def untitled_documents(self) -> list[DocumentRow]:
            return self.session().query(  # type: ignore[return-value]
                Document.id,
                Document.title
            ).filter(Document.title == None).all()

        @orm_cached(policy='on-table-change:documents')
        def first_document(self) -> DocumentRow | None:
            return self.session().query(  # type: ignore[return-value]
                Document.id,
                Document.title
            ).first()

        @orm_cached(policy=lambda o: o.title == 'Secret')  # type: ignore[attr-defined]
        def secret_document(self) -> int | None:
            return self.session().query(
                Document.id
            ).filter(Document.title == 'Secret').scalar()

    # this is required for the transactions to actually work, usually this
    # would be onegov.server's job
    scan_morepath_modules(App)

    app = App()
    app.namespace = 'foo'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    # remove ORMBase
    app.session_manager.bases.pop()
    app.set_application_id('foo/bar')

    # ensure that no results work
    app.clear_request_cache()
    assert app.documents == tuple()
    assert app.untitled_documents == []
    assert app.first_document is None
    assert app.secret_document is None

    assert app.request_cache == {
        'test_orm_cache.<locals>.App.documents': tuple(),
        'test_orm_cache.<locals>.App.first_document': None,
        'test_orm_cache.<locals>.App.secret_document': None,
        'test_orm_cache.<locals>.App.untitled_documents': []
    }

    ts1 = app.cache.get('test_orm_cache.<locals>.App.documents_ts')
    ts2 = app.cache.get('test_orm_cache.<locals>.App.first_document_ts')
    ts3 = app.cache.get('test_orm_cache.<locals>.App.secret_document_ts')
    ts4 = app.cache.get('test_orm_cache.<locals>.App.untitled_documents_ts')

    assert app.schema_cache == {
        'test_orm_cache.<locals>.App.documents': (ts1, tuple()),
        'test_orm_cache.<locals>.App.first_document': (ts2, None),
        'test_orm_cache.<locals>.App.secret_document': (ts3, None),
        'test_orm_cache.<locals>.App.untitled_documents': (ts4, [])
    }

    assert app.cache.get('test_orm_cache.<locals>.App.documents') == tuple()
    assert app.cache.get('test_orm_cache.<locals>.App.first_document') is None
    assert app.cache.get('test_orm_cache.<locals>.App.secret_document') is None
    assert app.cache.get(
        'test_orm_cache.<locals>.App.untitled_documents') == []

    # if we add a non-secret document all caches update except for the last one
    app.session().add(Document(id=1, title='Public', body='Lorem Ipsum'))
    transaction.commit()

    assert app.cache.get('test_orm_cache.<locals>.App.documents') is NO_VALUE
    assert app.cache.get(
        'test_orm_cache.<locals>.App.first_document') is NO_VALUE
    assert app.cache.get(
        'test_orm_cache.<locals>.App.untitled_documents') is NO_VALUE
    assert app.cache.get('test_orm_cache.<locals>.App.secret_document') is None
    assert app.cache.get(
        'test_orm_cache.<locals>.App.documents_ts') is NO_VALUE
    assert app.cache.get(
        'test_orm_cache.<locals>.App.first_document_ts') is NO_VALUE
    assert app.cache.get(
        'test_orm_cache.<locals>.App.untitled_documents_ts') is NO_VALUE
    assert app.cache.get(
        'test_orm_cache.<locals>.App.secret_document_ts') == ts3

    assert app.request_cache == {
        'test_orm_cache.<locals>.App.secret_document': None,
    }
    assert app.schema_cache == {
        'test_orm_cache.<locals>.App.secret_document': (ts3, None),
    }

    assert app.secret_document is None
    # NOTE: Undo mypy narrowing for app.first_document
    app2 = app
    assert app2.first_document is not None
    assert app2.first_document.title == 'Public'
    assert app.untitled_documents == []
    assert app.documents[0].title == 'Public'

    # the timestamps for the changed caches should update, but the one
    # that's still cached should stay the same
    assert app.cache.get('test_orm_cache.<locals>.App.documents_ts') > ts1  # type: ignore[operator]
    assert app.cache.get('test_orm_cache.<locals>.App.first_document_ts') > ts2  # type: ignore[operator]
    assert app.cache.get(
        'test_orm_cache.<locals>.App.secret_document_ts') == ts3
    assert app.cache.get(  # type: ignore[operator]
        'test_orm_cache.<locals>.App.untitled_documents_ts') > ts4

    # if we add a secret document all caches change
    app.session().add(Document(id=2, title='Secret', body='Geheim'))
    transaction.commit()

    assert app.request_cache == {}
    assert app.secret_document == 2
    assert app2.first_document.title == 'Public'
    assert app.untitled_documents == []
    assert len(app.documents) == 2


def test_orm_cache_flush(postgres_dsn: str, redis_url: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'

        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str | None]

    if TYPE_CHECKING:
        class DocumentRow(NamedTuple):
            title: str | None

    class App(Framework):

        @property
        def foo(self) -> Document:
            return self.session().query(Document).one()

        @orm_cached(policy='on-table-change:documents')
        def bar(self) -> DocumentRow:
            return self.session().query(Document.title).one()  # type: ignore[return-value]

    scan_morepath_modules(App)

    app = App()
    app.namespace = 'foo'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    # remove ORMBase
    app.session_manager.bases.pop()
    app.set_application_id('foo/bar')
    app.clear_request_cache()

    app.session().add(Document(id=1, title='Yo'))
    transaction.commit()

    # both instances get cached
    assert app.foo.title == 'Yo'
    assert app.bar.title == 'Yo'

    # one instance changes without an explicit flush
    app.foo.title = 'Sup'

    # accessing the bar instance *first* fetches it from the cache which at
    # this point would contain stale entries because we didn't flush explicitly
    # but thanks to our autoflush mechanism this doesn't happen
    assert app.session().dirty
    assert app.bar.title == 'Sup'
    assert app.foo.title == 'Sup'


def test_request_cache(postgres_dsn: str, redis_url: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'

        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str | None]
        body: Mapped[str | None]

    if TYPE_CHECKING:
        class DocumentRow(NamedTuple):
            id: int
            title: str | None

        class ExtendedRow(NamedTuple):
            id: int
            title: str | None
            body: str | None

    class App(Framework):

        @request_cached
        def untitled_documents(self) -> list[DocumentRow]:
            return self.session().query(  # type: ignore[return-value]
                Document.id,
                Document.title
            ).filter(Document.title == None).all()

        @request_cached
        def first_document(self) -> DocumentRow | None:
            return self.session().query(  # type: ignore[return-value]
                Document.id,
                Document.title
            ).first()

        @request_cached
        def secret_document(self) -> ExtendedRow | None:
            return self.session().query(  # type: ignore[return-value]
                Document.id,
                Document.title,
                Document.body
            ).filter(Document.title == 'Secret').first()

    # this is required for the transactions to actually work, usually this
    # would be onegov.server's job
    scan_morepath_modules(App)

    app = App()
    app.namespace = 'foo'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    # remove ORMBase
    app.session_manager.bases.pop()
    app.set_application_id('foo/bar')

    # ensure that no results work
    app.clear_request_cache()
    assert app.untitled_documents == []
    assert app.first_document is None
    assert app.secret_document is None

    assert app.request_cache == {
        'test_request_cache.<locals>.App.first_document': None,
        'test_request_cache.<locals>.App.secret_document': None,
        'test_request_cache.<locals>.App.untitled_documents': []
    }

    app.session().add(Document(id=1, title='Public', body='Lorem Ipsum'))
    app.session().add(Document(id=2, title='Secret', body='Geheim'))
    transaction.commit()
    # no influence on same request
    assert app.request_cache == {
        'test_request_cache.<locals>.App.first_document': None,
        'test_request_cache.<locals>.App.secret_document': None,
        'test_request_cache.<locals>.App.untitled_documents': []
    }
    assert app.untitled_documents == []
    assert app.first_document is None
    assert app.secret_document is None
    app.clear_request_cache()

    assert app.request_cache == {}
    # NOTE: Undo mypy type narrowing for app.secret_document
    app2 = app
    assert app2.secret_document is not None
    assert app2.secret_document.body == "Geheim"
    assert app2.first_document is not None
    assert app2.first_document.title == 'Public'
    assert app.untitled_documents == []

    # if we change something in a cached object it is reflected
    # in the next request
    secret_document = (
        app.session().query(Document)
        .filter(Document.title == 'Secret').one()
    )
    secret_document.title = None
    transaction.commit()

    # this is still in cache with the old title
    assert app2.secret_document.title == 'Secret'

    app.clear_request_cache()
    assert app.untitled_documents[0].title is None


def test_request_cache_flush(postgres_dsn: str, redis_url: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Document(Base):
        __tablename__ = 'documents'

        id: Mapped[int] = mapped_column(primary_key=True)
        title: Mapped[str | None]

    if TYPE_CHECKING:
        class DocumentRow(NamedTuple):
            title: str | None

    class App(Framework):

        @orm_cached(policy='on-table-change:documents')
        def foo(self) -> DocumentRow:
            return self.session().query(Document.title).one()  # type: ignore[return-value]

    scan_morepath_modules(App)

    app = App()
    app.namespace = 'foo'
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    # remove ORMBase
    app.session_manager.bases.pop()
    app.set_application_id('foo/bar')
    app.clear_request_cache()

    app.session().add(Document(id=1, title='Yo'))
    transaction.commit()

    # instance gets cached
    assert app.foo.title == 'Yo'

    # instance changes without an explicit flush
    doc = app.session().query(Document).one()
    doc.title = 'Sup'

    # accessing the instance *first* fetches it from the cache which at
    # this point would contain stale entries because we didn't flush explicitly
    # but thanks to our autoflush mechanism this doesn't happen
    assert app.session().dirty
    assert app.foo.title == 'Sup'


def test_associable_one_to_one(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Address(Base, Associable):
        __tablename__ = 'adresses'

        id: Mapped[int] = mapped_column(primary_key=True)
        town: Mapped[str]

    class Addressable:
        address = associated(Address, 'address', 'one-to-one')

    class Company(Base, Addressable):
        __tablename__ = 'companies'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    class Person(Base, Addressable):
        __tablename__ = 'people'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    session.add(Company(
        name='Seantis GmbH',
        address=Address(town='6004 Luzern')
    ))

    session.add(Person(
        name='Denis Krienbühl',
        address=Address(town='6343 Rotkreuz')
    ))

    seantis = session.query(Company).first()
    assert seantis is not None
    assert seantis.address is not None
    assert seantis.address.town == "6004 Luzern"

    denis = session.query(Person).first()
    assert denis is not None
    assert denis.address is not None
    assert denis.address.town == "6343 Rotkreuz"

    addresses = session.query(Address).all()
    assert addresses[0].links.count() == 1
    assert addresses[0].links.first().name == "Seantis GmbH"  # type: ignore[union-attr]
    assert len(addresses[0].linked_companies) == 1  # type: ignore[attr-defined]
    assert len(addresses[0].linked_people) == 0  # type: ignore[attr-defined]

    assert addresses[1].links.count() == 1
    assert addresses[1].links.first().name == "Denis Krienbühl"  # type: ignore[union-attr]
    assert len(addresses[1].linked_companies) == 0  # type: ignore[attr-defined]
    assert len(addresses[1].linked_people) == 1  # type: ignore[attr-defined]

    session.delete(denis)
    session.flush()

    assert session.query(Address).count() == 1

    session.delete(addresses[0])
    session.flush()

    assert session.query(Company).first()


def test_associable_one_to_many(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Address(Base, Associable):
        __tablename__ = 'adresses'

        id: Mapped[int] = mapped_column(primary_key=True)
        town: Mapped[str]

    class Addressable:
        addresses = associated(Address, 'addresses', 'one-to-many')

    class Company(Base, Addressable):
        __tablename__ = 'companies'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    class Person(Base, Addressable):
        __tablename__ = 'people'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    session.add(Company(
        name='Seantis GmbH',
        addresses=[Address(town='6004 Luzern')]
    ))

    session.add(Person(
        name='Denis Krienbühl',
        addresses=[Address(town='6343 Rotkreuz')]
    ))

    seantis = session.query(Company).first()
    assert seantis is not None
    assert seantis.addresses[0].town == "6004 Luzern"

    denis = session.query(Person).first()
    assert denis is not None
    assert denis.addresses[0].town == "6343 Rotkreuz"

    addresses = session.query(Address).all()

    assert addresses[0].links.count() == 1
    assert addresses[0].links.first().name == "Seantis GmbH"  # type: ignore[union-attr]
    assert len(addresses[0].linked_companies) == 1  # type: ignore[attr-defined]
    assert len(addresses[0].linked_people) == 0  # type: ignore[attr-defined]

    assert addresses[1].links.count() == 1
    assert addresses[1].links.first().name == "Denis Krienbühl"  # type: ignore[union-attr]
    assert len(addresses[1].linked_companies) == 0  # type: ignore[attr-defined]
    assert len(addresses[1].linked_people) == 1  # type: ignore[attr-defined]

    session.delete(denis)
    session.flush()

    assert session.query(Address).count() == 1


def test_associable_many_to_many(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Address(Base, Associable):
        __tablename__ = 'adresses'

        id: Mapped[int] = mapped_column(primary_key=True)
        town: Mapped[str]

    class Addressable:
        addresses = associated(Address, 'addresses', 'many-to-many')

    class Company(Base, Addressable):
        __tablename__ = 'companies'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    class Person(Base, Addressable):
        __tablename__ = 'people'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    session.add(Company(
        name='Seantis GmbH',
        addresses=[Address(town='6004 Luzern')]
    ))

    session.add(Person(
        name='Denis Krienbühl',
        addresses=session.query(Company).first().addresses  # type: ignore[union-attr]
    ))

    seantis = session.query(Company).first()
    assert seantis.addresses[0].town == "6004 Luzern"  # type: ignore[union-attr]

    denis = session.query(Person).first()
    assert denis.addresses[0].town == "6004 Luzern"  # type: ignore[union-attr]

    addresses = session.query(Address).all()
    assert addresses[0].links.count() == 2

    session.delete(denis)
    session.flush()

    assert session.query(Address).count() == 1
    assert addresses[0].links.count() == 1

    # orphans in many-to-many are fine
    session.delete(seantis)
    session.flush()
    assert session.query(Address).count() == 1
    assert addresses[0].links.count() == 0


def test_associable_multiple(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Address(Base, Associable):
        __tablename__ = 'adresses'

        id: Mapped[int] = mapped_column(primary_key=True)
        town: Mapped[str]

    class Person(Base, Associable):
        __tablename__ = 'people'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

        address = associated(Address, 'address', 'one-to-one')

    class Company(Base):
        __tablename__ = 'companies'

        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

        address = associated(
            Address, 'address', 'one-to-one', onupdate='CASCADE'
        )
        employee = associated(
            Person, 'employee', 'one-to-many', onupdate='CASCADE'
        )

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    session.add(Company(
        id=1,
        name='Engulf & Devour',
        address=Address(town='Ember'),
        employee=[
            Person(name='Alice', address=Address(town='Alicante')),
            Person(name='Bob', address=Address(town='Brigadoon'))
        ]
    ))

    company = session.query(Company).first()
    assert company is not None
    assert company.address is not None
    assert company.address.town == "Ember"
    assert {e.name: e.address.town for e in company.employee} == {  # type: ignore[union-attr]
        'Alice': 'Alicante', 'Bob': 'Brigadoon'
    }

    alice = session.query(Person).filter_by(name="Alice").one()
    assert alice is not None
    assert alice.address is not None
    assert alice.address.town == "Alicante"
    assert alice.linked_companies == [company]  # type: ignore[attr-defined]
    assert alice.links.count() == 1

    bob = session.query(Person).filter_by(name="Bob").one()
    assert bob is not None
    assert bob.address is not None
    assert bob.address.town == "Brigadoon"
    assert bob.linked_companies == [company]  # type: ignore[attr-defined]
    assert bob.links.count() == 1

    addresses = session.query(Address).all()
    assert session.query(Address).count() == 3

    assert addresses[0].links.count() == 1
    assert addresses[0].links.first().name == "Engulf & Devour"  # type: ignore[union-attr]
    assert len(addresses[0].linked_companies) == 1  # type: ignore[attr-defined]
    assert len(addresses[0].linked_people) == 0  # type: ignore[attr-defined]

    assert addresses[1].links.count() == 1
    assert addresses[1].links.first().name == "Alice"  # type: ignore[union-attr]
    assert len(addresses[1].linked_companies) == 0  # type: ignore[attr-defined]
    assert len(addresses[1].linked_people) == 1  # type: ignore[attr-defined]

    assert addresses[2].links.count() == 1
    assert addresses[2].links.first().name == "Bob"  # type: ignore[union-attr]
    assert len(addresses[2].linked_companies) == 0  # type: ignore[attr-defined]
    assert len(addresses[2].linked_people) == 1  # type: ignore[attr-defined]

    company.id = 2
    session.flush()

    assert alice.linked_companies[0].id == 2  # type: ignore[attr-defined]
    assert bob.linked_companies[0].id == 2  # type: ignore[attr-defined]
    assert company.address.linked_companies[0].id == 2  # type: ignore[attr-defined]

    session.delete(alice)
    session.flush()

    assert session.query(Address).count() == 2

    session.delete(addresses[2])
    session.flush()

    assert session.query(Company).first().address.town == 'Ember'  # type: ignore[union-attr]


def test_selectable_sql_query(session: Session) -> None:
    stmt = as_selectable("""
        SELECT
            table_name,         -- Text
            column_name,        -- Text
            CASE
                WHEN is_updatable = 'YES'
                    THEN TRUE
                ELSE
                    FALSE
            END as is_updatable -- Boolean
        FROM information_schema.columns
    """)

    columns = session.execute(
        select(stmt.c.column_name).where(
            and_(
                stmt.c.table_name == 'pg_group',
                stmt.c.is_updatable == True
            )
        ).order_by(stmt.c.column_name)
    ).tuples().all()

    assert columns == [('groname', ), ('grosysid', )]
    assert columns[0].column_name == 'groname'
    assert columns[1].column_name == 'grosysid'

    columns = session.execute(
        select(stmt.c.column_name).where(
            and_(
                stmt.c.table_name == 'pg_group',
                stmt.c.is_updatable == False
            )
        ).order_by(stmt.c.column_name)
    ).tuples().all()

    assert columns == [('grolist', )]
    assert columns[0].column_name == 'grolist'


def test_selectable_sql_query_with_array(session: Session) -> None:
    stmt = as_selectable("""
        SELECT
            table_name AS table,                    -- Text
            array_agg(column_name::text) AS columns -- ARRAY(Text)
        FROM information_schema.columns
        GROUP BY "table"
    """)

    query = session.execute(select(stmt.c.table, stmt.c.columns))
    table = next(query)

    assert isinstance(table.columns, list)
    assert len(table.columns) > 0


def test_selectable_sql_query_with_dots(session: Session) -> None:
    stmt = as_selectable("""
        SELECT
            column_name,                                     -- Text
            information_schema.columns.table_name,           -- Text
            information_schema.columns.column_name as column -- Text
        FROM information_schema.columns
    """)

    assert tuple(stmt.c.keys()) == ('column_name', 'table_name', 'column')


def test_i18n_translation_hybrid_independence(
    postgres_dsn: str,
    redis_url: str
) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class App(Framework):
        pass

    class Document(Base):
        __tablename__ = 'documents'

        id: Mapped[int] = mapped_column(primary_key=True)

        title_translations: Mapped[Mapping[str, str]] = mapped_column(HSTORE)
        title = translation_hybrid(title_translations)

    @App.path(model=Document, path='/document')
    def get_document(app: App) -> Document | None:
        return app.session().query(Document).first()

    @App.json(model=Document)
    def view_document(self: Document, request: CoreRequest) -> JSON_ro:
        assert self.session_manager is not None
        return {
            'title': self.title,
            'locale': self.session_manager.current_locale
        }

    scan_morepath_modules(App)

    freiburg = App()
    freiburg.namespace = 'app'
    freiburg.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    # remove ORMBase
    freiburg.session_manager.bases.pop()
    freiburg.set_application_id('app/freiburg')
    freiburg.locales = {'de_CH', 'fr_CH'}

    biel = App()
    biel.namespace = 'app'
    biel.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    # remove ORMBase
    biel.session_manager.bases.pop()
    biel.set_application_id('app/biel')
    biel.locales = {'de_CH', 'fr_CH'}

    for app in (freiburg, biel):
        app.session_manager.activate()
        app.session().add(Document(id=1, title_translations={
            'de_CH': 'Dokument',
            'fr_CH': 'Document'
        }))

    transaction.commit()

    c = Client(freiburg)
    c.set_cookie('locale', 'de_CH')

    assert c.get('/document').json == {
        'title': 'Dokument',
        'locale': 'de_CH'
    }

    c = Client(biel)
    c.set_cookie('locale', 'fr_CH')

    assert c.get('/document').json == {
        'title': 'Document',
        'locale': 'fr_CH'
    }

    c = Client(freiburg)
    c.set_cookie('locale', 'fr_CH')

    assert c.get('/document').json == {
        'title': 'Document',
        'locale': 'fr_CH'
    }

    c = Client(biel)
    c.set_cookie('locale', 'de_CH')

    assert c.get('/document').json == {
        'title': 'Dokument',
        'locale': 'de_CH'
    }


def test_unaccent_expression(postgres_dsn: str) -> None:
    class Base(DeclarativeBase, ModelBase):
        registry = registry()

    class Test(Base):
        __tablename__ = 'test'

        text: Mapped[str] = mapped_column(primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()
    session.add(Test(text='Schweiz'))
    session.add(Test(text='Deutschland'))
    session.add(Test(text='Österreich'))
    transaction.commit()

    query = session.query(Test).order_by(unaccent(Test.text))
    assert [r.text for r in query] == ['Deutschland', 'Österreich', 'Schweiz']


def test_postgres_timezone(postgres_dsn: str) -> None:
    """ We need to set the timezone when creating the test database for local
    development. Servers are configured having GMT as default timezone.
    This test will fail locally until we find the solution. """

    valid_timezones = ('UTC', 'GMT', 'Etc/UTC')

    class Base(DeclarativeBase, ModelBase):
        registry = registry()
    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')
    session = mgr.session()
    assert session.execute(
        text('show timezone;')
    ).scalar() in valid_timezones, """
    Run
        ALTER DATABASE onegov SET timezone TO 'UTC';
    to change the default timezone, then restart postgres service.
    """
