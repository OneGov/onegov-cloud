from onegov.core.orm import SessionManager
from sqlalchemy import Column, Integer, Text
from sqlalchemy.ext.declarative import declarative_base


def test_is_valid_schema():
    mgr = SessionManager()
    assert not mgr.is_valid_schema('pg_test')
    assert not mgr.is_valid_schema('-- or 1=1')
    assert not mgr.is_valid_schema('0')
    assert not mgr.is_valid_schema('information_schema')
    assert not mgr.is_valid_schema('public')
    assert mgr.is_valid_schema('my_schema')
    assert mgr.is_valid_schema('my-schema')


def test_create_schema(dsn):
    Base = declarative_base()

    class Document(Base):
        __tablename__ = 'document'

        id = Column(Integer, primary_key=True)
        title = Column(Text)

    mgr = SessionManager()
    mgr.setup(dsn, Base)

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

    assert 'test' not in existing_schemas()

    mgr.ensure_schema_exists('test')

    assert 'test' in existing_schemas()
    assert 'document' in schema_tables('test')
    assert 'document' not in schema_tables('public')


def test_schema_bound_session(dsn):
    Base = declarative_base()

    class Document(Base):
        __tablename__ = 'documents'

        id = Column(Integer, primary_key=True)
        title = Column(Text)

    mgr = SessionManager()
    mgr.setup(dsn, Base)

    mgr.set_current_schema('foo')
    session = mgr.session()

    session.add(Document(title='Welcome to Foo'))
    session.commit()

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

    mgr = SessionManager()
    mgr.setup(dsn, Base)

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
