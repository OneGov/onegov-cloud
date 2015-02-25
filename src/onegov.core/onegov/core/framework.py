from cached_property import cached_property
from more.transaction import TransactionApp
from onegov.core.orm import Base, SessionManager
from onegov.core.request import VirtualHostRequest
from onegov.server import Application as ServerApplication
from uuid import uuid4 as new_uuid


class Framework(TransactionApp, ServerApplication):
    """ Baseclass for Morepath OneGov applications. """

    request_class = VirtualHostRequest

    #: holds the database connection string, *if* there is a database connected
    dsn = None

    #: holdes the current schema associated with the database connection, set
    #: by and derived from :meth:`set_application_id`.
    schema = None

    @property
    def has_database_connection(self):
        """ onegov.core has good integration for Postgres using SQLAlchemy, but
        it doesn't require a connection.

        It's possible to have Onegov applications using a different database
        or not using one at all.

        """
        return self.dsn is not None

    def configure_application(self, **cfg):
        """ Configures the application, supporting the following parameters:

        :dsn:
            The database connection to use. May be None.

            See :meth:`onegov.core.orm.session_manager.setup`

        :base:
            The declarative base class used. By default,
            :attr:`onegov.core.orm.Base`is used.

        :identity_secure:
            True if the identity cookie is only transmitted over https. Only
            set this to False during development!

        :identity_secret_key:
            A random string used to sign the identity. By default a random
            string is generated. The drawback of this is the fact that
            users will be logged out every time the application restarts.

            So provide your own if you don't want that, but be sure to have
            a really long, really random key that you will never share
            with anyone!

        """

        super(Framework, self).configure_application(**cfg)

        self.dsn = cfg.get('dsn')

        if self.dsn:
            self.session_manager = SessionManager(
                self.dsn, cfg.get('base', Base))

        self.identity_secure = cfg.get('identity_secure', True)
        self.identity_secret_key = cfg.get(
            'identity_secret_key', new_uuid().hex)

    def set_application_id(self, application_id):
        """ Set before the request is handled. Gets the schema from the
        application id and makes sure it exists, *if* a database connection
        is present.

        """
        super(Framework, self).set_application_id(application_id)
        self.schema = application_id.replace('/', '-')

        if self.has_database_connection:
            self.session_manager.set_current_schema(self.schema)

    @cached_property
    def session(self):
        """ Alias for self.session_manager.session. """
        return self.session_manager.session
