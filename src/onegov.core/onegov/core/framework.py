from cached_property import cached_property
from more.transaction import TransactionApp
from onegov.core.orm import Base, SessionManager
from onegov.core.request import VirtualHostRequest
from onegov.server import Application as ServerApplication


class Framework(TransactionApp, ServerApplication):
    """ Baseclass for Morepath OneGov applications. """

    request_class = VirtualHostRequest

    def configure_application(self, **configuration):
        super(Framework, self).configure_application(**configuration)
        self.dsn = configuration.get('dsn')
        self.session_manager = SessionManager()
        self.session_manager.setup(self.dsn, configuration.get('base', Base))

    def set_application_id(self, application_id):
        super(Framework, self).set_application_id(application_id)
        self.schema = application_id.replace('/', '-')
        self.session_manager.set_current_schema(self.schema)

    @cached_property
    def session(self):
        """ Alias for self.session_manager.session. """
        return self.session_manager.session
