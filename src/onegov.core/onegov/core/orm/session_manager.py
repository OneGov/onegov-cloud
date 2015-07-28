import threading
import re
import zope.sqlalchemy

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool


class SessionManager(object):
    """ Holds sessions and creates schemas before binding sessions to schemas.

    Threadsafe in theory, but not tested or well thought out. No global state
    though, so two different session managers will manage different
    sessions/schemas.

    """

    # describes the accepted characters in a schema name
    _valid_schema_name = re.compile(r'^[a-z0-9_-]+$')

    # describes the prefixes with which a schema may not begin
    _invalid_prefixes = re.compile(r'^([0-9]|pg_)+')

    # holds schemas that may never be used:
    # - information_schema is a sql standard schema that's for internal use
    # - public is the default schema name which should not be used for security
    #   reasons. Someone could figure out a way to set the search_path to
    #   default and to add an application that has the right to change the
    #   public schema.
    _reserved_schemas = {'information_schema', 'public'}

    # defines the currently used schema (global variable)
    __current_schema = None

    def __init__(self, dsn, base,
                 engine_config={}, session_config={}, on_set_search_path=None):
        """ Configures the data source name/dsn/database url and sets up the
        connection to the database.

        :dsn:
            Database connection string including user, password, host, port
            and database name.

            See: `<http://docs.sqlalchemy.org/en/latest/core/engines.html\
            #database-urls>`_

        :base:
            Declarative base used to define the SQLAlchemy database models.

        :engine_config:
            Additional configuration passed to SQLAlchemy's `create_engine`.

            See: `<http://docs.sqlalchemy.org/en/latest/core/engines.html\
            #sqlalchemy.create_engine>`

        :session_config:
            Additional configuration passed to SQLAlchemy's sessionmaker.

            See: `<http://docs.sqlalchemy.org/en/latest/orm/session_api.html\
            #sqlalchemy.orm.session.sessionmaker>`

        :on_set_search_path:
            An optional function that receives the schema right after
            'SET search_path TO' query is executed. Only used for testing.

        Example::

            from sqlalchemy.ext.declarative import declarative_base

            Base = declarative_base()
            manager.setup(
                'postgres://user:password@localhost:5432/dbname', Base)

        Note, to connect to another database you need to create a new
        SessionManager instance.

        """
        assert 'postgres' in dsn, "Onegov only supports Postgres!"

        self.dsn = dsn
        self.base = base
        self.created_schemas = set()
        self.on_set_search_path = on_set_search_path

        self.engine = create_engine(
            self.dsn,
            poolclass=SingletonThreadPool,
            **engine_config
        )
        self.register_engine(self.engine)

        self.session_factory = scoped_session(
            sessionmaker(bind=self.engine, **session_config),
            scopefunc=self._scopefunc
        )
        zope.sqlalchemy.register(self.session_factory)

    def _activate_schema(self,
                         conn, cursor, stmt, params, context, executemany):
        """ Processes before_cursor_execute events and forces the current
        *global* schema to be used.

        """
        if 'schema' in conn._execution_options:
            schema = conn._execution_options['schema']
        else:
            schema = self.__current_schema

        if schema is not None:
            cursor.execute("SET search_path TO %s", (schema, ))

            if self.on_set_search_path:
                self.on_set_search_path(schema)

    def register_engine(self, engine):
        """ Takes the given engine and registers it with the *global* schema
        switching mechanism. Again, this is *global*, so there can only be
        one session manager and whatever it has set as the current schema, will
        be enforced on *all* engines registered with it.

        """

        event.listen(engine, "before_cursor_execute", self._activate_schema)

    def _scopefunc(self):
        """ Returns the scope of the scoped_session used to create new
        sessions. Relies on self.current_schema being set before the
        session is created.

        This function is as internal as they come and it exists only because
        we otherwise would have to create different session factories for each
        schema.

        """
        return (threading.current_thread(), self.current_schema)

    def dispose(self):
        """ Closes the connection to the server and cleans up. This only needed
        for testing.

        """
        self.engine.raw_connection().invalidate()
        self.engine.dispose()

    def is_valid_schema(self, schema):
        """ Returns True if the given schema looks valid enough to be created
        on the database with no danger of SQL injection or other unwanted
        sideeffects.

        """
        if not schema:
            return False

        if schema in self._reserved_schemas:
            return False

        if self._invalid_prefixes.match(schema):
            return False

        # only one consecutive '-' is allowed (-- constitues a comment)
        if '--' in schema:
            return False

        return self._valid_schema_name.match(schema) and True or False

    def set_current_schema(self, schema):
        """ Sets the current schema in use. The current schema is then used
        to bind the session to a schema. Note that this can't be done
        in a functional way. We need the current schema to generate a new
        scope.

        I would very much prefer to bind this to the session but this is not
        at all straight-forward with SQLAlchemy.

        I tried a solution like `this one <https://bitbucket.org/zzzeek/\
        sqlalchemy/wiki/UsageRecipes/SessionModifiedSQL>`_, but it's not good
        enough, because it still relies on some kind of global stage, even if
        it's set locally.

        Ideally a value could be bound to the session and an event would
        trigger every time the connection is used with that session. We
        could then set the schema on the connection every time that happens.

        For now, the global option is okay though, because in practice we
        only set the schema once per request and we don't do threading
        anyway.

        """
        assert self.is_valid_schema(schema)

        self.current_schema = schema
        self.ensure_schema_exists(schema)

    def bind_session(self, session):
        """ Bind the session to the current schema. """
        session.info['schema'] = self.current_schema
        session.connection().info['session'] = session

        return session

    def session(self):
        """ Returns a new session or an existing session. Sessions with
        different schemas are kept independent, though they might reuse
        each others connections.

        This means that a session retrieved thusly::

            mgr = SessionManager('postgres://...')
            mgr.set_current_schema('foo')
            session = mgr.session()

        Will not see objects attached to this session::

            mgr.set_current_schema('bar')
            session = mgr.session()

        """

        return self.bind_session(self.session_factory())

    def list_schemas(self, limit_to_namespace=None):
        """ Returns a list containing *all* schemas defined in the current
        database.

        """
        conn = self.engine.execution_options(schema=None)
        query = text("SELECT schema_name FROM information_schema.schemata")

        if limit_to_namespace is not None:
            return [
                r[0] for r in conn.execute(query).fetchall()
                if r[0].startswith(limit_to_namespace + '-')
            ]
        else:
            return [r[0] for r in conn.execute(query).fetchall()]

    def ensure_schema_exists(self, schema):
        """ Makes sure the schema exists on the database. If it doesn't, it
        is created.

        """
        assert self.engine is not None

        if schema not in self.created_schemas:

            # this is important because CREATE SCHEMA is done in a possibly
            # dangerous way!
            assert self.is_valid_schema(schema)

            # psycopg2 doesn't know how to correctly build a CREATE
            # SCHEMA statement, so we need to do it manually.
            # self.is_valid_schema should've checked that no sql
            # injections are possible.
            #
            # this is the *only* place where this happens - if anyone
            # knows how to do this using sqlalchemy/psycopg2, come forward!
            conn = self.engine.execution_options(schema=None)
            conn.execute('CREATE SCHEMA IF NOT EXISTS "{}"'.format(schema))
            conn.execute('COMMIT')

            conn = self.engine.execution_options(schema=schema)

            try:
                self.base.metadata.schema = schema
                self.base.metadata.create_all(conn)
                conn.execute('COMMIT')
            finally:
                # reset the schema on the global base variable - this state
                # sticks around otherwise and haunts us in the tests
                self.base.metadata.schema = None

            self.created_schemas.add(schema)
