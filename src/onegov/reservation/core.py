from __future__ import annotations

from libres.context.registry import create_default_registry
from libres.db.models import ORMBase
from onegov.reservation.collection import ResourceCollection
from uuid import UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from libres.context.core import Context
    from libres.context.registry import Registry
    from onegov.core.orm.session_manager import SessionManager


class LibresIntegration:
    """ Provides libres integration for
    :class:`onegov.core.framework.Framework` based applications.

    The application must be connected to a database

    Usage::

        from onegov.core import Framework

        class MyApp(Framework, LibresIntegration):
            pass

    """

    if TYPE_CHECKING:
        # necessary forward declaration
        # provided by onegov.core.framework.Framework
        session_manager: SessionManager

    def configure_libres(self, **cfg: Any) -> None:
        """ Configures the libres integration and leaves two properties on
        the class:

        :libres_context:
            The libres context configured for the current application.

        :libres_registrye:
            The libres registry bound to the current application.

        With those two a scheduler can easily be created::

            from libres import new_scheduler
            scheduler = new_scheduler(
                app.libres_context, 'test', 'Europe/Zurich'
            )

        """

        assert ORMBase in self.session_manager.bases, (
            'Must be run after configure_dsn')

        self.libres_registry = create_default_registry()
        self.libres_context = self.libres_context_from_session_manager(
            self.libres_registry,
            self.session_manager
        )

    @staticmethod
    def libres_context_from_session_manager(
        registry: Registry,
        session_manager: SessionManager
    ) -> Context:

        if registry.is_existing_context('onegov.reservation'):
            return registry.get_context('onegov.reservation')

        context = registry.register_context('onegov.reservation')
        context.set_service('session_provider', lambda ctx: session_manager)

        # onegov.reservation uses uuids for the resources, so we don't need to
        # generate anything, we can just reuse the id (which is passed as the
        # name)
        def uuid_generator(name: UUID) -> UUID:
            assert isinstance(name, UUID)
            return name

        context.set_service('uuid_generator', lambda ctx: uuid_generator)

        return context

    @property
    def libres_resources(self) -> ResourceCollection:
        return ResourceCollection(self.libres_context)
