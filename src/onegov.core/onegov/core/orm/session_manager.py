import threading
import transaction
import re
import zope.sqlalchemy

from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import SingletonThreadPool


class SessionManager(object):
    """ Holds sessions and creates schemas before binding sessions to schemas.

    It currently works by keeping the currently used schema in a global
    variable. So this class is not threadsafe, nor should it be used
    with multiple instances.

    This is unfortunate, but it's good enough for our current use case. That
    is to say, this sucks, but it works because:

        - Every request has one schema associated with it.
        - Concurrency is enabled using multiple WSGI processes.

    Refactoring this to be threadsafe and to be independent is not *that* easy
    because SQLAlchemy doesn't have straight-forward facilities to implement
    this kind of thing (schema bound sessions with connections that connect
    to the bound schema only).

    """

    # describes the accepted characters in a schema name
    _valid_schema_name = re.compile(r'^[a-z0-9_-]+$')

    # holds prefixes with which a schema may not begin
    _invalid_prefixes = ('pg_', ) + tuple(str(i) for i in range(0, 10))

    # holds schemas that may never be used:
    # - information_schema is a sql standard schema that's for internal use
    # - public is the default schema name which should not be used for security
    #   reasons. Someone could figure out a way to set the search_path to
    #   default and to add an application that has the right to change the
    #   public schema.
    _reserved_schemas = {'information_schema', 'public'}

    # defines the currently used schema (global variable)
    __current_schema = None

    def __init__(self):

        #: the engine used in the current thread
        self.engine = None

        #: schemas that were created
        self.created_schemas = set()

        #: dsn associated with this configuration
        self.dsn = None

        #: the SQLAlchemy base to operate on
        self.base = None

        #: the session factory to use
        self.session_factory = None

    def _scopefunc(self):
        """ Returns the scope of the scoped_session used to create new
        sessions. Relies on self.__current_schema being set before the
        session is created.

        This function is as internal as they come and it exists only because
        we otherwise would have to create different session factories for each
        schema.

        """
        return (threading.current_thread(), self.__current_schema)

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

        if schema.startswith(self._invalid_prefixes):
            return False

        if schema in self._reserved_schemas:
            return False

        return self._valid_schema_name.match(schema) and True or False

    def setup(self, dsn, base, engine_config={}, session_config={}):
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

        Example::

            from sqlalchemy.ext.declarative import declarative_base

            Base = declarative_base()
            manager.setup(
                'postgres://user:password@localhost:5432/dbname', Base)

        Note that the dsn can only be configured once, as other things depend
        on it. It might be possible to add this feature, so get in touch if
        you have a use case for this.

        """

        assert self.dsn is None or self.dsn == dsn
        assert 'postgres' in dsn, "Onegov only supports Postgres!"

        self.dsn = dsn
        self.base = base

        self.engine = create_engine(
            self.dsn,
            poolclass=SingletonThreadPool,
            **engine_config
        )
        self.session_factory = scoped_session(
            sessionmaker(bind=self.engine, **session_config),
            scopefunc=self._scopefunc
        )

        zope.sqlalchemy.register(self.session_factory)

        def activate_schema(conn, cursor, stmt, params, context, executemany):
            if 'schema' in conn._execution_options:
                schema = conn._execution_options['schema']
            else:
                schema = self.__current_schema

            # it's important that we check the schema every time before we
            # use it in an SQL statement!
            assert self.is_valid_schema(schema)
            cursor.execute('SET search_path TO "{}"'.format(schema))

        event.listen(self.engine, "before_cursor_execute", activate_schema)

    def set_current_schema(self, schema):
        """ Sets the current schema in use. Note that this is a *global*
        setting and will affect all sessions in use!

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
        self.__current_schema = schema
        self.ensure_schema_exists(schema)

    def session(self):
        """ Returns a new session or an existing session. Sessions with
        different schemas are kept independent, though they might reuse
        each others connections.

        This means that a session retrieved thusly::

            mgr = SessionManager()
            mgr.set_current_schema('foo')
            session = mgr.session()

        Will not see objects attached to this session::

            mgr.set_current_schema('bar')
            session = mgr.session()

        """
        return self.session_factory()

    def is_schema_found_on_database(self, schema):
        """ Returns True if the given schema exists on the database. """

        assert self.is_valid_schema(schema)

        result = self.engine.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.schemata "
            "WHERE schema_name = '{}')".format(schema)
        )

        return result.first()[0]

    def ensure_schema_exists(self, schema):
        """ Makes sure the schema exists on the database. If it doesn't, it
        is created.

        """
        assert self.engine is not None

        if schema not in self.created_schemas:

            # I haven't figured out yet how to safely create a DDL statement
            # in SQLAlchemy. This is why the schema is checked for validity
            # (a-z only, without any spaces) and only checked schemas are later
            # allowed to be switched to. Nobody should have influence on these
            # schemas anyway, but we want to be very sure.
            assert self.is_valid_schema(schema)

            if not self.is_schema_found_on_database(schema):
                self.engine.execute('CREATE SCHEMA "{}"'.format(schema))
                self.engine.execute("COMMIT")

            conn = self.engine.execution_options(schema=schema)

            self.base.metadata.schema = schema
            self.base.metadata.create_all(conn)

            conn.execute('COMMIT')
            transaction.commit()

            self.created_schemas.add(schema)
