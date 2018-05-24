import re

from onegov.server import errors


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

    #: The namespace of the application, set before the application is
    #: configured in :meth:`configure_application`.
    namespace = None

    #: Use :meth:`alias` instead of manipulating this dictionary.
    _aliases = None

    def __call__(self, environ, start_respnose):
        raise NotImplementedError

    def configure_application(self, **configuration):
        """ Called *once* when the application is instantiated, with the
        configuration values defined for this application.

        This will be called *before* :meth:`set_application_base_path` is
        called, as this happens *before* the request.

        Be sure to call this method from any subclasses you create. The server
        adds its own configuration here!

        """
        self.configuration = configuration

        if 'allowed_hosts_expression' in configuration:
            self.allowed_hosts_expression = re.compile(
                configuration['allowed_hosts_expression'])

        self.allowed_hosts = set(
            configuration.get('allowed_hosts', []))

        self._aliases = {}

    def set_application_id(self, application_id):
        """ Sets the application id before __call__ is called. That is, before
        each request.

        The application id consists of two values, delimitd by a '/'. The first
        value is the namespace of the application, the second value is the
        last fragment of the base_path.

        That is `namespace/app` for all requests in the following config::

            {
                'applications': [
                    {
                        path: '/app',
                        namespace: 'namespace'
                    }
                ]
            }

        And `namespace/blog` for a `/sites/blog` request in the following
        config::

            {
                'applications': [
                    {
                        path: '/sites/*',
                        namespace: 'namespace'
                    }
                ]
            }
        """
        assert application_id.startswith(self.namespace + '/')
        self.application_id = application_id

    def set_application_base_path(self, base_path):
        """ Sets the base path of the application before __call__ is called.
        That is, before each request.

        The base_path of static applications is equal to path the application
        was configured to run under.

        The base_path of wildcard applications includes the path matched
        by the wildcard. For example, if the application is configured to run
        under `/sites/*`, the base_path would be `/sites/blog` if
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

    def is_allowed_application_id(self, application_id):
        """ Called at least once per request with the given application id.

        If True is returned, the request with the given application_id is
        allowed. If False is returned, the request is denied.

        By default, all application ids are allowed.

        """

        return True

    def alias(self, application_id, alias):
        """ Adds an alias under which this application is available on the
        server.

        The alias only works for wildcard applications - it has no effect
        on static applications!

        This is how it works:

        An application running under `/sites/main` can be made available
        under `/sites/blog` by running `self.alias('main', 'blog')`.

        Aliases must be unique, so this method will fail with a
        :class:`onegov.server.errors.ApplicationConflictError` if an alias
        is already in use by another application running under the same path.

        Note that an application opened through an alias will still have
        the application_id set to the actual root, not the alias. So
        `/sites/blog` in the example above would still lead to an
        application_id of `main` instead of `blog`.

        This is mainly meant to be used for dynamic DNS setups. Say you have
        an application available through test.onegov.dev (pointing to
        `/sites/test`). You now want to make this site available through
        example.org. You can do this as follows::

            self.allowed_hosts.add('example.org')
            self.alias('example_org')

        If your server has a catch-all rule that sends unknown domains to
        `/sites/domain_without_dots`, then you can add domains dynamically
        and the customer just points the DNS to your ip address.
        """
        if alias in self._aliases:
            raise errors.ApplicationConflictError(
                "the alias '{}' is already in use".format(alias))

        self._aliases[alias] = application_id

    def handle_exception(self, exception, environ, start_response):
        """ Default exception handling - this can be used to return a different
        response when an unhandle exception occurs inside a request or before
        a request is handled by the application (when any of the above methods
        are called).

        By default we just raise the exception.

        Typically, returning an error is what you might want to do::

            def handle_exception(exception, environ, start_response):
                if isinstance(exception, UnderMaintenanceError):
                    error = webob.exc.HTTPInternalServerError()
                    return error(environ, start_response)

        """

        raise exception
