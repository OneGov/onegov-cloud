from __future__ import annotations

import inspect

from onegov.server import errors


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from .application import Application
    from .config import ApplicationConfig


class CachedApplication:
    """ Wraps an application class with a configuration, returning a new
    instance the first time `get()` is called and the same instance very
    time after that.

    """

    instance: Application | None

    def __init__(
        self,
        application_class: type[Application],
        namespace: str,
        configuration: dict[str, Any] | None = None
    ):
        self.application_class = application_class
        self.configuration = configuration or {}
        self.namespace = namespace
        self.instance = None

    def get(self) -> Application:
        if self.instance is None:
            instance = self.application_class()
            instance.namespace = self.namespace
            instance.configure_application(**self.configuration)
            # NOTE: Only set the attribute after we successfully configured
            #       the application, since the server will continue operating
            #       after exceptions, we may otherwise end up with partially
            #       initialized application instances. It's better if we
            #       fail the same way each request.
            self.instance = instance
        return self.instance


class ApplicationCollection:
    """ Keeps a list of applications and their roots.

    The applications are registered lazily and only instantiated/configured
    once the `get()` is called.
    """

    applications: dict[str, CachedApplication]

    def __init__(
        self,
        applications: Iterable[ApplicationConfig] | None = None
    ):
        self.applications = {}

        for a in applications or ():
            self.register(
                a.root, a.application_class, a.namespace, a.configuration)

    def register(
        self,
        root: str,
        application_class: type[Application],
        namespace: str,
        configuration: dict[str, Any] | None = None
    ) -> None:
        """ Registers the given path for the given application_class and
        configuration.

        """

        if root in self.applications:
            raise errors.ApplicationConflictError(
                "tried to register '{}' twice".format(root))

        self.applications[root] = CachedApplication(
            application_class, namespace, configuration
        )

    def get(self, root: str) -> Application | None:
        """ Returns the applicaton for the given path, creating a new instance
        if none exists already.

        """
        application = self.applications.get(root)

        if application is None:
            return None
        else:
            return application.get()

    def morepath_applications(self) -> Iterator[CachedApplication]:
        """ Iterates through the applications that depend on morepath. """

        for app in self.applications.values():
            for base in inspect.getmro(app.application_class):
                if base.__module__.startswith('morepath.'):
                    yield app
                    break
