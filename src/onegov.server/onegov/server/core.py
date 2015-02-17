from onegov.server.collection import ApplicationCollection


class Server(object):
    """ A WSGI application that hosts multiple Morepath applications in the
    same process.

    Not to be confused with Morepath's mounting functionality. The morepath
    applications hosted by this WSGI application are root applications, not
    mounted applications.

    See `Morepath's way of nesting applications
    <http://morepath.readthedocs.org/en/latest/app_reuse.html
    #nesting-applications>`_

    """

    def __init__(self, config):
        self.applications = ApplicationCollection(config.applications)

    def __call__(self, environ, start_response):
        pass
