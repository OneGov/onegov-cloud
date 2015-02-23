import inspect

from onegov.server import errors


class CachedApplication(object):
    """ Wraps an application class with a configuration, returning a new
    instance the first time `get()` is called and the same instance very
    time after that.

    """

    def __init__(self, application_class, namespace, configuration={}):
        self.application_class = application_class
        self.configuration = configuration
        self.namespace = namespace
        self.instance = None

    def get(self):
        if self.instance is None:
            self.instance = self.application_class()
            self.instance.namespace = self.namespace
            self.instance.configure_application(**self.configuration)
        return self.instance


class ApplicationCollection(object):
    """ Keeps a list of applications and their roots.

    The applications are registered lazily and only instantiated/configured
    once the `get()` is called.
    """

    def __init__(self, applications=None):
        self.applications = {}

        for a in applications or []:
            self.register(
                a.root, a.application_class, a.namespace, a.configuration)

    def register(self, root, application_class, namespace, configuration={}):
        """ Registers the given path for the given application_class and
        configuration.

        """

        if root in self.applications:
            raise errors.ApplicationConflictError(
                "tried to register '{}' twice".format(root))

        self.applications[root] = CachedApplication(
            application_class, namespace, configuration
        )

    def get(self, root):
        """ Returns the applicaton for the given path, creating a new instance
        if none exists already.

        """
        application = self.applications.get(root)

        if application is None:
            return None
        else:
            return application.get()

    def morepath_applications(self):
        """ Iterates through the applications that depend on morepath. """

        for app in self.applications.values():
            for base in inspect.getmro(app.application_class):
                if base.__module__.startswith('morepath.'):
                    yield app
                    break
