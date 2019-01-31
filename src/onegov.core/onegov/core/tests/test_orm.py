import morepath
import pytest
import pickle
import sqlalchemy
import time
import transaction
import uuid

from datetime import datetime
from dogpile.cache.api import NO_VALUE
from onegov.core.framework import Framework
from onegov.core.orm import (
    ModelBase, SessionManager, as_selectable, translation_hybrid, find_models
)
from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.abstract import Associable, associated
from onegov.core.orm.func import unaccent
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm import orm_cached
from onegov.core.orm.types import HSTORE, JSON, UTCDateTime, UUID
from onegov.core.orm.types import LowercaseText
from onegov.core.security import Private
from onegov.core.utils import scan_morepath_modules
from psycopg2.extensions import TransactionRollbackError
from pytz import timezone
from sqlalchemy import Column, Integer, Text, ForeignKey, func, select, and_
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import relationship
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlalchemy_utils import aggregated
from threading import Thread
from webob.exc import HTTPUnauthorized, HTTPConflict
from webtest import TestApp as Client


class PicklePage(AdjacencyList):
    __tablename__ = 'picklepages'


def test_is_valid_schema(postgres_dsn):
    mgr = SessionManager(postgres_dsn, None)
    assert not mgr.is_valid_schema('pg_test')
    assert not mgr.is_valid_schema('-- or 1=1')
    assert not mgr.is_valid_schema('0')
    assert not mgr.is_valid_schema('information_schema')
    assert not mgr.is_valid_schema('public')
    assert not mgr.is_valid_schema('my--schema')
    assert mgr.is_valid_schema('my_schema')
    assert mgr.is_valid_schema('my-schema')


