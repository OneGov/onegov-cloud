class Application(object):
    """ WSGI applications inheriting from this class can be served by
    onegov.server.

    """

    def __call__(self, environ, start_respnose):
        raise NotImplementedError

    def configure_application(self, **configuration):
        """ Called *once* when the application is instantiated, with the
        configuration values defined for this application.

        """
        pass
