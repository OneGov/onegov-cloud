from __future__ import annotations

from functools import cached_property
from onegov.agency import _
from onegov.ticket import TicketCollection


from typing import Any
from typing import Generic
from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.agency.collections import ExtendedAgencyCollection
    from onegov.agency.collections import ExtendedPersonCollection
    from onegov.core.orm import Base
    from onegov.ticket import Ticket
    from sqlalchemy.orm import Session
    from uuid import UUID

    from .agency import ExtendedAgency  # noqa: F401
    from .move import SupportsById
    from .person import ExtendedPerson  # noqa: F401


_M = TypeVar('_M', bound='Base')
_IdT_contra = TypeVar('_IdT_contra', bound='UUID | int')
_NOT_FOUND = object()

AGENCY_MUTATION_LABELS = {
    'title': _('Title'),
    'location_address': _('Location address'),
    'location_code_city': _('Location Code and City'),
    'postal_address': _('Postal address'),
    'postal_code_city': _('Postal Code and City'),
    'phone': _('Phone'),
    'phone_direct': _('Alternate Phone Number or Fax'),
    'email': _('E-Mail'),
    'website': _('Website'),
    'opening_hours': _('Opening hours'),
}


class Mutation(Generic[_M, _IdT_contra]):

    def __init__(
        self,
        session: Session,
        target_id: _IdT_contra,
        ticket_id: UUID
    ) -> None:
        self.session = session
        self.target_id = target_id
        self.ticket_id = ticket_id

    @cached_property
    def collection(self) -> SupportsById[_M, _IdT_contra]:
        raise NotImplementedError

    @cached_property
    def target(self) -> _M | None:
        return self.collection.by_id(self.target_id)

    @cached_property
    def ticket(self) -> Ticket | None:
        return TicketCollection(self.session).by_id(self.ticket_id)

    @cached_property
    def changes(self) -> dict[str, Any]:
        assert self.ticket is not None
        handler_data = self.ticket.handler_data['handler_data']
        result = handler_data.get('proposed_changes', {})
        result = {k: v for k, v in result.items() if hasattr(self.target, k)}
        return result

    @property
    def labels(self) -> dict[str, str]:
        return {}

    def apply(self, items: Iterable[str]) -> None:
        assert self.ticket is not None
        self.ticket.handler_data['state'] = 'applied'
        for item in items:
            value = self.changes.get(item, _NOT_FOUND)
            if value is not _NOT_FOUND:
                setattr(self.target, item, value)


class AgencyMutation(Mutation['ExtendedAgency', int]):

    @cached_property
    def collection(self) -> ExtendedAgencyCollection:
        from onegov.agency.collections import ExtendedAgencyCollection
        return ExtendedAgencyCollection(self.session)

    @property
    def labels(self) -> dict[str, str]:
        return {
            'title': _('Title'),
            'location_address': _('Location address'),
            'location_code_city': _('Location Code and City'),
            'postal_address': _('Postal address'),
            'postal_code_city': _('Postal Code and City'),
            'phone': _('Phone'),
            'phone_direct': _('Alternate Phone Number or Fax'),
            'email': _('E-Mail'),
            'website': _('Website'),
            'opening_hours': _('Opening hours'),
        }


class PersonMutation(Mutation['ExtendedPerson', 'UUID']):

    @cached_property
    def collection(self) -> ExtendedPersonCollection:
        from onegov.agency.collections import ExtendedPersonCollection
        return ExtendedPersonCollection(self.session)

    @property
    def labels(self) -> dict[str, str]:
        return {
            'title': _('Title'),
            'salutation': _('Salutation'),
            'academic_title': _('Academic Title'),
            'first_name': _('First name'),
            'last_name': _('Last name'),
            'function': _('Function'),
            'email': _('E-Mail'),
            'phone': _('Phone'),
            'phone_direct': _('Direct Phone Number or Mobile'),
            'born': _('Born'),
            'profession': _('Profession'),
            'political_party': _('Political Party'),
            'parliamentary_group': _('Parliamentary Group'),
            'website': _('Website'),
            'location_address': _('Location address'),
            'location_code_city': _('Location Code and City'),
            'postal_address': _('Postal address'),
            'postal_code_city': _('Postal Code and City'),
            'notes': _('Notes'),
        }
