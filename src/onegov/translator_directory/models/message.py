from __future__ import annotations

from functools import cached_property
from onegov.chat import Message
from onegov.org.models.message import TicketMessageMixin
from onegov.translator_directory.models.mutation import TranslatorMutation


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ticket import Ticket
    from onegov.translator_directory.request import TranslatorAppRequest
    from typing import Self


class TranslatorMutationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'translator_mutation'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: TranslatorAppRequest,
        change: str,
        changes: list[str]
    ) -> Self:
        return super().create(ticket, request, change=change, changes=changes)

    @cached_property
    def applied_changes(self) -> list[str]:
        changes = self.meta.get('changes', [])
        if changes:
            labels = TranslatorMutation.labels
            changes = [labels.get(change, change) for change in changes]
        return changes


class AccreditationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'translator_accreditation'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: TranslatorAppRequest,
        change: str
    ) -> Self:
        return super().create(ticket, request, change=change)
