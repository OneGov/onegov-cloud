from __future__ import annotations

from datetime import date
from functools import cached_property
from onegov.translator_directory.models.translator import Translator


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ticket import Ticket
    from sqlalchemy.orm import Session
    from uuid import UUID


class Accreditation:

    def __init__(
        self,
        session: Session,
        target_id: UUID,
        ticket_id: UUID
    ) -> None:
        self.session = session
        self.target_id = target_id
        self.ticket_id = ticket_id

    # FIXME: Should we force that both the ticket and translator exist?
    #        Rather than do the check inside grant/refuse
    @cached_property
    def target(self) -> Translator | None:
        return self.session.query(Translator).filter_by(
            id=self.target_id
        ).first()

    @cached_property
    def ticket(self) -> Ticket | None:
        from onegov.ticket import TicketCollection
        return TicketCollection(self.session).by_id(self.ticket_id)

    def grant(self) -> None:
        assert self.ticket is not None
        assert self.target is not None
        self.ticket.handler_data['state'] = 'granted'
        self.target.state = 'published'
        self.target.date_of_decision = date.today()

    def refuse(self) -> None:
        assert self.ticket is not None
        self.ticket.handler_data['state'] = 'refused'
        self.session.delete(self.target)
