from more.transaction import TransactionApp
from onegov.core.request import VirtualHostRequest
from onegov.server import Application as ServerApplication


class Framework(TransactionApp, ServerApplication):
    """ Baseclass for Morepath OneGov applications. """

    request_class = VirtualHostRequest

    def configure_application(self, **configuration):
        super(Framework, self).configure_application(**configuration)
        self.dsn = configuration.get('dsn')

    def set_application_id(self, application_id):
        super(Framework, self).set_application_id(application_id)
        self.schema = application_id.replace('/', '-')
