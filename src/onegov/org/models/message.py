from __future__ import annotations

from functools import cached_property
from onegov.chat import Message
from onegov.core.elements import Link, Confirm, Intercooler
from onegov.core.utils import paragraphify, linkify
from onegov.event import Event
from onegov.org import _
from onegov.org.utils import hashtag_elements
from onegov.ticket import Ticket, TicketCollection
from sqlalchemy.orm import object_session


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from libres.db.models import Reservation
    from onegov.chat.collections import MessageCollection
    from onegov.directory import Directory
    from onegov.file import File
    from onegov.org.layout import DefaultLayout
    from onegov.org.request import OrgRequest
    from onegov.pay import Payment
    from sqlalchemy import Column
    from sqlalchemy.orm import Session
    from typing import Self

# 👉 when adding new ticket messages be sure to evaluate if they should
# be added to the ticket status page through the org.public_ticket_messages
# setting


class TicketMessageMixin:

    if TYPE_CHECKING:
        meta: Column[dict[str, Any]]

        @classmethod
        def bound_messages(cls, session: Session) -> MessageCollection[Any]:
            ...

    def link(self, request: OrgRequest) -> str:
        return request.class_link(Ticket, {
            'id': self.meta['id'],
            'handler_code': self.meta['handler_code'],
        })

    @cached_property
    def ticket(self) -> Ticket | None:
        return TicketCollection(object_session(self)).by_id(
            self.meta['id'],
            self.meta['handler_code']
        )

    @classmethod
    def create(
        cls,
        ticket: Ticket,
        request: OrgRequest,
        text: str | None = None,
        owner: str | None = None,
        **extra_meta: Any
    ) -> Self:

        meta = {
            'id': ticket.id.hex,
            'handler_code': ticket.handler_code,
            'group': ticket.group
        }
        meta.update(extra_meta)

        # force a change of the ticket to make sure that it gets reindexed
        ticket.force_update()

        # the owner can be forced to a specific value
        owner = owner or request.current_username or ticket.ticket_email

        return cls.bound_messages(request.session).add(
            channel_id=ticket.number,
            owner=owner,
            text=text,
            meta=meta
        )


class TicketNote(Message, TicketMessageMixin):
    __mapper_args__ = {
        'polymorphic_identity': 'ticket_note'
    }

    if TYPE_CHECKING:
        # text is not optional for TicketNote
        text: Column[str]

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: OrgRequest,
        text: str,
        file: File | None = None,
        owner: str | None = None,
        origin: str = 'internal'
    ) -> Self:
        note = super().create(ticket, request, text=text, owner=owner,
                              origin=origin)
        note.file = file

        return note

    def formatted_text(self, layout: DefaultLayout) -> str:
        return hashtag_elements(
            layout.request, paragraphify(linkify(self.text)))

    def links(self, layout: DefaultLayout) -> Iterator[Link]:
        # unprivileged members can only modify their own notes
        if (
            self.owner != layout.request.current_username
            and not layout.request.is_manager_for_model(self.ticket)
        ):
            return

        yield Link(_('Edit'), layout.request.link(self, 'edit'))
        yield Link(
            _('Delete'), layout.csrf_protected_url(layout.request.link(self)),
            traits=(
                Confirm(
                    _('Do you really want to delete this note?'),
                    _('This cannot be undone.'),
                    _('Delete Note'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=layout.request.link(self.ticket)
                )
            ))


class TicketChatMessage(Message, TicketMessageMixin):
    """ Chat messages sent between the person in charge of the ticket and
    the submitter of the ticket.

    Paramters of note:

    - origin: 'external' or 'internal', to differentiate between the
              messages sent from the organisation to someone outside or
              from someone outside to someone inside.

    - notify: only relevant for messages originating from 'internal' - if the
              last sent message with origin 'internal' has this flag, a
              notification is sent to the owner of that message, whenever
              a new external reply comes in.

    """

    __mapper_args__ = {
        'polymorphic_identity': 'ticket_chat'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: OrgRequest,
        text: str,
        owner: str,
        origin: str,
        notify: bool = False,
        recipient: str | None = None
    ) -> Self:

        return super().create(
            ticket, request, text=text, owner=owner, origin=origin,
            notify=notify, recipient=recipient)

    def formatted_text(self, layout: DefaultLayout) -> str:
        return self.text and hashtag_elements(
            layout.request, paragraphify(linkify(self.text))) or ''

    @property
    def subtype(self) -> str | None:
        return self.meta.get('origin', None)


class TicketMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'ticket'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: OrgRequest,
        change: str,
        origin: str = 'internal',
        **extra_meta: Any
    ) -> Self:
        return super().create(ticket, request, change=change,
                              origin=origin, **extra_meta)


class ReservationMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'reservation'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        reservations: Iterable[Reservation],
        ticket: Ticket,
        request: OrgRequest,
        change: str,
        origin: str = 'internal'
    ) -> Self:
        return super().create(
            ticket,
            request,
            change=change,
            origin=origin,
            reservations=[
                # NOTE: we record more than just the id, since if the
                #       change is, that we deleted the reservations,
                #       then we no longer will know when those reservations
                #       were.
                {
                    'id': reservation.id,
                    'start': reservation.display_start(),
                    'end': reservation.display_end(),
                }
                for reservation in reservations
            ]
        )


class ReservationAdjustedMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'reservation_adjusted'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        old_reservation: Reservation,
        new_reservation: Reservation,
        ticket: Ticket,
        request: OrgRequest,
    ) -> Self:
        return super().create(
            ticket,
            request,
            old_start=old_reservation.display_start(),
            old_end=old_reservation.display_end(),
            new_start=new_reservation.display_start(),
            new_end=new_reservation.display_end()
        )


class SubmissionMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'submission'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: OrgRequest,
        change: str
    ) -> Self:
        return super().create(ticket, request, change=change)


class EventMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'event'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        event: Event,
        ticket: Ticket,
        request: OrgRequest,
        change: str
    ) -> Self:
        return super().create(
            ticket, request, change=change, event_name=event.name)

    def event_link(self, request: OrgRequest) -> str:
        return request.class_link(Event, {'name': self.meta['event_name']})


class PaymentMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'payment'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        payment: Payment,
        ticket: Ticket,
        request: OrgRequest,
        change: str
    ) -> Self:
        assert payment.amount is not None
        return super().create(
            ticket, request,
            change=change,
            payment_id=payment.id.hex,
            amount=float(payment.amount),
            currency=payment.currency
        )


class DirectoryMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'directory'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        directory: Directory,
        ticket: Ticket,
        request: OrgRequest,
        action: str
    ) -> Self:
        return super().create(
            ticket, request,
            directory_id=directory.id.hex,
            action=action
        )


class TimeReportMessage(Message, TicketMessageMixin):

    __mapper_args__ = {'polymorphic_identity': 'time_report'}

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: OrgRequest,
        change: str,
        origin: str = 'internal',
    ) -> Self:
        return super().create(ticket, request, change=change, origin=origin)
