import pydoc

from onegov.server.collection import ApplicationCollection
from webob import BaseRequest
from webob.exc import HTTPNotFound


class Server(object):
    """ A WSGI application that hosts multiple WSGI applications in the
    same process.

    Not to be confused with Morepath's mounting functionality. The morepath
    applications hosted by this WSGI application are root applications, not
    mounted applications.

    See `Morepath's way of nesting applications
    <http://morepath.readthedocs.org/en/latest/app_reuse.html
    #nesting-applications>`_

    Applications are hosted in two ways:

    1. As static applications under a base path (`/app`)
    2. As wildcard applications under a base path with wildcard (`/sites/*`)

    There is no further nesting and there is no way to run an application
    under `/`.

    The idea for this server is to run a number of WSGI applications that
    are relatively independent, but share a common framework. Though thought
    to be used with Morepath this module does not try to assume anything but
    a WSGI application.

    Since most of the time we *will* be running morepath applications, this
    server automatically configures morepath for the applications that depend
    on it.

    """

    def __init__(self, config):
        self.applications = ApplicationCollection(config.applications)
        self.wildcard_applications = set(
            a.root for a in config.applications if not a.is_static)

        self.configure_morepath()

    def configure_morepath(self):
        """ Configures morepath automatically, if any application uses it. """

        morepath_applications = set(
            self.applications.morepath_applications())

        if morepath_applications:

            # it's safe to say that we got morepath available here
            import morepath

            config = morepath.setup()
            for app in morepath_applications:
                config.scan(pydoc.locate(app.application_class.__module__))
            config.commit()

    def __call__(self, environ, start_response):
        request = BaseRequest(environ)
        path_fragments = request.path.split('/')

        application_root = '/'.join(path_fragments[:2])
        application = self.applications.get(application_root)

        if application is None:
            return HTTPNotFound()(environ, start_response)

        if application_root in self.wildcard_applications:
            base_path = '/'.join(path_fragments[:3])
            application_id = ''.join(path_fragments[2:3])
        else:
            base_path = application_root
            application_id = ''.join(path_fragments[1:2])

        # happens if the root of a wildcard path is requested
        # ('/wildcard' from '/wildcard/*') - this is not allowed
        if not application_id:
            return HTTPNotFound()(environ, start_response)

        environ['PATH_INFO'] = request.path[len(base_path):]
        environ['SCRIPT_NAME'] = base_path

        application.set_application_base_path(base_path)
        application.set_application_id(application_id)

        return application(environ, start_response)
