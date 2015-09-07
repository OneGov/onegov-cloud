import json
import morepath
import pytest
import sqlalchemy
import time
import transaction
import uuid

from datetime import datetime
from morepath import setup
from onegov.core.framework import Framework
from onegov.core.orm import SessionManager
from onegov.core.orm.mixins import ContentMixin, TimestampMixin
from onegov.core.orm.types import JSON, UTCDateTime, UUID
from onegov.core.security import Private
from psycopg2.extensions import TransactionRollbackError
from pytz import timezone
from sqlalchemy import Column, Integer, Text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.mutable import MutableDict
from threading import Thread
from webob.exc import HTTPUnauthorized, HTTPConflict
from webtest import TestApp as Client


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
    Base = declarative_base()

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
    Base = declarative_base()

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
    Base = declarative_base()

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
    Base = declarative_base()

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
    Base = declarative_base()

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


def test_orm_scenario(postgres_dsn):
    # test a somewhat complete ORM scenario in which create and read data
    # for different applications
    Base = declarative_base()
    config = setup()

    class App(Framework):
        testing_config = config

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
    import onegov.core
    import more.transaction
    import more.webassets
    config.scan(more.transaction)
    config.scan(more.webassets)
    config.scan(onegov.core)
    config.commit()

    app = App()
    app.configure_application(dsn=postgres_dsn, base=Base)
    app.namespace = 'municipalities'

    c = Client(app)

    # let's try to add some documents to new york
    app.set_application_id('municipalities/new-york')

    assert json.loads(c.get('/documents').text) == {}
    c.post('/documents/add', {'title': 'Welcome to the big apple!'})

    assert json.loads(c.get('/documents').text) == {
        '1': "Welcome to the big apple!"
    }

    # after that, we switch to chicago, where a different set of documents
    # should exist
    app.set_application_id('municipalities/chicago')

    assert json.loads(c.get('/documents').text) == {}
    c.post('/documents/add', {'title': 'Welcome to the windy city!'})

    assert json.loads(c.get('/documents').text) == {
        '1': "Welcome to the windy city!"
    }

    # finally, let's see if the transaction is rolled back if there's an
    # error during the course of the request
    c.get('/documents/error', expect_errors=True)
    assert json.loads(c.get('/documents').text) == {
        '1': "Welcome to the windy city!"
    }

    app.session_manager.dispose()


def test_json_type(postgres_dsn):
    Base = declarative_base()

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

    assert session.query(Test).filter(Test.id == 1).one().data is None

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

    mgr.dispose()


def test_uuid_type(postgres_dsn):
    Base = declarative_base()

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


def test_utc_datetime_naive(postgres_dsn):
    Base = declarative_base()

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
    Base = declarative_base()

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
    Base = declarative_base()

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
    Base = declarative_base()

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
    Base = declarative_base()

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

    assert mgr.created_extensions == {'hstore'}


def test_serialization_failure(postgres_dsn):

    Base = declarative_base()

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


@pytest.mark.parametrize("number_of_retries", range(1, 10))
def test_application_retries(postgres_dsn, number_of_retries):

    Base = declarative_base()
    config = setup()

    class App(Framework):
        testing_config = config

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
                role='editor',
                application_id=request.app.application_id
            )

            morepath.remember_identity(response, request, identity)

    @App.view(model=Document, permission=Private)
    def provoke_serialization_failure(self, request):
        session = request.app.session()
        session.add(Record())
        session.query(Record).delete('fetch')

        time.sleep(0.1)

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

    import onegov.core
    import more.transaction
    import more.webassets
    config.scan(more.transaction)
    config.scan(more.webassets)
    config.scan(onegov.core)
    config.commit()

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        base=Base,
        identity_secure=False,
        disable_memcached=True
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
    Base = declarative_base()

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
    Base = declarative_base()

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
    Base = declarative_base()

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
    Base = declarative_base()

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


def test_orm_signals(postgres_dsn):
    Base = declarative_base()

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
