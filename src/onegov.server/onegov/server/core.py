import logging.config

from onegov.server.collection import ApplicationCollection
from webob import BaseRequest
from webob.exc import HTTPNotFound, HTTPForbidden

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


local_hostnames = {
    '127.0.0.1',
    '::1',
    'localhost'
}


class Request(BaseRequest):

    hostname_keys = ('HTTP_HOST', 'HTTP_X_VHM_HOST')

    @property
    def hostnames(self):
        """ Iterates through the hostnames of the request. """
        for key in self.hostname_keys:
            if key in self.environ:
                hostname = urlparse(self.environ[key]).hostname

                if hostname is None:
                    yield self.environ[key].split(':')[0]
                else:
                    yield hostname


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

    If morepath autoconfig is not desired, set ``configure_morepath`` to False.

    """

    def __init__(self, config, configure_morepath=True):
        self.applications = ApplicationCollection(config.applications)
        self.wildcard_applications = set(
            a.root for a in config.applications if not a.is_static)

        self.configure_logging(config.logging)

        if configure_morepath:
            self.configure_morepath()

    def configure_logging(self, config):
        """ Configures the python logging.

        :config:
            A dictionary that is understood by python's
            `logging.config.dictConfig` method.

        """
        config.setdefault('version', 1)
        logging.config.dictConfig(config)

    def configure_morepath(self):
        """ Configures morepath automatically, if any application uses it. """

        morepath_applications = set(
            self.applications.morepath_applications())

        if morepath_applications:
            # morepath is only loaded if required by an application
            import importlib
            import morepath

            from morepath.autosetup import DependencyMap

            # we do our own autosetup to avoid this issue (for now):
            # https://github.com/morepath/morepath/issues/319
            # the next release or morepath will be smarter in this regard
            # and we'll be able to change this code

            m = DependencyMap()
            m.load()

            config = morepath.setup()

            for dist in m.relevant_dists('morepath'):

                if hasattr(dist, 'get_entry_map'):
                    entry_points = dist.get_entry_map('morepath')
                else:
                    entry_points = None

                if entry_points and 'scan' in entry_points:
                    module_name = entry_points['scan'].module_name
                else:
                    module_name = dist.project_name

                # likewise, the config scan will exclude '.test', '.tests'
                # by default
                config.scan(
                    importlib.import_module(module_name),
                    ignore=['.test', '.tests'])

            config.commit()

    def __call__(self, environ, start_response):
        request = Request(environ)
        path_fragments = request.path.split('/')

        # try to find the application that handles this path
        application_root = '/'.join(path_fragments[:2])
        application = self.applications.get(application_root)

        if application is None:
            return HTTPNotFound()(environ, start_response)

        # make sure the application accepts the given hostname
        for host in request.hostnames:
            if host not in local_hostnames:
                if not application.is_allowed_hostname(host):
                    return HTTPForbidden()(environ, start_response)

        if application_root in self.wildcard_applications:
            base_path = '/'.join(path_fragments[:3])
            application_id = ''.join(path_fragments[2:3])

            # dealias the application id
            if application_id in application._aliases:
                application_id = application._aliases[application_id]

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
        application.set_application_id(
            application.namespace + '/' + application_id)

        return application(environ, start_response)
