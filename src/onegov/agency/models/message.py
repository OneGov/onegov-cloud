from __future__ import annotations

from onegov.chat import Message
from onegov.org.models.message import TicketMessageMixin


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.request import AgencyRequest
    from onegov.ticket import Ticket
    from typing import Self


class AgencyMutationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'agency_mutation'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: AgencyRequest,
        change: str
    ) -> Self:
        return super().create(ticket, request, change=change)


class PersonMutationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'person_mutation'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: AgencyRequest,
        change: str
    ) -> Self:
        return super().create(ticket, request, change=change)
