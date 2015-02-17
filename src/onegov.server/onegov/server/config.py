import inspect
import pydoc
import yaml


class Config(object):
    """ Represents the configuration of the server. """

    def __init__(self, configuration):
        """ Load the given configuration, which is expected to look thusly:

            {
                'applications': [
                    {
                        'path': '/application',
                        'class': 'my.module.StaticApp',
                        'configuration': {
                            'my': 'custom',
                            'config': 'values'
                        }
                    },
                    {
                        'path': '/sites/*',
                        'class': 'my.module.WildcardApp',
                    }
                ]
            }

        There are two types of applications, static applications without a
        wildcard (*) in their path. And wildcard applications with a wildcard
        in their path.

        Static applications exist once. Wildcard applications exist
        once for every path. That is to say `/sites/one` and `/sites/two` in
        the example above are two different applications and a path of
        `/sites/one/login` is passed to WildcardApp as `/login`, while
        `/application/one/login` is passed to StaticApp as `/one/login`.

        Note that the `class` may be a string or a class. If it's a string
        the class is dynamically loaded immediately.

        Nested paths are *not* supported. So `/namespace/path` is invalid.

        """
        self.applications = [
            ApplicationConfig(a) for a in configuration.get('applications')
        ]

    @staticmethod
    def from_yaml_file(yaml_file):
        """ Load the given yaml file and return a new Configuration instance
        with the configuration values found in the yaml file.

        """
        with open(yaml_file, 'r') as f:
            return Config(yaml.load(f.read()))


class ApplicationConfig(object):
    """ Represents an application config entry. """

    __slots__ = ['_cfg']

    def __init__(self, configuration):
        self._cfg = configuration

        assert self.path.count('*') <= 1
        assert self.path.count('/') <= 2
        assert self.path.startswith('/')

    @property
    def path(self):
        return self._cfg['path'].rstrip('/')

    @property
    def application_class(self):
        if inspect.isclass(self._cfg['class']):
            return self._cfg['class']
        else:
            return pydoc.locate(self._cfg['class'])

    @property
    def configuration(self):
        return self._cfg.get('configuration', {})

    @property
    def root(self):
        """ The path without the wildcard such that '/app' and '/app/*' produce
        the same root (/app).

        """
        return self.path.rstrip('/*')

    @property
    def is_static(self):
        """ True if the application is static (has no '*' in the path). """
        return '*' not in self.path
