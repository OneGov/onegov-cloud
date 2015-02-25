from cached_property import cached_property
from more.transaction import TransactionApp
from onegov.core.orm import Base, SessionManager
from onegov.core.request import VirtualHostRequest
from onegov.server import Application as ServerApplication


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

    def configure_application(self, **configuration):
        """ Configures the application, supporting the following parameters:

        :dsn:
            The database connection to use. May be None.

            See :meth:`onegov.core.orm.session_manager.setup`

        :base:
            The declarative base class used. By default,
            :attr:`onegov.core.orm.Base`is used.

        """

        super(Framework, self).configure_application(**configuration)

        self.dsn = configuration.get('dsn')

        if self.dsn:
            self.session_manager = SessionManager(
                self.dsn, configuration.get('base', Base))

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
