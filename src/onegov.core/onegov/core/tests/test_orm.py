import json
import transaction

from morepath import setup
from onegov.core.orm import SessionManager
from onegov.core.orm.types import JSON
from onegov.core.framework import Framework
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from webtest import TestApp as Client
from webob.exc import HTTPUnauthorized


def test_is_valid_schema(dsn):
    mgr = SessionManager(dsn, None)
    assert not mgr.is_valid_schema('pg_test')
    assert not mgr.is_valid_schema('-- or 1=1')
    assert not mgr.is_valid_schema('0')
    assert not mgr.is_valid_schema('information_schema')
    assert not mgr.is_valid_schema('public')
    assert not mgr.is_valid_schema('my--schema')
    assert mgr.is_valid_schema('my_schema')
    assert mgr.is_valid_schema('my-schema')


def test_create_schema(dsn):
    Base = declarative_base()

    class Document(Base):
        __tablename__ = 'document'

        id = Column(Integer, primary_key=True)
        title = Column(Text)

    mgr = SessionManager(dsn, Base)

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


def test_schema_bound_session(dsn):
    Base = declarative_base()

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text)

    mgr = SessionManager(dsn, Base)
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


def test_session_scope(dsn):
    Base = declarative_base()

    mgr = SessionManager(dsn, Base)

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


def test_orm_scenario(dsn):
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
    import more.transaction
    config.scan(more.transaction)

    config.commit()

    app = App()
    app.configure_application(dsn=dsn, base=Base)
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


def test_json_type(dsn):
    Base = declarative_base()

    class Test(Base):
        __tablename__ = 'test'

        id = Column(Integer, primary_key=True)
        data = Column(JSON, nullable=True)

    mgr = SessionManager(dsn, Base)
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
