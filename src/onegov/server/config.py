from __future__ import annotations

import yaml

from onegov.server import errors
from onegov.server.utils import load_class


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath
    from typing import Self

    from .application import Application


class Config:
    """ Represents the configuration of the server. """

    def __init__(self, configuration: dict[str, Any]):
        """ Load the given configuration, which is a list of dictionaries.
        Each dictionary is loaded by the :class:`ApplicationConfig` class.

        See :class:`ApplicationConfig` for a documentation of all configuration
        values.

        """
        self.applications = [
            ApplicationConfig(a)
            for a in configuration.get('applications', ())
        ]
        self.mail_queues = configuration.get('mail_queues', {})
        self.logging = configuration.get('logging', {})

        all_namespaces = [a.namespace for a in self.applications]
        unique_namespaces = set(all_namespaces)

        if len(unique_namespaces) != len(all_namespaces):
            raise errors.ApplicationConflictError(
                'Not all namespaces are unique')

    @classmethod
    def from_yaml_file(cls, yaml_file: StrOrBytesPath) -> Self:
        """ Load the given yaml file and return a new Configuration instance
        with the configuration values found in the yaml file.

        """
        with open(yaml_file) as fp:
            return cls(yaml.safe_load(fp))

    @classmethod
    def from_yaml_string(cls, yaml_string: str | bytes) -> Self:
        """ Load the given yaml string and return a new Configuration instance
        with the configuration values found in the yaml string.

        """
        return cls(yaml.safe_load(yaml_string))


class ApplicationConfig:
    """ Represents an application config entry loaded from a dictionary like
    this::

        {
            'path': '/application',
            'application': 'my.module.StaticApp',
            'namespace': 'my-namespace'
            'configuration': {
                'my': 'custom',
                'config': 'values'
            }
        }

    It may contain the following keys:

    :path:
        The path of the application is the prefix under which the application
        is running. For each path onegov.server loads and caches an
        application.

        Applications are basically WSGI containers that are run independently
        in the same process.

        See :class:`~.application.Application` for more.

        There are two types of applications, static applications without a
        wildcard (`*`) in their path and wildcard applications *with* a
        wildcard in their path.

        Static applications always have the same application_id (`ns/static`,
        if the path is `/static` and the namespace is `ns`).

        Wildcard applications have the application_id set to the wildcard
        part of the path: (`/wildcard/*` can result in an applicaiton_id of
        `ns/blog` if `/wildcard/blog` is opened and the namespace is `ns`).

        See also: :meth:`~.application.Application.set_application_id`.

        Nested paths are not supported. `/static` works and `/wildcard/*`
        works, but not `/static/site` or `/wildcard/site/*`.

    :application:
        The application class or string to an application class that inherits
        from :class:`~.application.Application`.

        If `application` is a string, the class it points to is loaded
        immediately.

    :namespace:
        Each application has a namespace that must be unique. It is used
        make the application_id unique. Dashes in the namespace are replaced
        by underscores.

    :configuration:
        A dictionary that is passed to the application once it is initialized.
        See :meth:`.application.Application.configure_application`.
    """

    __slots__ = ('_cfg',)

    def __init__(self, configuration: dict[str, Any]):
        self._cfg = configuration

        assert self.path != '/'
        assert self.path.count('*') <= 1
        assert self.path.count('/') <= 2
        assert self.path.startswith('/')

        assert '/' not in self.namespace

    @property
    def path(self) -> str:
        return self._cfg['path'].rstrip('/')

    @property
    def namespace(self) -> str:
        return self._cfg['namespace'].replace('-', '_')

    @property
    def application_class(self) -> type[Application]:
        application_class = load_class(self._cfg['application'])

        if application_class is None:
            raise errors.ApplicationConfigError(
                'The application class could not be found.')

        return application_class

    @property
    def configuration(self) -> dict[str, Any]:
        return self._cfg.get('configuration', {})

    @property
    def root(self) -> str:
        """ The path without the wildcard such that `/app` and `/app/*` produce
        the same root (`/app`).

        """
        return self.path.rstrip('/*')

    @property
    def is_static(self) -> bool:
        """ True if the application is static (has no '*' in the path). """
        return '*' not in self.path
