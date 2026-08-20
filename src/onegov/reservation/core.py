from __future__ import annotations

from libres.context.registry import create_default_registry
from libres.db.models import ORMBase
from onegov.core.orm import orm_cached
from onegov.reservation.collection import ResourceCollection
from onegov.reservation.models.resource import blocking_resources_table
from onegov.reservation.pricing_scheme import PRICING_SCHEMES
from uuid import UUID


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection
    from libres.context.core import Context
    from libres.context.registry import Registry
    from onegov.core.orm.session_manager import SessionManager
    from onegov.reservation.pricing_scheme import ResourcePricingScheme
else:
    # HACK: Monkeypatch libres' JSON type processor with ours
    from libres.db.models.types import JSON as _LibresJSON  # ruff:ignore[constant-imported-as-non-constant]
    from onegov.core.orm.types import JSON as _OnegGovJSON  # ruff:ignore[constant-imported-as-non-constant]

    _LibresJSON.process_bind_param = _OnegGovJSON.process_bind_param
    _LibresJSON.process_result_value = _OnegGovJSON.process_result_value


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
        application_id: str

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

    def configure_resource_pricing_schemes(
        self,
        *,
        resource_pricing_schemes: dict[str, list[str]] | None = None,
        **cfg: Any
    ) -> None:
        self.available_resource_pricing_schemes = {
            tenant: tuple(PRICING_SCHEMES[name] for name in names)
            for tenant, names in resource_pricing_schemes.items()
        } if resource_pricing_schemes else {}

    @property
    def resource_pricing_schemes(
        self
    ) -> tuple[type[ResourcePricingScheme], ...]:
        return getattr(self, 'available_resource_pricing_schemes', {}).get(
            self.application_id,
            ()
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
        child_to_parents: dict[UUID, set[UUID]] = {}
        parent_to_children: dict[UUID, set[UUID]] = {}
        all_blocking_resources: dict[UUID, set[UUID]] = {}
        for child_id, parent_id in session.query(
            blocking_resources_table.c.child_id,
            blocking_resources_table.c.parent_id
        ):
            # NOTE: libres gives us SoftUUIDs, which are not msgpack
            #       serializable, so we convert it to the base class
            child_id = UUID(int=child_id.int)
            all_blocking_resources[child_id] = set()
            parent_id = UUID(int=parent_id.int)
            child_to_parents.setdefault(child_id, set()).add(parent_id)
            parent_to_children.setdefault(parent_id, set()).add(child_id)

        def walk_children(resource_id: UUID) -> None:
            for child_id in parent_to_children.get(resource_id, ()):
                if child_id in blocking_resources or child_id == target_id:
                    # NOTE: This means we have a cycle in our dependencies
                    #       so we don't need to walk this again, cycles
                    #       should be harmless, even if not ideal.
                    continue

                blocking_resources.add(child_id)
                walk_children(child_id)

        def walk_parents(resource_id: UUID) -> None:
            for parent_id in child_to_parents.get(resource_id, ()):
                if parent_id in blocking_resources or parent_id == target_id:
                    # NOTE: This means we have a cycle in our dependencies
                    #       so we don't need to walk this again, cycles
                    #       should be harmless, even if not ideal.
                    return

                blocking_resources.add(parent_id)
                walk_parents(parent_id)

        for target_id, blocking_resources in all_blocking_resources.items():
            walk_children(target_id)
            walk_parents(target_id)

        return {
            resource_id.hex: frozenset(blocking)
            for resource_id, blocking in all_blocking_resources.items()
        }

    def get_ancestor_resource_ids(self, resource: UUID) -> tuple[UUID, ...]:
        """ This returns the ancestors ids in reverse hierarchical order.

        I.e. first you get the parents, then the grandparents, etc.

        Resources sharing the same generation will be returned in
        an arbitrary order.

        """
        return self._ancestor_resource_id_mapping.get(resource.hex, ())

    @orm_cached(policy='on-table-change:resources')
    def _ancestor_resource_id_mapping(self) -> dict[str, tuple[UUID, ...]]:
        session = self.session_manager.session()
        child_to_parents: dict[UUID, list[UUID]] = {}
        all_ancestor_resources: dict[UUID, list[UUID]] = {}
        for child_id, parent_id in session.query(
            blocking_resources_table.c.child_id,
            blocking_resources_table.c.parent_id
        ).order_by(blocking_resources_table.c.parent_id):
            # NOTE: libres gives us SoftUUIDs, which are not msgpack
            #       serializable, so we convert it to the base class
            child_id = UUID(int=child_id.int)
            all_ancestor_resources[child_id] = []
            parent_id = UUID(int=parent_id.int)
            child_to_parents.setdefault(child_id, []).append(parent_id)

        def walk_parents(resource_id: UUID) -> None:
            for parent_id in child_to_parents.get(resource_id, ()):
                if parent_id in ancestor_resources or parent_id == target_id:
                    # NOTE: This means we have a cycle in our dependencies
                    #       so we don't need to walk this again, cycles
                    #       should be harmless, even if not ideal.
                    return

                ancestor_resources.append(parent_id)
                walk_parents(parent_id)

        for target_id, ancestor_resources in all_ancestor_resources.items():
            walk_parents(target_id)

        return {
            resource_id.hex: tuple(ancestors)
            for resource_id, ancestors in all_ancestor_resources.items()
        }
