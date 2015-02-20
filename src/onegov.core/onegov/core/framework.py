from morepath.app import App as MorepathApp
from onegov.core.request import VirtualHostRequest
from onegov.server import Application as ServerApplication


class Framework(MorepathApp, ServerApplication):
    """ Baseclass for Morepath OneGov applications. """

    request_class = VirtualHostRequest
