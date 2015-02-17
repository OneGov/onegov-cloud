from onegov.server import errors


class CachedApplication(object):
    """ Wraps an application class with a configuration, returning a new
    instance the first time `get()` is called and the same instance very
    time after that.

    """

    def __init__(self, application_class, configuration={}):
        self.application_class = application_class
        self.configuration = configuration
        self.instance = None

    def get(self):
        if self.instance is None:
            self.instance = self.application_class()
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
            self.register(a.root, a.application_class, a.configuration)

    def register(self, root, application_class, configuration={}):
        """ Registers the given path for the given application_class and
        configuration.

        """

        if root in self.applications:
            raise errors.ApplicationConflictError(
                "tried to register '{}' twice".format(root))

        self.applications[root] = CachedApplication(
            application_class, configuration
        )

    def alias(self, root, alias):
        """ Creates an alias for the given path. For example:

            collection.register('app', Class)
            collection.alias('app', 'alias')

            assert collection.get('alias') is collection.get('app')
        """
        self.applications[alias] = self.applications[root]

    def get(self, root):
        """ Returns the applicaton for the given path, creating a new instance
        if none exists already.

        """
        return self.applications[root].get()
