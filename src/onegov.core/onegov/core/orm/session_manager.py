import threading
import re
import weakref
import zope.sqlalchemy

from blinker import Signal
from onegov.core.cache import lru_cache
from onegov.core.custom import json
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm.query import Query
from sqlalchemy_utils.aggregates import manager as aggregates_manager


class ForceFetchQueryClass(Query):
    """ Alters the buitlin query class, ensuring that the delete query always
    fetches the data first, which is important for the bulk delete events
    to get the actual objects affected by the change.

    """

    def delete(self, synchronize_session=None):
        return super().delete('fetch')


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
    _reserved_schemas = {'information_schema', 'public', 'extensions'}

    def __init__(self, dsn, base,
                 engine_config=None, session_config=None, pool_config=None):
        """ Configures the data source name/dsn/database url and sets up the
        connection to the database.

        :dsn:
            Database connection string including user, password, host, port
            and database name.

            See: `<http://docs.sqlalchemy.org/en/latest/core/engines.html\
            #database-urls>`_

        :base:
            Declarative base used to define the SQLAlchemy database models.

            Extra bases may be added to the session manager after __init__::

                mgr.bases.append(MyBase)

            The tables in these additional schemas are created on the schema
            alongside the primary base.

        :engine_config:
            Additional configuration passed to SQLAlchemy's `create_engine`.

            See: `<http://docs.sqlalchemy.org/en/latest/core/engines.html\
            #sqlalchemy.create_engine>`

        :session_config:
            Additional configuration passed to SQLAlchemy's sessionmaker.

            See: `<http://docs.sqlalchemy.org/en/latest/orm/session_api.html\
            #sqlalchemy.orm.session.sessionmaker>`

        :pool_config:
            Custom pool configuration to be used in lieue of the default pool.
            Only use under special circumstances.

        Note, to connect to another database you need to create a new
        SessionManager instance.

        **Postgres Extensions**

        The session manager supports the setup of postgres extensions.
        Currently those extensions are hard-coded and they are all added to the
        extensions schema. The extensions schema is then added to the search
        path of each query.

        Since extensions can only be created by superusers, this is something
        you might want to do in a separate step in deployment. We don't advise
        you to use a superuser connection for your onegov cloud deployment.

        You may therefore use the list of the required extensions below and
        create a schema 'extensions' with those extensions inside.

        **Signals**

        The session manager supports the following signals:

        ``self.on_insert``

        Called with the schema and each object when an insert happens.

        ``self.on_update``

        Called with the schema and each object when a change happens.

        ``self.on_delete``

        Called with the scheam and each object when a change happens. Note that
        because those objects basically do not exist anymore, only the
        primary keys of those objects contain actual values!

        Signals abstracts SQLAlchemy ORM events. Since those handle events
        of the Session, only things happening on sessions provided by this
        sessionmanager are caught. Raw SQL queries, other sessions and other
        outside changes to the database are not caught!

        The signals are implemented using blinker:
        `<https://pythonhosted.org/blinker/>`_

        Note that signal handler functions are by default attached as weakrefs,
        that means if you create your signal handling function inside another
        function, the signal will stop working once the outer function
        completes.

        To avoid this behavior use ``connect_via``. See examples below:

        Examples::

            mgr = SessionManager(dsn)

            # connect to the insert signal, disconnecting automatically once
            # the handler function is garbage collected
            @mgr.on_insert.connect
            def on_insert(schema, obj):
                print("Inserted {} @ {}".format(obj, schema))

            # connect to the update signal, limited to a specific schema, also
            # disconnecting automatically once the handler function falls out
            # of scope
            @mgr.on_update.connect_via('my-schema')
            def on_update(schema, obj):
                print("Updated {} @ {}".format(obj, schema))

            # connect to the delete signal for all schemas -> here, the
            # handler is strongly referenced and may be used in a closure
            from blinker import ANY
            @mgr.on_delete.connect_via(ANY, weak=False)
            def on_delete(schema, obj):
                print("Deleted {} @ {}".format(obj, schema))

        """
        assert 'postgres' in dsn, "Onegov only supports Postgres!"

        engine_config = engine_config or {}
        session_config = session_config or {}
        pool_config = pool_config or {}

        self.dsn = dsn
        self.bases = [base]
        self.created_schemas = set()
        self.current_schema = None

        self.on_insert = Signal()
        self.on_update = Signal()
        self.on_delete = Signal()

        # onegov.core creates extensions that it requires in a separate schema
        # in the future, this might become something we can configure through
        # the setuptools entry_points -> modules could advertise what they need
        # and the core would install the extensions the modules require
        self.required_extensions = {'btree_gist', 'hstore', 'unaccent'}
        self.created_extensions = set()

        # override the isolation level in any case, we cannot allow another
        engine_config['isolation_level'] = 'SERIALIZABLE'

        # provide our custom serializer to the engine
        assert 'json_serializer' not in engine_config
        assert 'json_deserializer' not in engine_config

        engine_config['json_serializer'] = json.dumps
        engine_config['json_deserializer'] = json.loads

        if pool_config:
            engine_config.update(pool_config)
        else:
            # the default pool config should work for all onegov applications
            #
            # currently most applications use one single connection that is
            # reused between requests as well as one extra connection for each
            # instance (cronjob thread with session-based lock)
            engine_config['poolclass'] = QueuePool

            # connections which are kept open when returned to the pool
            engine_config['pool_size'] = 5

            # connections which are closed when returned (unlimited)
            engine_config['max_overflow'] = -1

        self.engine = create_engine(self.dsn, **engine_config)
        self.register_engine(self.engine)

        self.session_factory = scoped_session(
            sessionmaker(
                bind=self.engine,
                query_cls=ForceFetchQueryClass,
                **session_config
            ),
            scopefunc=self._scopefunc,
        )
        self.register_session(self.session_factory)
        self.setup_manager_instance_sharing(self.bases)

    def register_engine(self, engine):
        """ Takes the given engine and registers it with the schema
        switching mechanism. Maybe used to register external engines with
        the session manager.

        If used like this, make sure to call :meth:`bind_session` before using
        the session provided by the external engine.

        """

        @event.listens_for(engine, "before_cursor_execute")
        def _activate_schema(
            conn, cursor, statement, parameters, context, executemany
        ):
            """ Share the 'info' dictionary of Session with Connection
            objects.

            """

            # execution options have priority!
            if 'schema' in conn._execution_options:
                schema = conn._execution_options['schema']
            else:
                if 'session' in conn.info:
                    schema = conn.info['session'].info['schema']
                else:
                    schema = None

            if schema is not None:
                cursor.execute("SET search_path TO %s, extensions", (schema, ))

    def register_session(self, session):
        """ Takes the given session and registers it with zope.sqlalchemy and
        various orm events.

        """

        signals = (
            (self.on_insert, lambda session: session.new),
            (self.on_update, lambda session: session.dirty),
            (self.on_delete, lambda session: session.deleted)
        )

        # SQLAlchemy-Utils' aggregates decorator doesn't work correctly
        # with our sessions - we need to setup the appropriate event handler
        # manually. There's a test that makes sure that this is not done
        # twice. The cause of this has to be investigated still.
        event.listen(
            target=session,
            identifier='after_flush',
            fn=aggregates_manager.construct_aggregate_queries
        )

        # This check we need in any case, since aggregates don't work with
        # bulk udpdates/deletes, which is something we make sure can't
        # happen by accident (it'll lead to hard to debug errors)
        cache_size = min(len(aggregates_manager.generator_registry), 32)

        @lru_cache(cache_size)
        def prevent_bulk_changes_on_aggregate_modules(module_class):
            for registered in aggregates_manager.generator_registry:
                assert not issubclass(module_class, registered), """
                    Bulk queries run on models that use sqlalchemy-utils
                    aggregates won't lead to a proper update. It's impossible
                    to have both aggregates and bulk updates/deletes.
                """

        @event.listens_for(session, 'after_flush')
        def on_after_flush(session, flush_context):
            for signal, get_objects in signals:
                if signal.receivers:
                    for obj in get_objects(session):
                        signal.send(self.current_schema, obj=obj)

        @event.listens_for(session, 'after_bulk_update')
        def on_after_bulk_update(update_context):
            prevent_bulk_changes_on_aggregate_modules(
                update_context.mapper.class_)

            if self.on_update.receivers:
                assert hasattr(update_context, 'matched_objects'), """
                    Bulk queries which use synchronize_session=False or
                    synchronize_session='fetch' cannot be supported because
                    it is unclear what rows were affected. Manually update
                    values instead (even though it's way slower). There's no
                    better solution at the moment.
                """

                for obj in update_context.matched_objects:
                    self.on_update.send(self.current_schema, obj=obj)

        @event.listens_for(session, 'after_bulk_delete')
        def on_after_bulk_delete(delete_context):
            prevent_bulk_changes_on_aggregate_modules(
                delete_context.mapper.class_)

            if self.on_delete.receivers:
                for row in delete_context.matched_rows:
                    obj = delete_context.mapper.class_(**{
                        c.name: v for c, v
                        in zip(delete_context.mapper.primary_key, row)
                    })
                    self.on_delete.send(self.current_schema, obj=obj)

        zope.sqlalchemy.register(session)

    def setup_manager_instance_sharing(self, bases):
        """ Shares this instance with all mapped classes of all bases.

        This enables each model to look up the current schema, the current
        locale and so on.

        This is a rather complicated way to make sure we don't use a global
        variable. One might argue that this would warrant an exception
        to the rule...

        """

        # the instance is shared with all classes, loaded or created
        def share_with_class(target, *args, **kwargs):
            target.session_manager = weakref.proxy(self)

        # and it is shared with all query types, at which point there is
        # no type available yet.
        def share_with_query(query):
            session_manager = weakref.proxy(self)

            for desc in query.column_descriptions:
                desc['type'].session_manager = session_manager

        event.listen(Query, 'before_compile', share_with_query, retval=False)

        for base in bases:
            if base:
                for cls in base._decl_class_registry.values():
                    if isinstance(cls, base.__class__):
                        event.listen(cls, 'init', share_with_class)
                        event.listen(cls, 'load', share_with_class)

    def set_locale(self, default_locale, current_locale):
        """ Sets the default locale and the current locale so it may be
        shared with the translated ORM columns.

        Note that the locales may be NONE. It is up to the consumer of these
        settings to assert their existence.

        """

        self.default_locale = default_locale
        self.current_locale = current_locale

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

    def create_schema(self, schema, validate=True):
        """ Creates the given schema. If said schema exists, expect this
        method to throw an error. If you use :meth:`set_current_schema`,
        this is invoked automatically if needed. So you usually shouldn't
        have to care about this function.

        """

        if validate:
            assert self.is_valid_schema(schema)

        # psycopg2 doesn't know how to correctly build a CREATE
        # SCHEMA statement, so we need to do it manually.
        # self.is_valid_schema should've checked that no sql
        # injections are possible.
        #
        # this is the *only* place where this happens - if anyone
        # knows how to do this using sqlalchemy/psycopg2, come forward!
        conn = self.engine.execution_options(schema=None)
        conn.execute('CREATE SCHEMA "{}"'.format(schema))
        conn.execute('COMMIT')

    def create_schema_if_not_exists(self, schema, validate=True):
        """ Creates the given schema if it doesn't exist yet. """
        if not self.is_schema_found_on_database(schema):
            self.create_schema(schema, validate)

    def bind_session(self, session):
        """ Bind the session to the current schema. """
        session.info['schema'] = self.current_schema
        session.connection().info['session'] = weakref.proxy(session)

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
        query = text("""
            SELECT schema_name
            FROM information_schema.schemata
            ORDER BY schema_name
        """)

        if limit_to_namespace is not None:
            return [
                r[0] for r in conn.execute(query).fetchall()
                if r[0].startswith(limit_to_namespace + '-')
            ]
        else:
            return [r[0] for r in conn.execute(query).fetchall()]

    def is_schema_found_on_database(self, schema):
        """ Returns True if the given schema exists on the database. """

        conn = self.engine.execution_options(schema=None)
        result = conn.execute(text(
            "SELECT EXISTS(SELECT 1 FROM information_schema.schemata "
            "WHERE schema_name = :schema)"
        ), schema=schema)

        return result.first()[0]

    def create_required_extensions(self):
        """ Creates the required extensions once per lifetime of the manager.

        """
        if self.required_extensions != self.created_extensions:

            # extensions are a all added to a shared schema (a reserved schema)
            self.create_schema_if_not_exists('extensions', validate=False)

            conn = self.engine.execution_options(schema='extensions')
            for ext in self.required_extensions - self.created_extensions:
                conn.execute(
                    'CREATE EXTENSION IF NOT EXISTS "{}" '
                    'SCHEMA "extensions"'.format(ext)
                )
                conn.execute('COMMIT')
                self.created_extensions.add(ext)

    def ensure_schema_exists(self, schema):
        """ Makes sure the schema exists on the database. If it doesn't, it
        is created.

        """
        assert self.engine is not None

        if schema not in self.created_schemas:

            # XXX circular dependencies
            from onegov.core import upgrade

            # this is important because CREATE SCHEMA is done in a possibly
            # dangerous way!
            assert self.is_valid_schema(schema)

            # setup the extensions right before we activate our first schema
            self.create_required_extensions()
            self.create_schema_if_not_exists(schema)

            conn = self.engine.execution_options(schema=schema)
            declared_classes = set()

            try:
                for base in self.bases:
                    base.metadata.schema = schema
                    base.metadata.create_all(conn)

                    declared_classes.update(base._decl_class_registry.values())

                conn.execute('COMMIT')
            finally:
                # reset the schema on the global base variable - this state
                # sticks around otherwise and haunts us in the tests
                for base in self.bases:
                    base.metadata.schema = None

            # if we have an upgrade state table, we want to prefill it with
            # all the current modules/tasks, to get the correct initial update
            # state (see https://github.com/OneGov/onegov.core/issues/8)
            #
            # we usually want to do that, but during testing, those upgrade
            # state classes may not exist, that's why we check
            if upgrade.UpgradeState in declared_classes:

                # we use a special session that is not registered with the
                # zope transaction extension -> we do this during a request
                # and we don't want the whole request to be commited, just
                # this small change.
                session = sessionmaker(bind=self.engine)()
                upgrade.register_all_modules_and_tasks(session)
                session.commit()

            self.created_schemas.add(schema)
