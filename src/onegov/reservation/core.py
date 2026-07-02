from __future__ import annotations

from libres.context.registry import create_default_registry
from libres.db.models import ORMBase
from onegov.core.orm import orm_cached
from onegov.reservation.collection import ResourceCollection
from onegov.reservation.models import Resource
from uuid import UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection
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
            self.session_manager,
            self.get_blocking_resource_ids
        )

    @staticmethod
    def libres_context_from_session_manager(
        registry: Registry,
        session_manager: SessionManager,
        get_blocking_resource_ids: Callable[[UUID], Collection[UUID]]
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

        context.set_service(
            'get_blocking_resource_ids',
            lambda ctx: get_blocking_resource_ids
        )

        return context

    @property
    def libres_resources(self) -> ResourceCollection:
        return ResourceCollection(self.libres_context)

    def get_blocking_resource_ids(self, resource: UUID) -> Collection[UUID]:
        return self._blocking_resource_id_mapping.get(resource.hex, ())

    @orm_cached(policy='on-table-change:resources')
    def _blocking_resource_id_mapping(self) -> dict[str, frozenset[UUID]]:
        session = self.session_manager.session()
        child_to_parent: dict[UUID, UUID] = {}
        parent_to_children: dict[UUID, set[UUID]] = {}
        all_blocking_resources: dict[UUID, set[UUID]] = {}
        for child_id, parent_id in session.query(
            Resource.id,
            Resource.parent_id
        ):
            # NOTE: libres gives us SoftUUIDs, which are not msgpack
            #       serializable, so we convert it to the base class
            child_id = UUID(int=child_id.int)
            all_blocking_resources[child_id] = set()
            if parent_id is None:
                continue
            parent_id = UUID(int=parent_id.int)
            child_to_parent[child_id] = parent_id
            parent_to_children.setdefault(parent_id, set()).add(child_id)

        def walk_children(resource_id: UUID) -> None:
            for child_id in parent_to_children.get(resource_id, ()):
                if child_id in blocking_resources:
                    # NOTE: This means we have a cycle in our dependencies
                    #       so we don't need to walk this again, cycles
                    #       should be harmless, even if not ideal.
                    continue

                if child_id == target_id:
                    # NOTE: This could also happen with cycles, we don't
                    #       need to explicitly block ourselves, we already
                    #       do that, so we can ignore it.
                    continue

                blocking_resources.add(child_id)
                walk_children(child_id)

        def walk_parents(resource_id: UUID | None) -> None:
            if resource_id is None:
                return

            if resource_id in blocking_resources or resource_id == target_id:
                # NOTE: This means we have a cycle in our dependencies
                #       so we don't need to walk this again, cycles
                #       should be harmless, even if not ideal.
                return

            blocking_resources.add(resource_id)
            walk_parents(child_to_parent.get(resource_id))

        for target_id, blocking_resources in all_blocking_resources.items():
            walk_children(target_id)
            walk_parents(child_to_parent.get(target_id))

        return {
            resource_id.hex: frozenset(blocking)
            for resource_id, blocking in all_blocking_resources.items()
        }
