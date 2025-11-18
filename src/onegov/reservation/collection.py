from __future__ import annotations

import enum

from onegov.core.utils import normalize_for_url
from onegov.reservation.models import Resource
from uuid import uuid4, UUID

from typing import overload, Any, Literal, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from libres.context.core import Context
    from libres.db.models import Allocation, Reservation
    from libres.db.scheduler import Scheduler

    from sqlalchemy.orm import Query, Session
    from typing import TypeAlias


_R = TypeVar('_R', bound=Resource)


class _Marker(enum.Enum):
    any_type = enum.auto()


any_type_t: TypeAlias = Literal[_Marker.any_type]  # noqa: PYI042
any_type: any_type_t = _Marker.any_type


class ResourceCollection:
    """ Manages a list of resources.

    """
    def __init__(self, libres_context: Context):
        assert hasattr(libres_context, 'get_service'), """
            The ResourceCollection expected the libres_contex, not the session.
        """

        self.libres_context = libres_context
        self.session = libres_context.get_service('session_provider').session()

    def query(self) -> Query[Resource]:
        return self.session.query(Resource)

    def add(
        self,
        title: str,
        timezone: str,
        type: str | None = None,
        name: str | None = None,
        meta: dict[str, Any] | None = None,
        content: dict[str, Any] | None = None,
        definition: str | None = None,
        group: str | None = None,
        subgroup: str | None = None,
    ) -> Resource:

        if type is None:
            resource = Resource()
        else:
            # look up the right class depending on the type (we need to do
            # this a bit akwardly here, because Resource does not use the
            # ModelBase as declarative base)
            resource = Resource.get_polymorphic_class(type, Resource)()

        resource.id = uuid4()
        resource.name = name or normalize_for_url(title)
        resource.title = title
        resource.timezone = timezone
        resource.meta = meta or {}
        resource.content = content or {}
        resource.definition = definition
        resource.group = group
        resource.subgroup = subgroup
        resource.renew_access_token()

        self.session.add(resource)
        self.session.flush()

        return self.bind(resource)

    @overload
    def bind(self, resource: _R) -> _R: ...
    @overload
    def bind(self, resource: None) -> None: ...

    def bind(self, resource: _R | None) -> _R | None:
        if resource:
            resource.bind_to_libres_context(self.libres_context)

        return resource

    def by_id(
        self,
        id: UUID,
        ensure_type: str | any_type_t = any_type
    ) -> Resource | None:

        query = self.query().filter(Resource.id == id)

        if ensure_type is not any_type:
            query = query.filter(Resource.type == ensure_type)

        return self.bind(query.first())

    def by_name(
        self,
        name: str,
        ensure_type: str | any_type_t = any_type
    ) -> Resource | None:

        query = self.query().filter(Resource.name == name)

        if ensure_type is not any_type:
            query = query.filter(Resource.type == ensure_type)

        return self.bind(query.first())

    def by_allocation(self, allocation: Allocation) -> Resource | None:
        return self.by_id(allocation.resource)

    def by_reservation(self, reservation: Reservation) -> Resource | None:
        return self.by_id(reservation.resource)

    def delete(
        self,
        resource: Resource,
        including_reservations: bool = False,
        handle_linked_objects: (
            Callable[[Scheduler, Session], Any] | None
        ) = None,
    ) -> None:

        scheduler = resource.get_scheduler(self.libres_context)

        if not including_reservations:
            assert not scheduler.managed_reserved_slots().first()
            assert not scheduler.managed_reservations().first()

            scheduler.managed_allocations().delete('fetch')
        else:
            if callable(handle_linked_objects):
                handle_linked_objects(scheduler, self.session)
            scheduler.extinguish_managed_records()

        if resource.files:
            # unlink any linked files
            resource.files = []
            self.session.flush()

        self.session.delete(resource)
        self.session.flush()
