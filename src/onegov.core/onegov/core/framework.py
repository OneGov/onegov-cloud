import re

from cached_property import cached_property
from morepath.app import App as MorepathApp
from onegov.core import compat
from onegov.core.request import VirtualHostRequest
from onegov.server import Application as ServerApplication
from webob.exc import HTTPForbidden


class Framework(MorepathApp, ServerApplication):
    """ Baseclass for Morepath OneGov applications. """

    request_class = VirtualHostRequest
    configuration = {}

    def configure_application(self, **configuration):
        """ Called by onegov.server with the configuration defined in the
        yaml file that's either passed to the onegov server script
        (development) or to the wsgi server.

        """
        self.configuration = configuration

    @cached_property
    def valid_hostname(self):
        """ Returns a regular expression matching all hostnames that may
        be handled by this application.

        """
        default = r'^(localhost|127.0.0.1)'
        return re.compile(self.configuration.get('valid_hostname') or default)

    def is_valid_hostname(self, hostname):
        """ Returns True if the given hostname may be handled by this
        application. If a hostname may not be handled, the application
        will return 403 - Forbidden.

        :hostname:
            The hostname to check.

        This method may be extend by subclasses to include dynamic checks.
        Note that this happens up to two times for every request, so you want
        this to be an efficient check.

        """
        return self.valid_hostname.match(hostname) and True or False

    def __call__(self, environ, start_response):
        """ Runs the same code that Morepath does, but runs some checks
        before actually responding to the request.

        """
        request = self.request(environ)

        # make sure the hostname may be served through this application
        # this is not necessarily needed - usually your webserver config
        # should make sure that these values can be trusted - but it's an
        # additional security measure for simple cases and a necessity if
        # you want to allow for catch-all hosting, where the customer can
        # select the domain the application should be served under
        #
        # see also https://github.com/OneGov/onegov.server/issues/1
        #
        # Django has something similar:
        # https://docs.djangoproject.com/en/1.7/ref/settings/#allowed-hosts
        hosts = (
            request.headers.get('HTTP_HOST'),
            request.headers.get('X_VHM_HOST')
        )

        for host in hosts:
            if host is not None:
                host = compat.urlparse(host).hostname

                if not self.is_valid_hostname(host):
                    return HTTPForbidden()(environ, start_response)

        return self.publish(request)(environ, start_response)
