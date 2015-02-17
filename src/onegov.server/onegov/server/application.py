class Application(object):
    """ WSGI applications inheriting from this class can be served by
    onegov.server.

    """

    def __call__(self, environ, start_respnose):
        raise NotImplementedError

    def configure_application(self, **configuration):
        """ Called *once* when the application is instantiated, with the
        configuration values defined for this application.

        This will be called *before* set_application_base_path is called, as
        this happens *before* the request.

        """
        pass

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