def test_independent_sessions(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'document'
        id = Column(Integer, primary_key=True)

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


def test_independent_managers(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'document'
        id = Column(Integer, primary_key=True)

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
    one.session().info == {'schema': 'bar'}
    two.session().info == {'schema': 'foo'}

    one.dispose()
    two.dispose()


def test_create_schema(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'document'

        id = Column(Integer, primary_key=True)
        title = Column(Text)

    mgr = SessionManager(postgres_dsn, Base)

    # we need a schema to use the session manager and it can't be 'public'
    mgr.set_current_schema('testing')

    def existing_schemas():
        # DO NOT copy this query, it's insecure (which is fine in testing)
        return set(
            r['schema_name'] for r in mgr.engine.execute(
                'SELECT schema_name FROM information_schema.schemata'
            )
        )

    def schema_tables(schema):
        # DO NOT copy this query, it's insecure (which is fine in testing)
        return set(
            r['tablename'] for r in mgr.engine.execute((
                "SELECT tablename FROM pg_catalog.pg_tables "
                "WHERE schemaname = '{}'".format(schema)
            ))
        )

    assert 'testing' in existing_schemas()
    assert 'new' not in existing_schemas()

    mgr.ensure_schema_exists('new')

    assert 'new' in existing_schemas()
    assert 'document' in schema_tables('new')

    mgr.dispose()


def test_schema_bound_session(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text)

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


def test_session_scope(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

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


def test_orm_scenario(postgres_dsn, redis_url):
    # test a somewhat complete ORM scenario in which create and read data
    # for different applications
    Base = declarative_base(cls=ModelBase)

    class App(Framework):
        pass

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=False)

    class DocumentCollection(object):

        def __init__(self, session):
            self.session = session

        def query(self):
            return self.session.query(Document)

        def all(self):
            return self.query().all()

        def get(self, id):
            return self.query().filter(Document.id == id).first()

        def add(self, title):
            document = Document(title=title)
            self.session.add(document)
            self.session.flush()

            return document

    @App.path(model=DocumentCollection, path='documents')
    def get_documents(app):
        return DocumentCollection(app.session())

    @App.json(model=DocumentCollection)
    def documents_default(self, request):
        return {d.id: d.title for d in self.all()}

    @App.json(model=DocumentCollection, name='add', request_method='POST')
    def documents_add(self, request):
        self.add(title=request.params.get('title'))

    @App.json(model=DocumentCollection, name='error')
    def documents_error(self, request):
        # tries to create a document that should not be created since the
        # request as a whole fails
        self.add('error')

        raise HTTPUnauthorized()

    # this is required for the transactions to actually work, usually this
    # would be onegov.server's job
    scan_morepath_modules(App)

    app = App()
    app.configure_application(dsn=postgres_dsn, base=Base, redis_url=redis_url)
    app.namespace = 'municipalities'

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


def test_i18n_with_request(postgres_dsn, redis_url):
    Base = declarative_base(cls=ModelBase)

    class App(Framework):
        pass

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)

        title_translations = Column(HSTORE, nullable=False)
        title = translation_hybrid(title_translations)

    @App.path(model=Document, path='document')
    def get_document(app):
        return app.session().query(Document).first() or Document(id=1)

    @App.json(model=Document)
    def view_document(self, request):
        return {'title': self.title}

    @App.json(model=Document, request_method='PUT')
    def put_document(self, request):
        self.title = request.params.get('title')
        app.session().merge(self)

    @App.setting(section='i18n', name='default_locale')
    def get_i18n_default_locale():
        return 'de_CH'

    scan_morepath_modules(App)

    app = App()
    app.configure_application(dsn=postgres_dsn, base=Base, redis_url=redis_url)
    app.namespace = 'municipalities'
    app.set_application_id('municipalities/new-york')
    app.locales = ['de_CH', 'en_US']

    c = Client(app)
    c.put('/document?title=Dokument')
    assert c.get('/document').json == {'title': 'Dokument'}

    c.set_cookie('locale', 'en_US')
    c.put('/document?title=Document')
    assert c.get('/document').json == {'title': 'Document'}

    c.set_cookie('locale', '')
    assert c.get('/document').json == {'title': 'Dokument'}

    app.session_manager.dispose()


def test_json_type(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base):
        __tablename__ = 'test'

        id = Column(Integer, primary_key=True)
        data = Column(JSON, nullable=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test(id=1, data=None)
    session.add(test)
    transaction.commit()

    # our json type automatically coreces None to an empty dict
    assert session.query(Test).filter(Test.id == 1).one().data == {}
    assert session.execute('SELECT data::text from test').scalar() == '{}'

    test = Test(id=2, data={'foo': 'bar'})
    session.add(test)
    transaction.commit()

    assert session.query(Test).filter(Test.id == 2).one().data == {
        'foo': 'bar'
    }

    test = session.query(Test).filter(Test.id == 2).one()
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


def test_session_manager_sharing(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base):
        __tablename__ = 'test'
        id = Column(Integer, primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    test = Test(id=1)

    # session_manager is a weakref proxy so we need to go through some hoops
    # to get the actual instance for a proper identity test
    assert test.session_manager.__repr__.__self__ is mgr

    session = mgr.session()
    session.add(test)
    transaction.commit()

    assert session.query(Test).one().session_manager.__repr__.__self__ is mgr
    mgr.dispose()


def test_session_manager_i18n(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base):
        __tablename__ = 'test'
        id = Column(Integer, primary_key=True)

        text_translations = Column(HSTORE)
        text = translation_hybrid(text_translations)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')
    mgr.set_locale(default_locale='en_us', current_locale='en_us')

    test = Test(id=1, text='no')
    assert test.text == 'no'

    mgr.set_locale(default_locale='en_us', current_locale='de_ch')
    assert test.text == 'no'

    test.text_translations['de_ch'] = 'nein'
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


def test_uuid_type(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base):
        __tablename__ = 'test'

        id = Column(UUID, primary_key=True, default=uuid.uuid4)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test()
    session.add(test)
    transaction.commit()

    assert isinstance(session.query(Test).one().id, uuid.UUID)

    mgr.dispose()


def test_lowercase_text(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base):
        __tablename__ = 'test'

        id = Column(LowercaseText, primary_key=True)

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


def test_utc_datetime_naive(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base):
        __tablename__ = 'test'

        id = Column(Integer, primary_key=True)
        date = Column(UTCDateTime)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    with pytest.raises(sqlalchemy.exc.StatementError):
        test = Test(date=datetime.now())
        session.add(test)
        session.flush()

    mgr.dispose()


def test_utc_datetime_aware(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base):
        __tablename__ = 'test'

        id = Column(Integer, primary_key=True)
        date = Column(UTCDateTime)

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


def test_timestamp_mixin(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base, TimestampMixin):
        __tablename__ = 'test'

        id = Column(Integer, primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test()
    session.add(test)
    session.flush()
    transaction.commit()

    now = datetime.utcnow()

    assert session.query(Test).one().created.year == now.year
    assert session.query(Test).one().created.month == now.month
    assert session.query(Test).one().created.day == now.day

    assert session.query(Test).one().modified is None

    test = session.query(Test).one()
    test.id = 2
    session.flush()

    assert session.query(Test).one().modified.year == now.year
    assert session.query(Test).one().modified.month == now.month
    assert session.query(Test).one().modified.day == now.day

    mgr.dispose()


def test_content_mixin(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base, ContentMixin):
        __tablename__ = 'test'

        id = Column(Integer, primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    test = Test(meta={'filename': 'rtfm'}, content={'text': 'RTFM'})
    session.add(test)
    session.flush()
    transaction.commit()

    session.query(Test).one().meta == {'filename': 'rtfm'}
    session.query(Test).one().content == {'text': 'RTFM'}

    mgr.dispose()


def test_extensions_schema(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Data(Base):
        __tablename__ = 'data'

        id = Column(Integer, primary_key=True)
        data = Column(MutableDict.as_mutable(HSTORE))

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
        assert obj.data['index'] == str(ix)
        assert obj.data['schema'] == schema

    assert mgr.created_extensions == {'btree_gist', 'hstore', 'unaccent'}


def test_serialization_failure(postgres_dsn):

    Base = declarative_base(cls=ModelBase)

    class Data(Base):
        __tablename__ = 'data'
        id = Column(Integer, primary_key=True)

    class MayFailThread(Thread):

        def __init__(self, dsn, base, schema):
            Thread.__init__(self)
            self.dsn = dsn
            self.base = base
            self.schema = schema

        def run(self):
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

    [t.start() for t in threads]
    [t.join() for t in threads]

    exceptions = [t.exception for t in threads]

    # one will have failed with a rollback error
    rollbacks = [e for e in exceptions if e]
    assert len(rollbacks) == 1
    assert isinstance(rollbacks[0].orig, TransactionRollbackError)


@pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize("number_of_retries", range(1, 10))
def test_application_retries(postgres_dsn, number_of_retries, redis_url):

    Base = declarative_base(cls=ModelBase)

    class App(Framework):
        pass

    @App.path(path='/foo/{id}/{uid}')
    class Document(object):
        def __init__(self, id, uid):
            self.id = id
            self.uid = uid

    @App.path(path='/')
    class Root(object):
        pass

    class Record(Base):
        __tablename__ = 'records'
        id = Column(Integer, primary_key=True)

    @App.view(model=Root, name='init')
    def init_schema(self, request):
        pass  # the schema is initialized by the application

    @App.view(model=Root, name='login')
    def login(self, request):
        @request.after
        def remember(response):
            identity = morepath.Identity(
                userid='admin',
                groupid='admins',
                role='editor',
                application_id=request.app.application_id
            )

            request.app.remember_identity(response, request, identity)

    @App.view(model=Document, permission=Private)
    def provoke_serialization_failure(self, request):
        session = request.app.session()
        session.add(Record())
        session.query(Record).delete('fetch')

        # we sleep in small increments, as this might increase the chance of
        # these threads actually running concurrently (depending on postgres
        # latencies we might otherwise be scheduled serially)
        for _ in range(0, 10):
            time.sleep(0.01)

    @App.view(model=OperationalError)
    def operational_error_handler(self, request):
        if not hasattr(self, 'orig'):
            return

        if not isinstance(self.orig, TransactionRollbackError):
            return

        raise HTTPConflict()

    @App.setting(section='transaction', name='attempts')
    def get_retry_attempts():
        return number_of_retries

    scan_morepath_modules(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        identity_secure=False,
        redis_url=redis_url
    )
    app.namespace = 'municipalities'

    # make sure the schema exists already
    app.set_application_id('municipalities/new-york')
    Client(app).get('/init')

    class RequestThread(Thread):
        def __init__(self, app, path):
            Thread.__init__(self)
            self.app = app
            self.path = path

        def run(self):
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

    [t.start() for t in threads]
    [t.join() for t in threads]

    # no exceptions should happen, we want proper http return codes
    assert len([t.exception for t in threads if t.exception]) == 0
    assert len([t.response for t in threads if t.response]) == len(threads)

    # all responses should be okay, but for one which gets a 409 Conflict
    status_codes = [t.response.status_code for t in threads]
    assert sum(1 for c in status_codes if c == 200) == len(threads) - 1
    assert sum(1 for c in status_codes if c == 409) == 1


def test_orm_signals_independence(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'documents'
        id = Column(Integer, primary_key=True)

    m1 = SessionManager(postgres_dsn, Base)
    m2 = SessionManager(postgres_dsn, Base)

    m1.set_current_schema('foo')
    m2.set_current_schema('foo')

    m1_inserted, m2_inserted = [], []

    @m1.on_insert.connect
    def on_m1_insert(schema, obj):
        m1_inserted.append((obj, schema))

    @m2.on_insert.connect
    def on_m2_insert(schema, obj):
        m2_inserted.append((obj, schema))

    m1.session().add(Document())
    m1.session().flush()

    assert len(m1_inserted) == 1
    assert len(m2_inserted) == 0

    m2.session().add(Document())
    m2.session().flush()

    assert len(m1_inserted) == 1
    assert len(m2_inserted) == 1


def test_orm_signals_schema(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'documents'
        id = Column(Integer, primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)

    inserted = []

    @mgr.on_insert.connect
    def on_insert(schema, obj):
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


def test_scoped_signals(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'documents'
        id = Column(Integer, primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)

    inserted = []

    @mgr.on_insert.connect_via('bar')
    def on_insert(schema, obj):
        inserted.append((obj, schema))

    mgr.set_current_schema('foo')
    mgr.session().add(Document())
    mgr.session().flush()

    assert len(inserted) == 0

    mgr.set_current_schema('bar')
    mgr.session().add(Document())
    mgr.session().flush()

    assert len(inserted) == 1


def test_orm_signals_data_flushed(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'documents'
        id = Column(Integer, primary_key=True)
        body = Column(Text, nullable=True, default=lambda: 'asdf')

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    inserted = []

    @mgr.on_insert.connect
    def on_insert(schema, obj):
        inserted.append((obj, schema))

    mgr.session().add(Document())
    mgr.session().flush()

    assert inserted[0][0].id > 0
    assert inserted[0][0].body == 'asdf'


def test_pickle_model(postgres_dsn):

    # pickling doesn't work with inline classes, so we need to use the
    # PicklePage class defined in thos module
    from onegov.core.orm import Base
    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    # pickling will fail if the session_manager is still attached
    page = PicklePage(name='foobar', title='Foobar')
    assert page.session_manager.__repr__.__self__ is mgr

    # this is why we automatically remove it internally when we pickle
    page = pickle.loads(pickle.dumps(page))

    assert page.name == 'foobar'
    assert page.title == 'Foobar'

    # make sure the session manager is set after restore
    page = mgr.session().merge(page)
    assert page.session_manager.__repr__.__self__ is mgr


def test_orm_signals(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Document(Base):
        __tablename__ = 'documents'
        id = Column(Integer, primary_key=True)
        body = Column(Text, nullable=True)

    class Comment(Base):
        __tablename__ = 'comments'
        id = Column(Integer, primary_key=True)
        document_id = Column(Integer, primary_key=True)
        body = Column(Text, nullable=True)

    mgr = SessionManager(postgres_dsn, Base)

    inserted, updated, deleted = [], [], []

    @mgr.on_insert.connect
    def on_insert(schema, obj):
        inserted.append((obj, schema))

    @mgr.on_update.connect
    def on_update(schema, obj):
        updated.append((obj, schema))

    @mgr.on_delete.connect
    def on_delete(schema, obj):
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
    assert com[0].document_id == 1
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
    assert deleted[0][0].document_id == 2
    assert deleted[0][1] == 'foo'
    assert deleted[1][0].id == 2
    assert deleted[1][0].document_id == 2
    assert deleted[1][1] == 'foo'

    # .. since those objects are never loaded, the body is not present
    assert not deleted[0][0].body
    assert not deleted[1][0].body


def test_get_polymorphic_class():
    Base = declarative_base(cls=ModelBase)

    class Plain(Base):
        __tablename__ = 'plain'
        id = Column(Integer, primary_key=True)

    class Base(Base):
        __tablename__ = 'polymorphic'

        id = Column(Integer, primary_key=True)
        type = Column(Text)

        __mapper_args__ = {
            'polymorphic_on': 'type'
        }

    class ChildA(Base):
        __mapper_args__ = {'polymorphic_identity': 'A'}

    class ChildB(Base):
        __mapper_args__ = {'polymorphic_identity': 'B'}

    assert Plain.get_polymorphic_class('A', None) is None
    assert Plain.get_polymorphic_class('B', None) is None
    assert Plain.get_polymorphic_class('C', None) is None

    assert Plain.get_polymorphic_class('A', 1) == 1
    assert Plain.get_polymorphic_class('B', 2) == 2
    assert Plain.get_polymorphic_class('C', 3) == 3

    assert Base.get_polymorphic_class('A') is ChildA
    assert ChildA.get_polymorphic_class('A') is ChildA
    assert ChildB.get_polymorphic_class('A') is ChildA

    assert Base.get_polymorphic_class('B') is ChildB
    assert ChildA.get_polymorphic_class('B') is ChildB
    assert ChildB.get_polymorphic_class('B') is ChildB

    assert Base.get_polymorphic_class('C', None) is None
    assert ChildA.get_polymorphic_class('C', None) is None
    assert ChildB.get_polymorphic_class('C', None) is None

    with pytest.raises(AssertionError) as assertion_info:
        Base.get_polymorphic_class('C')

    assert "No such polymorphic_identity: C" in str(assertion_info.value)


def test_dict_properties():

    class Site(object):
        users = {}
        names = dict_property('users')

    site = Site()
    site.names = ['foo', 'bar']

    assert site.users == {'names': ['foo', 'bar']}


def test_content_properties():

    class Content(object):
        meta = {}
        content = {}

        type = meta_property('type')
        name = content_property('name')
        value = meta_property('value', default=1)

        @name.setter
        def name(self, value):
            self.content['name'] = value
            self.content['name2'] = value

        @name.deleter
        def name(self):
            del self.content['name']
            del self.content['name2']

    content = Content()
    assert content.type is None
    assert content.name is None
    assert content.value == 1

    content.type = 'page'
    assert content.type == 'page'
    assert content.meta['type'] == 'page'
    del content.type
    assert content.type is None

    content.name = 'foobar'
    assert content.name == 'foobar'
    assert content.content['name'] == 'foobar'
    assert content.content['name2'] == 'foobar'

    del content.name

    assert content.name is None
    assert content.content == {}

    content.value = 2
    assert content.value == 2
    assert content.meta['value'] == 2
    del content.value
    assert content.value == 1

    content.meta = None
    assert content.type is None
    assert content.value == 1
    content.type = 'Foobar'
    assert content.type == 'Foobar'

    with pytest.raises(AssertionError):
        content.invalid = meta_property('invalid', default=[])
    with pytest.raises(AssertionError):
        content.invalid = meta_property('invalid', default={})


def test_find_models():

    Base = declarative_base(cls=ModelBase)

    class Mixin(object):
        pass

    class A(Base):
        __tablename__ = 'plain'
        id = Column(Integer, primary_key=True)

    class B(Base, Mixin):
        __tablename__ = 'polymorphic'
        id = Column(Integer, primary_key=True)

    results = list(find_models(Base, lambda cls: issubclass(cls, Mixin)))
    assert results == [B]

    results = list(find_models(Base, lambda cls: not issubclass(cls, Mixin)))
    assert results == [A]

    results = list(find_models(Base, lambda cls: True))
    assert results == [A, B]


def test_sqlalchemy_aggregate(postgres_dsn):

    called = 0

    def count_calls(fn):
        def wrapper(*args, **kwargs):
            nonlocal called
            called += 1
            return fn(*args, **kwargs)
        return wrapper

    from sqlalchemy_utils.aggregates import manager
    manager.construct_aggregate_queries = count_calls(
        manager.construct_aggregate_queries)

    Base = declarative_base(cls=ModelBase)

    class Thread(Base):
        __tablename__ = 'thread'

        id = Column(Integer, primary_key=True)
        name = Column(Text)

        @aggregated('comments', Column(Integer))
        def comment_count(self):
            return func.count('1')

        comments = relationship(
            'Comment',
            backref='thread'
        )

    class Comment(Base):
        __tablename__ = 'comment'

        id = Column(Integer, primary_key=True)
        content = Column(Text)
        thread_id = Column(Integer, ForeignKey(Thread.id))

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('foo')

    session = mgr.session()

    thread = Thread(name='SQLAlchemy development')
    thread.comments.append(Comment(content='Going good!'))
    thread.comments.append(Comment(content='Great new features!'))

    session.add(thread)

    transaction.commit()

    thread = session.query(Thread).first()
    assert thread.comment_count == 2

    # if this goes up, we need to remove our custom fix
    assert called == 1

    # make sure that bulk queries are prohibited on aggregated models
    with pytest.raises(AssertionError):
        session.query(Comment).delete()

    with pytest.raises(AssertionError):
        session.query(Comment).update({'content': 'foobar'})


def test_orm_cache(postgres_dsn, redis_url):

    Base = declarative_base(cls=ModelBase)

    class App(Framework):

        @orm_cached(policy='on-table-change:documents')
        def documents(self):
            return self.session().query(Document)

        @orm_cached(policy='on-table-change:documents')
        def untitled_documents(self):
            q = self.session().query(Document)
            q = q.with_entities(Document.id, Document.title)
            q = q.filter(Document.title == None)

            return q.all()

        @orm_cached(policy='on-table-change:documents')
        def first_document(self):
            q = self.session().query(Document)
            q = q.with_entities(Document.id, Document.title)

            return q.first()

        @orm_cached(policy=lambda o: o.title == 'Secret')
        def secret_document(self):
            q = self.session().query(Document)
            q = q.filter(Document.title == 'Secret')

            return q.first()

    # get dill to pickle the following inline class
    global Document

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=True)
        body = Column(Text, nullable=True)

    # this is required for the transactions to actually work, usually this
    # would be onegov.server's job
    scan_morepath_modules(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    app.namespace = 'foo'
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

    assert app.cache.get('test_orm_cache.<locals>.App.documents') == tuple()
    assert app.cache.get('test_orm_cache.<locals>.App.first_document') is None
    assert app.cache.get('test_orm_cache.<locals>.App.secret_document') is None
    assert app.cache.get('test_orm_cache.<locals>.App.untitled_documents')\
        == []

    # if we add a non-secret document all caches update except for the last one
    app.session().add(Document(id=1, title='Public', body='Lorem Ipsum'))
    transaction.commit()

    assert app.cache.get('test_orm_cache.<locals>.App.documents') is NO_VALUE
    assert app.cache.get('test_orm_cache.<locals>.App.first_document')\
        is NO_VALUE
    assert app.cache.get('test_orm_cache.<locals>.App.untitled_documents')\
        is NO_VALUE
    assert app.cache.get('test_orm_cache.<locals>.App.secret_document') is None

    assert app.request_cache == {
        'test_orm_cache.<locals>.App.secret_document': None,
    }

    assert app.secret_document is None
    assert app.first_document.title == 'Public'
    assert app.untitled_documents == []
    assert app.documents[0].body == 'Lorem Ipsum'

    # if we add a secret document all caches change
    app.session().add(Document(id=2, title='Secret', body='Geheim'))
    transaction.commit()

    assert app.request_cache == {}
    assert app.secret_document.body == "Geheim"
    assert app.first_document.title == 'Public'
    assert app.untitled_documents == []
    assert len(app.documents) == 2

    # if we change something in a cached object it is reflected
    app.secret_document.title = None
    transaction.commit()

    assert 'test_orm_cache.<locals>.App.secret_document' in app.request_cache
    assert app.untitled_documents[0].title is None

    # the object in the request cache is now detached
    with pytest.raises(DetachedInstanceError):
        key = 'test_orm_cache.<locals>.App.secret_document'
        assert app.request_cache[key].title

    # which we transparently undo
    assert app.secret_document.title is None


def test_orm_cache_flush(postgres_dsn, redis_url):

    Base = declarative_base(cls=ModelBase)

    class App(Framework):

        @orm_cached(policy='on-table-change:documents')
        def foo(self):
            return self.session().query(Document).one()

        @orm_cached(policy='on-table-change:documents')
        def bar(self):
            return self.session().query(Document)\
                .with_entities(Document.title).one()

    # get dill to pickle the following inline class
    global Document

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text, nullable=True)

    scan_morepath_modules(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    app.namespace = 'foo'
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
    # this point would contain stale entries because we didn't flush eplicitly,
    # but thanks to our autoflush mechanism this doesn't happen
    assert app.session().dirty
    assert app.bar.title == 'Sup'
    assert app.foo.title == 'Sup'


def test_associable_one_to_one(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Address(Base, Associable):
        __tablename__ = 'adresses'

        id = Column(Integer, primary_key=True)
        town = Column(Text, nullable=False)

    class Addressable(object):
        address = associated(Address, 'address', 'one-to-one')

    class Company(Base, Addressable):
        __tablename__ = 'companies'

        id = Column(Integer, primary_key=True)
        name = Column(Text, nullable=False)

    class Person(Base, Addressable):
        __tablename__ = 'people'

        id = Column(Integer, primary_key=True)
        name = Column(Text, nullable=False)

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
    assert seantis.address.town == "6004 Luzern"

    denis = session.query(Person).first()
    assert denis.address.town == "6343 Rotkreuz"

    addresses = session.query(Address).all()
    assert addresses[0].links.count() == 1
    assert addresses[0].links.first().name == "Seantis GmbH"
    assert len(addresses[0].linked_companies) == 1
    assert len(addresses[0].linked_people) == 0

    assert addresses[1].links.count() == 1
    assert addresses[1].links.first().name == "Denis Krienbühl"
    assert len(addresses[1].linked_companies) == 0
    assert len(addresses[1].linked_people) == 1

    session.delete(denis)
    session.flush()

    assert session.query(Address).count() == 1

    session.delete(addresses[0])
    session.flush()

    assert session.query(Company).first()


def test_associable_one_to_many(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Address(Base, Associable):
        __tablename__ = 'adresses'

        id = Column(Integer, primary_key=True)
        town = Column(Text, nullable=False)

    class Addressable(object):
        addresses = associated(Address, 'addresses', 'one-to-many')

    class Company(Base, Addressable):
        __tablename__ = 'companies'

        id = Column(Integer, primary_key=True)
        name = Column(Text, nullable=False)

    class Person(Base, Addressable):
        __tablename__ = 'people'

        id = Column(Integer, primary_key=True)
        name = Column(Text, nullable=False)

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
    assert seantis.addresses[0].town == "6004 Luzern"

    denis = session.query(Person).first()
    assert denis.addresses[0].town == "6343 Rotkreuz"

    addresses = session.query(Address).all()

    assert addresses[0].links.count() == 1
    assert addresses[0].links.first().name == "Seantis GmbH"
    assert len(addresses[0].linked_companies) == 1
    assert len(addresses[0].linked_people) == 0

    assert addresses[1].links.count() == 1
    assert addresses[1].links.first().name == "Denis Krienbühl"
    assert len(addresses[1].linked_companies) == 0
    assert len(addresses[1].linked_people) == 1

    session.delete(denis)
    session.flush()

    assert session.query(Address).count() == 1


def test_associable_many_to_many(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Address(Base, Associable):
        __tablename__ = 'adresses'

        id = Column(Integer, primary_key=True)
        town = Column(Text, nullable=False)

    class Addressable(object):
        addresses = associated(Address, 'addresses', 'many-to-many')

    class Company(Base, Addressable):
        __tablename__ = 'companies'

        id = Column(Integer, primary_key=True)
        name = Column(Text, nullable=False)

    class Person(Base, Addressable):
        __tablename__ = 'people'

        id = Column(Integer, primary_key=True)
        name = Column(Text, nullable=False)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    session.add(Company(
        name='Seantis GmbH',
        addresses=[Address(town='6004 Luzern')]
    ))

    session.add(Person(
        name='Denis Krienbühl',
        addresses=session.query(Company).first().addresses
    ))

    seantis = session.query(Company).first()
    assert seantis.addresses[0].town == "6004 Luzern"

    denis = session.query(Person).first()
    assert denis.addresses[0].town == "6004 Luzern"

    addresses = session.query(Address).all()
    assert addresses[0].links.count() == 2

    session.delete(denis)
    session.flush()

    assert session.query(Address).count() == 1


def test_associable_multiple(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Address(Base, Associable):
        __tablename__ = 'adresses'

        id = Column(Integer, primary_key=True)
        town = Column(Text, nullable=False)

    class Person(Base, Associable):
        __tablename__ = 'people'

        id = Column(Integer, primary_key=True)
        name = Column(Text, nullable=False)

        address = associated(Address, 'address', 'one-to-one')

    class Company(Base):
        __tablename__ = 'companies'

        id = Column(Integer, primary_key=True)
        name = Column(Text, nullable=False)

        address = associated(Address, 'address', 'one-to-one')
        employee = associated(Person, 'employee', 'one-to-many')

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()

    session.add(Company(
        name='Engulf & Devour',
        address=Address(town='Ember'),
        employee=[
            Person(name='Alice', address=Address(town='Alicante')),
            Person(name='Bob', address=Address(town='Brigadoon'))
        ]
    ))

    company = session.query(Company).first()
    assert company.address.town == "Ember"
    assert {e.name: e.address.town for e in company.employee} == {
        'Alice': 'Alicante', 'Bob': 'Brigadoon'
    }

    alice = session.query(Person).filter_by(name="Alice").one()
    assert alice.address.town == "Alicante"
    assert alice.linked_companies == [company]
    assert alice.links.count() == 1

    bob = session.query(Person).filter_by(name="Bob").one()
    assert bob.address.town == "Brigadoon"
    assert bob.linked_companies == [company]
    assert bob.links.count() == 1

    addresses = session.query(Address).all()
    assert session.query(Address).count() == 3

    assert addresses[0].links.count() == 1
    assert addresses[0].links.first().name == "Engulf & Devour"
    assert len(addresses[0].linked_companies) == 1
    assert len(addresses[0].linked_people) == 0

    assert addresses[1].links.count() == 1
    assert addresses[1].links.first().name == "Alice"
    assert len(addresses[1].linked_companies) == 0
    assert len(addresses[1].linked_people) == 1

    assert addresses[2].links.count() == 1
    assert addresses[2].links.first().name == "Bob"
    assert len(addresses[2].linked_companies) == 0
    assert len(addresses[2].linked_people) == 1

    session.delete(alice)
    session.flush()

    assert session.query(Address).count() == 2

    session.delete(addresses[2])
    session.flush()

    assert session.query(Company).first().address.town == 'Ember'


def test_selectable_sql_query(session):
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
        select((stmt.c.column_name, )).where(
            and_(
                stmt.c.table_name == 'pg_group',
                stmt.c.is_updatable == True
            )
        )
    ).fetchall()

    assert columns == [('groname', )]
    assert columns[0].column_name == 'groname'

    columns = session.execute(
        select((stmt.c.column_name, )).where(
            and_(
                stmt.c.table_name == 'pg_group',
                stmt.c.is_updatable == False
            )
        ).order_by(stmt.c.column_name)
    ).fetchall()

    assert columns == [('grolist', ), ('grosysid', )]
    assert columns[0].column_name == 'grolist'
    assert columns[1].column_name == 'grosysid'


def test_selectable_sql_query_with_array(session):
    stmt = as_selectable("""
        SELECT
            table_name AS table,                    -- Text
            array_agg(column_name::text) AS columns -- ARRAY(Text)
        FROM information_schema.columns
        GROUP BY "table"
    """)

    query = session.execute(select((stmt.c.table, stmt.c.columns)))
    table = next(query, None)

    assert isinstance(table.columns, list)
    assert len(table.columns) > 0


def test_selectable_sql_query_with_dots(session):
    stmt = as_selectable("""
        SELECT
            column_name,                                     -- Text
            information_schema.columns.table_name,           -- Text
            information_schema.columns.column_name as column -- Text
        FROM information_schema.columns
    """)

    assert tuple(stmt.c.keys()) == ('column_name', 'table_name', 'column')


def test_i18n_translation_hybrid_independence(postgres_dsn, redis_url):
    Base = declarative_base(cls=ModelBase)

    class App(Framework):
        pass

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)

        title_translations = Column(HSTORE, nullable=False)
        title = translation_hybrid(title_translations)

    @App.path(model=Document, path='/document')
    def get_document(app):
        return app.session().query(Document).first()

    @App.json(model=Document)
    def view_document(self, request):
        return {
            'title': self.title,
            'locale': self.session_manager.current_locale
        }

    scan_morepath_modules(App)

    freiburg = App()
    freiburg.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    freiburg.namespace = 'app'
    freiburg.set_application_id('app/freiburg')
    freiburg.locales = ['de_CH', 'fr_CH']

    biel = App()
    biel.configure_application(
        dsn=postgres_dsn,
        base=Base,
        redis_url=redis_url
    )
    biel.namespace = 'app'
    biel.set_application_id('app/biel')
    biel.locales = ['de_CH', 'fr_CH']

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


def test_unaccent_expression(postgres_dsn):
    Base = declarative_base(cls=ModelBase)

    class Test(Base):
        __tablename__ = 'test'

        text = Column(Text, primary_key=True)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.set_current_schema('testing')

    session = mgr.session()
    session.add(Test(text='Schweiz'))
    session.add(Test(text='Deutschland'))
    session.add(Test(text='Österreich'))
    transaction.commit()

    query = session.query(Test).order_by(unaccent(Test.text))
    assert [r.text for r in query] == ['Deutschland', 'Österreich', 'Schweiz']
