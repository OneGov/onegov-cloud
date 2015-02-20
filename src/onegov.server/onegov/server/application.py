import re


class Application(object):
    """ WSGI applications inheriting from this class can be served by
    onegov.server.

    """

    #: If the host passed by the request is not localhost, then it is
    #: checked against the allowed_hosts expression. If it doesn't match,
    #: the request is denied.
    allowed_hosts_expression = None

    #: Additional allowed hosts may be added to this set. Those are not
    #: expressions, but straight hostnames.
    allowed_hosts = None

    def __call__(self, environ, start_respnose):
        raise NotImplementedError

    def configure_application(self, **configuration):
        """ Called *once* when the application is instantiated, with the
        configuration values defined for this application.

        This will be called *before* set_application_base_path is called, as
        this happens *before* the request.

        Be sure to call this method from any subclasses you create. The server
        adds its own configuration here!

        """
        self.configuration = configuration

        if 'allowed_hosts_expression' in configuration:
            self.allowed_hosts_expression = re.compile(
                configuration['allowed_hosts_expression'])

        self.allowed_hosts = set(
            configuration.get('allowed_hosts', []))

    def set_application_id(self, application_id):
        """ Sets the application id before __call__ is called. That is, before
        each request.

        The application is is the last fragment of the base_path. That is
        `app` for all requests in the following config::

            {
                'applications': [
                    {
                        path: '/app'
                    }
                ]
            }

        And `blog` for a `/sites/blog` request in the following config::

            {
                'applications': [
                    {
                        path: '/sites/*'
                    }
                ]
            }
        """
        self.application_id = application_id

    def set_application_base_path(self, base_path):
        """ Sets the base path of the application before __call__ is called.
        That is, before each request.

        The base_path of static applications is equal to path the application
        was configured to run under.

        The base_path of wildcard applications includes the path matched
        by the wildcard. For example, if the application is configured to run
        under '/sites/*', the base_path would be `/sites/blog` if
        `/sites/blog/login` was requested.

        """
        self.application_base_path = base_path

    def is_allowed_hostname(self, hostname):
        """ Called at least once per request with the given hostname.

        If True is returned, the request with the given hostname is allowed.
        If False is returned, the request is denied.

        You usually won't need to override this method, as
        :attr:`allowed_hosts_expression` and :attr:`allowed_hosts` already
        gives you a way to influence its behavior.

        If you do override, it's all on you though (except for localhost
        requests).
        """

        if self.allowed_hosts_expression:
            if self.allowed_hosts_expression.match(hostname):
                return True

        return hostname in self.allowed_hosts
