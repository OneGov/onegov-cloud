from onegov.server.collection import ApplicationCollection
from webob import BaseRequest
from webob.exc import HTTPNotFound


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
        self.wildcard_applications = set(
            a.root for a in config.applications if not a.is_static)

    def __call__(self, environ, start_response):
        request = BaseRequest(environ)
        path_fragments = request.path.split('/')

        application_root = '/'.join(path_fragments[:2])
        application = self.applications.get(application_root)

        if application is None:
            return HTTPNotFound()(environ, start_response)

        if application_root in self.wildcard_applications:
            application_id = ''.join(path_fragments[2:3])
            base_path = '/'.join(path_fragments[:3])
        else:
            application_id = ''.join(path_fragments[1:2])
            base_path = application_root

        if not application_id:
            return HTTPNotFound()(environ, start_response)

        application.set_application_base_path(base_path)
        application.set_application_id(application_id)

        return application(environ, start_response)
