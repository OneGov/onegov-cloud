from __future__ import annotations

from functools import cached_property
from markupsafe import Markup
from onegov.chat import Message, MessageCollection
from onegov.chat.collections import ChatCollection
from onegov.core.elements import Link, LinkGroup, Confirm, Intercooler, Trait
from onegov.core.templates import render_macro
from onegov.directory import Directory, DirectoryEntry
from onegov.event import EventCollection
from onegov.form import FormSubmissionCollection
from onegov.org import _
from onegov.org.layout import DefaultLayout, EventLayout
from onegov.org.views.utils import show_tags, show_filters
from onegov.org.utils import (
    currency_for_submission,
    invoice_items_for_submission
)
from onegov.pay import ManualPayment
from onegov.reservation import Allocation, Resource, Reservation
from onegov.ticket import handlers, Handler, Ticket, TicketInvoice
from onegov.search.utils import extract_hashtags
from operator import attrgetter
from purl import URL
from sedate import utcnow
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import object_session, undefer
from uuid import uuid4


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.chat.models import Chat
    from onegov.core.request import CoreRequest
    from onegov.event import Event
    from onegov.form import Form, FormSubmission
    from onegov.org.request import OrgRequest
    from onegov.pay import InvoiceItem, InvoiceItemMeta, Payment
    from onegov.ticket.handler import _Q
    from sqlalchemy import Column
    from sqlalchemy.orm import Query, Session
    from typing import TypeAlias
    from uuid import UUID

    DateRange: TypeAlias = tuple[datetime, datetime]


def ticket_submitter(ticket: Ticket) -> str | None:
    handler = ticket.handler
    mail = handler.deleted and ticket.snapshot.get('email') or handler.email
    # case of EventSubmissionHandler for imported events
    if handler.data.get('source'):
        mail = handler.data.get('user', mail)
    return mail


def submission_invoice_items(
    self: FormSubmissionHandler | DirectoryEntryHandler,
    request: CoreRequest
) -> list[InvoiceItemMeta]:
    return invoice_items_for_submission(
        request,
        self.form,  # type: ignore[arg-type]
        self.submission
    ) if self.submission else []


def refresh_submission_invoice_items(
    self: FormSubmissionHandler | DirectoryEntryHandler,
    request: CoreRequest
) -> None:
    payment = self.payment
    invoice = self.ticket.invoice
    new_item_metas = self.invoice_items(request)
    if not new_item_metas:
        # delete the invoice and payment (if it exists)
        if invoice is not None:
            for item in invoice.items:
                item.payments = []
                request.session.delete(item)
            self.ticket.invoice = None
            request.session.delete(invoice)

        if payment is not None:
            if self.submission is not None:
                self.submission.payment = None
            request.session.delete(payment)

        return

    if invoice is None:
        # create a new invoice
        invoice = TicketInvoice(id=uuid4())
        request.session.add(invoice)
        self.ticket.invoice = invoice

    old_items = sorted(invoice.items, key=attrgetter('group'))
    new_items: list[InvoiceItem] = []
    unused: set[InvoiceItem] = set(old_items)
    for meta in new_item_metas:
        existing: InvoiceItem | None = None
        for item in old_items:
            if item.group != meta.group:
                continue

            if meta.group == 'form':
                assert meta.extra is not None
                assert meta.extra['submission_id'] == item.submission_id
                if meta.family == item.family:
                    existing = item
                    break
            elif meta.group == 'submission':
                if item.group == 'submission':
                    existing = item
                    break
            else:
                raise AssertionError('unreachable')

        if existing is None:
            new_item = meta.add_to_invoice(invoice)
            if payment is not None:
                new_item.payments.append(payment)
                # FIXME: If we allow paid payments we need to do
                #        more here
            new_items.append(new_item)
            continue

        # update the existing item if necessary
        meta.refresh_item(existing)

        unused.discard(existing)
        new_items.append(existing)

    for existing in unused:
        # keep manually added items
        if existing.group == 'manual':
            new_items.append(existing)
            continue

        # clear out any links to payments before deleting
        existing.payments = []
        request.session.delete(existing)

    invoice.items = new_items  # type: ignore[assignment]
    request.session.flush()

    # FIXME: If we allow paid or online payments, then we need to do
    #        something different here
    total = invoice.total_amount
    if payment is None:
        if total > 0:
            # we need to create a new manual payment
            # and link it to the submission and invoice items
            assert self.submission
            payment = ManualPayment(
                amount=invoice.total_amount,
                currency=currency_for_submission(
                    self.form,  # type: ignore[arg-type]
                    self.submission
                )
            )
            self.submission.payment = payment
            for item in invoice.items:
                item.payments.append(payment)
            invoice.sync(capture=False)
            self.ticket.payment = payment
    elif total <= 0:
        # we need to delete the payment
        # TODO: We may allow deleting non-manual payments in the future
        #       but for now we assert we didn't delete a non-open
        #       non-manual payment
        assert payment.source == 'manual' and payment.state == 'open'
        if self.submission:
            self.submission.payment = None
        for item in invoice.items:
            item.payments.remove(payment)
        self.ticket.payment = None
        self.ticket.payment_id = None
        request.session.delete(payment)
    elif total != payment.amount:
        # we need to update the payment
        # TODO: We may allow changing non-manual payments in the future
        #       but for now we assert we didn't change a non-open
        #       non-manual payment
        assert payment.source == 'manual' and payment.state == 'open'
        payment.amount = total
    request.session.flush()


class OrgTicketMixin:
    """ Adds additional methods to the ticket, needed by the organisations
    implementation of it. Strictly limited to things that
    do not belong into onegov.ticket.

    """

    if TYPE_CHECKING:
        number: Column[str]
        group: Column[str]

    def reference(self, request: OrgRequest) -> str:
        """ Returns the reference which should be used wherever we talk about
        a ticket, but do not show it (say in an e-mail subject).

        This reference should not be changed so it stays consistent.

        If you want, you can override the content of the reference group,
        shown in brackets (see :meth:`reference_group`).

        """
        return f'{self.number} / {self.reference_group(request)}'

    def reference_group(self, request: OrgRequest) -> str:
        return request.translate(self.group)

    @cached_property
    def extra_localized_text(self) -> str:

        # extracts of attachments are currently not searchable - if they were
        # we would add this here - probably in a raw SQL query that
        # concatenates all the text
        #
        # for now I've decided against it as it would lower the hit-rate
        # for notes (which should be very easy to find), just to be able
        # to search through files which are mostly going to be irrelevant
        # for what the user wants to find
        #
        # if the user wants to have a ticket findable through the file content
        # we should advise them to enter a meaningful note with the file
        # instead.
        #
        q = object_session(self).query(Message)
        q = q.filter_by(channel_id=self.number)
        q = q.filter(Message.type.in_(('ticket_note', 'ticket_chat')))
        q = q.with_entities(Message.text)

        return ' '.join(n.text for n in q if n.text)

    @property
    def es_tags(self) -> list[str] | None:
        if self.extra_localized_text:
            return [
                tag.lstrip('#') for tag in extract_hashtags(
                    self.extra_localized_text
                )
            ]
        return None


class FormSubmissionTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FRM'}  # type:ignore
    es_type_name = 'submission_tickets'

    if TYPE_CHECKING:
        handler: FormSubmissionHandler


class ReservationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'RSV'}  # type:ignore
    es_type_name = 'reservation_tickets'

    if TYPE_CHECKING:
        handler: ReservationHandler


class EventSubmissionTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EVN'}  # type:ignore
    es_type_name = 'event_tickets'

    if TYPE_CHECKING:
        handler: EventSubmissionHandler

    def reference_group(self, request: OrgRequest) -> str:
        return self.title

    def unguessable_edit_link(self, request: OrgRequest) -> str | None:
        if (
            self.handler
            and self.handler.ticket
            and self.handler.ticket.state in ('open', 'pending')
            and self.handler.event
            and self.handler.event.state == 'submitted'
            and self.handler.event.meta
            and 'token' in self.handler.event.meta
        ):
            return request.link(
                self.handler.event,
                name='edit',
                query_params={'token': self.handler.event.meta['token']}
            )
        return None


class DirectoryEntryTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'DIR'}  # type:ignore
    es_type_name = 'directory_tickets'

    if TYPE_CHECKING:
        handler: DirectoryEntryHandler


@handlers.registered_handler('FRM')
class FormSubmissionHandler(Handler):

    id: UUID

    handler_title = _('Form Submissions')
    code_title = _('Forms')
    invoice_items = submission_invoice_items
    refresh_invoice_items = refresh_submission_invoice_items

    @cached_property
    def collection(self) -> FormSubmissionCollection:
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self) -> FormSubmission | None:
        return self.collection.by_id(self.id)

    @cached_property
    def form(self) -> Form:
        assert self.submission is not None
        return self.submission.form_class(data=self.submission.data)

    @property
    def deleted(self) -> bool:
        return self.submission is None

    # FIXME: We should be a little bit more careful about data from
    #        properties that can be None
    @property
    def email(self) -> str:
        return (
            self.submission.email or ''
            if self.submission is not None else ''
        )

    @property
    def title(self) -> str:
        return (
            self.submission.title or ''
            if self.submission is not None else ''
        )

    @property
    def subtitle(self) -> None:
        return None

    @property
    def group(self) -> str:
        return (
            self.submission.form.title  # type:ignore[union-attr]
            if self.submission is not None else ''
        )

    @property
    def payment(self) -> Payment | None:
        return self.submission.payment if self.submission is not None else None

    # FIXME: This should probably be cached on the ticket/submission
    #        so it can't change throughout the ticket's lifespan
    #        however this VAT stuff will probably still change quite
    #        a bit, so for now this simple solution should be fine.
    @property
    def show_vat(self) -> bool:
        return (
            getattr(self.submission.form, 'show_vat', False)
            if self.submission is not None else False
        )

    @property
    def extra_data(self) -> list[str]:
        return [
            v for v in self.submission.data.values()
            if isinstance(v, str)
        ] if self.submission is not None else []

    @property
    def undecided(self) -> bool:
        if self.deleted:
            return False

        assert self.submission is not None

        # submissions without registration window do not present a decision
        if not self.submission.registration_window:
            return False

        if self.submission.claimed is None:
            return True

        return False

    def get_summary(
        self,
        request: OrgRequest  # type:ignore[override]
    ) -> Markup:

        layout = DefaultLayout(self.submission, request)
        if self.submission is not None:
            return render_macro(layout.macros['display_form'], request, {
                'form': self.form,
                'layout': layout,
                'price': self.submission.payment,
                'show_vat': self.show_vat,
            })
        return Markup('')

    def get_links(  # type:ignore[override]
        self,
        request: OrgRequest  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        links: list[Link | LinkGroup] = []
        extra: list[Link] = []

        # there's a decision to be made about the registration
        window = (self.submission.registration_window
                  if self.submission is not None else None)

        if window:
            assert self.submission is not None
            if self.submission.spots and self.submission.claimed is None:
                confirmation_traits: list[Trait] = [
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.url
                    )
                ]

                next_in_queue = window.next_submission

                if next_in_queue and next_in_queue is not self.submission:
                    confirmation_traits.append(Confirm(
                        _(
                            'This is not the oldest undecided submission of '
                            'this registration window. Do you really want to '
                            'confirm this submission?'
                        ),
                        _(
                            'By confirming this submission, you will prefer '
                            'this over a submission that came in earlier.'
                        ),
                        _(
                            'Confirm registration'
                        ),
                        _(
                            'Cancel'
                        )
                    ))

                links.append(
                    Link(
                        text=_('Confirm registration'),
                        url=request.csrf_protected_url(
                            request.link(self.ticket, 'confirm-registration')
                        ),
                        attrs={'class': 'accept-link'},
                        traits=confirmation_traits
                    )
                )
                extra.append(
                    Link(
                        text=_('Deny registration'),
                        url=request.csrf_protected_url(
                            request.link(self.ticket, 'deny-registration')
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Intercooler(
                                request_method='POST',
                                redirect_after=request.url
                            ),
                        )
                    )
                )

            # a registration was accepted before, we can issue an uninvite
            if self.submission.spots and self.submission.claimed:
                links.append(
                    Link(
                        text=_('Cancel registration'),
                        url=request.csrf_protected_url(
                            request.link(self.ticket, 'cancel-registration')
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Intercooler(
                                request_method='POST',
                                redirect_after=request.url
                            ),
                        )
                    )
                )
            extra.append(
                Link(
                    text=_('Registration Window'),
                    url=request.link(self.ticket, 'window'),
                    attrs={'class': 'edit-link'}
                )
            )

        if self.submission is not None:
            url_obj = URL(request.link(self.ticket, 'submission'))
            edit_url = url_obj.query_param('edit', '').as_string()

            (links if not links else extra).append(
                Link(
                    text=_('Edit submission'),
                    url=edit_url,
                    attrs={'class': 'edit-link'}
                )
            )

        if extra:
            links.append(LinkGroup(
                _('Advanced'),
                links=extra,
                right_side=False
            ))

        return links


@handlers.registered_handler('RSV')
class ReservationHandler(Handler):

    id: UUID

    handler_title = _('Reservations')
    code_title = _('Reservations')

    @cached_property
    def resource(self) -> Resource | None:
        if self.deleted:
            return None
        query = self.session.query(Resource)
        query = query.filter(Resource.id == self.reservations[0].resource)

        return query.one()

    def reservations_query(self) -> Query[Reservation]:
        # libres allows for multiple reservations with a single request (token)
        # for now we don't really have that case in onegov.org, but we
        # try to be aware of it as much as possible
        query = self.session.query(Reservation)
        query = query.filter(Reservation.token == self.id)
        query = query.order_by(Reservation.start)
        return query

    @cached_property
    def reservations(self) -> tuple[Reservation, ...]:
        return tuple(
            self.reservations_query()
            .options(undefer(Reservation.data))
        )

    @cached_property
    def has_future_reservation(self) -> bool:
        exists = self.reservations_query().filter(
            Reservation.start > func.now()
        ).exists()

        return self.session.query(exists).scalar()

    @cached_property
    def most_future_reservation(self) -> Reservation | None:
        return (
            self.session.query(Reservation)
            .order_by(desc(Reservation.start))
            .first()
        )

    @cached_property
    def submission(self) -> FormSubmission | None:
        return FormSubmissionCollection(self.session).by_id(self.id)

    @property
    def payment(self) -> Payment | None:
        return self.reservations and self.reservations[0].payment or None

    @property
    def deleted(self) -> bool:
        return not self.reservations

    def invoice_items(self, request: CoreRequest) -> list[InvoiceItemMeta]:
        if self.submission:
            form = request.get_form(
                self.submission.form_class,
                data=self.submission.data
            )
            item_extra = {'submission_id': self.submission.id}
            extras = form.invoice_items(extra=item_extra)
            discounts = form.discount_items(extra=item_extra)
        else:
            extras = []
            discounts = []

        return self.resource.invoice_items_for_reservation(
            self.reservations,
            extras,
            discounts,
            reduced_amount_label=request.translate(_('Discount'))
        ) if self.resource else []

    def refresh_invoice_items(self, request: CoreRequest) -> None:
        payment = self.payment
        invoice = self.ticket.invoice
        new_item_metas = self.invoice_items(request)
        if not new_item_metas:
            # delete the invoice and payment (if it exists)
            if invoice is not None:
                for item in invoice.items:
                    item.payments = []
                    request.session.delete(item)
                self.ticket.invoice = None
                request.session.delete(invoice)

            if payment is not None:
                for reservation in self.reservations:
                    reservation.payment = None
                request.session.delete(payment)

            return

        if invoice is None:
            # create a new invoice
            invoice = TicketInvoice(id=uuid4())
            request.session.add(invoice)
            self.ticket.invoice = invoice

        old_items = sorted(invoice.items, key=attrgetter('group'))
        new_items: list[InvoiceItem] = []
        unused: set[InvoiceItem] = set(old_items)
        for meta in new_item_metas:
            existing: InvoiceItem | None = None
            for item in old_items:
                if item.group != meta.group:
                    continue

                if meta.group == 'reservation':
                    assert meta.extra is not None
                    if meta.extra['reservation_id'] == item.reservation_id:
                        existing = item
                        break
                elif meta.group == 'form':
                    assert meta.extra is not None
                    assert item.submission_id is not None
                    assert meta.extra['submission_id'] == item.submission_id
                    if meta.family == item.family:
                        existing = item
                        break
                elif meta.group == 'reduced_amount':
                    existing = item
                    break
                else:
                    raise AssertionError('unreachable')

            if existing is None:
                new_item = meta.add_to_invoice(invoice)
                if payment is not None:
                    new_item.payments.append(payment)
                    # FIXME: If we allow paid payments we need to do
                    #        more here
                new_items.append(new_item)
                continue

            # update the existing item if necessary
            meta.refresh_item(existing)

            unused.discard(existing)
            new_items.append(existing)

        for existing in unused:
            # keep manually added items
            if existing.group == 'manual':
                new_items.append(existing)
                continue

            # clear out any links to payments before deleting
            existing.payments = []
            request.session.delete(existing)

        invoice.items = new_items  # type: ignore[assignment]
        request.session.flush()

        # FIXME: If we allow paid or online payments, then we need to do
        #        something different here
        total = invoice.total_amount
        if payment is None:
            if total > 0:
                # we need to create a new manual payment
                # and link it to the reservations and invoice items
                assert self.resource is not None
                payment = ManualPayment(
                    amount=invoice.total_amount,
                    currency=self.resource.currency or 'CHF'
                )
                for reservation in self.reservations:
                    reservation.payment = payment
                for item in invoice.items:
                    item.payments.append(payment)
                invoice.sync(capture=False)
                self.ticket.payment = payment
        elif total <= 0:
            # we need to delete the payment
            # TODO: We may allow deleting non-manual payments in the future
            #       but for now we assert we didn't delete a non-open
            #       non-manual payment
            assert payment.source == 'manual' and payment.state == 'open'
            for reservation in self.reservations:
                reservation.payment = None
            for item in invoice.items:
                item.payments.remove(payment)
            self.ticket.payment = None
            self.ticket.payment_id = None
            request.session.delete(payment)
        elif total != payment.amount:
            # we need to update the payment
            # TODO: We may allow changing non-manual payments in the future
            #       but for now we assert we didn't change a non-open
            #       non-manual payment
            assert payment.source == 'manual' and payment.state == 'open'
            payment.amount = total
        request.session.flush()

    @property
    def extra_data(self) -> list[str]:
        return self.submission and [
            v for v in self.submission.data.values()
            if isinstance(v, str)
        ] or []

    @property
    def email(self) -> str:
        # the e-mail is the same over all reservations
        if self.deleted:
            return self.ticket.snapshot.get('email')  # type:ignore
        return self.reservations[0].email

    @property
    def undecided(self) -> bool:
        # if there is no reservation with an 'accept' marker, the user
        # has not yet made a decision
        if self.deleted:
            return False

        for r in self.reservations:
            if r.data and r.data.get('accepted'):
                return False

        return True

    def prepare_delete_ticket(self) -> None:
        for reservation in self.reservations or ():
            self.session.delete(reservation)

    @cached_property
    def ticket_deletable(self) -> bool:
        return not self.has_future_reservation and super().ticket_deletable

    @property
    def title(self) -> str:
        parts = []

        for ix, reservation in enumerate(self.reservations):
            parts.append(self.get_reservation_title(reservation))

            if ix == 4:
                parts.append('…')
                break

        return ', '.join(parts)

    def get_reservation_title(self, reservation: Reservation) -> str:
        assert self.resource and hasattr(self.resource, 'reservation_title')
        return self.resource.reservation_title(reservation)

    @property
    def subtitle(self) -> str | None:
        if self.submission:
            return ', '.join(
                p for p in (self.email, self.submission.title) if p)
        elif self.reservations:
            return self.email
        else:
            return None

    @property
    def group(self) -> str | None:
        return self.resource.title if self.resource else None

    @classmethod
    def handle_extra_parameters(
        cls,
        session: Session,
        query: _Q,
        extra_parameters: dict[str, Any]
    ) -> _Q:

        if 'allocation_id' in extra_parameters:
            allocations = session.query(Allocation.group)
            allocations = allocations.filter(
                Allocation.id == int(extra_parameters['allocation_id']))

            tokens = session.query(Reservation.token)
            tokens = tokens.filter(
                Reservation.target.in_(allocations.subquery()))

            handler_ids = tuple(t[0].hex for t in tokens)

            if handler_ids:
                query = query.filter(Ticket.handler_id.in_(handler_ids))
            else:
                query = query.filter(False)

        return query

    def get_summary(
        self,
        request: OrgRequest  # type:ignore[override]
    ) -> Markup:

        layout = DefaultLayout(self.resource, request)

        is_manager = request.is_manager_for_model(self.ticket)
        parts = []
        parts.append(
            render_macro(layout.macros['reservations'], request, {
                'reservations': self.reservations,
                'get_links': self.get_reservation_links
                if is_manager and self.ticket.state == 'pending' else None,
                'get_occupancy_url': self.get_occupancy_url,
                'layout': layout
            })
        )

        # render key code
        if key_code := self.data.get('key_code'):
            parts.append(Markup(
                '<dl class="field-display">'
                '<dt>{}</dt><dd>{}</dd>'
                '</dl>'
            ).format(
                request.translate(_('Key Code')),
                key_code
            ))

        # render internal tag meta data
        if is_manager and self.ticket.tag_meta:
            parts.append(
                Markup('').join(
                    Markup(
                        '<dl class="field-display">'
                        '<dt>{}</dt><dd>{}</dd>'
                        '</dl>'
                    ).format(key, value)
                    for key, value in self.ticket.tag_meta.items()
                )
            )

        if self.submission:
            form = self.submission.form_class(data=self.submission.data)

            parts.append(
                render_macro(layout.macros['display_form'], request, {
                    'form': form,
                    'layout': layout
                })
            )

        return Markup('').join(parts)

    def get_changes(
        self,
        request: OrgRequest
    ) -> dict[DateRange, DateRange | None]:
        """ Returns a compressed set of changes of reservations.

        If a reservation is moved multiple times and then rejected, then
        this will only contain the rejection (orginal start/end -> None).

        If there is a chain of time adjustments, only the orginal and
        current start/end will be included.
        """

        messages = MessageCollection(
            request.session,
            type=('reservation', 'reservation_adjusted'),
            channel_id=self.ticket.number
        )
        changes: dict[DateRange, DateRange | None] = {}
        # maps current start/end to its original start/end
        origin: dict[DateRange, DateRange] = {}
        for message in messages.query():
            if message.type == 'reservation':
                if message.meta['change'] != 'rejected':
                    continue

                for reservation in message.meta['reservations']:
                    # for old messages we can't reconstruct the change
                    # so we just return an empty changelog
                    if not isinstance(reservation, dict):
                        return {}

                    key = reservation['start'], reservation['end']
                    key = origin.pop(key, key)
                    changes[key] = None
            else:
                assert message.type == 'reservation_adjusted'
                key = message.meta['old_start'], message.meta['old_end']
                current = message.meta['new_start'], message.meta['new_end']
                # if we have been moved previously map back to the origin
                key = origin.pop(key, key)
                origin[current] = key
                if key == current:
                    # if we changed a reservation back to its original
                    # state, then we remove it from the changes,
                    changes.pop(key, None)
                else:
                    changes[key] = current

        return changes

    def get_reservation_links(
        self,
        reservation: Reservation,
        request: OrgRequest
    ) -> list[Link]:

        links: list[Link] = []

        url_obj = URL(request.link(self.ticket, 'reject-reservation'))
        url_obj = url_obj.query_param(
            'reservation-id', str(reservation.id))
        url = url_obj.as_string()

        title = self.get_reservation_title(reservation)
        links.append(Link(
            text=_('Reject'),
            url=url,
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _('Do you really want to reject this reservation?'),
                    _("Rejecting ${title} can't be undone.", mapping={
                        'title': title
                    }),
                    _('Reject reservation'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='GET',
                    redirect_after=request.url
                )
            )
        ))

        if reservation.is_adjustable:
            url_obj = URL(request.link(self.ticket, 'adjust-reservation'))
            url_obj = url_obj.query_param(
                'reservation-id', str(reservation.id))
            url = url_obj.as_string()
            links.append(Link(
                text=_('Adjust'),
                url=url,
                attrs={'class': 'edit-link'}
            ))

        return links

    def get_occupancy_url(
        self,
        reservation: Reservation,
        request: OrgRequest
    ) -> str | None:

        if self.deleted:
            return None

        if not request.is_manager_for_model(self.ticket):
            return None

        assert self.resource is not None
        return request.class_link(
            Resource,
            {
                'name': self.resource.name,
                'date': reservation.display_start(),
                'view': 'timeGridDay'
            },
            name='occupancy'
        )

    def get_links(  # type:ignore[override]
        self,
        request: OrgRequest  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        if self.deleted:
            return []

        links: list[Link | LinkGroup] = []

        accepted = tuple(
            r.data and r.data.get('accepted') or False
            for r in self.reservations
        )

        if not all(accepted):
            links.append(
                Link(
                    text=_('Accept all reservations'),
                    url=request.link(self.ticket, 'accept-reservation'),
                    attrs={'class': 'accept-link'}
                )
            )

        advanced_links = []

        if self.reservations:
            advanced_links.append(Link(
                text=_('Send reservation summary'),
                url=request.link(self.ticket, 'send-reservation-summary'),
                attrs={'class': ('envelope', 'border')},
                traits=(
                    Confirm(
                        _('Do you really want to send a reservation summary?'),
                        _(
                            'This will always be sent via e-mail, even when '
                            'ticket updates have been disabled. Make sure to '
                            'only use this to inform customers, when '
                            'significant changes have been made to the '
                            'reservations, they need to be aware of.'
                        ),
                        _('Send'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='GET',
                        redirect_after=request.url
                    )
                )
            ))

        if self.submission:
            url_obj = URL(request.link(self.ticket, 'submission'))
            url_obj = url_obj.query_param('edit', '')
            url_obj = url_obj.query_param('title', request.translate(
                _('Details about the reservation')))
            url = url_obj.as_string()

            advanced_links.append(
                Link(
                    text=_('Edit details'),
                    url=url,
                    attrs={'class': ('edit-link', 'border')}
                )
            )

        now = utcnow()
        if getattr(self.resource, 'kaba_components', None) and any(
            True
            for reservation in self.reservations
            if reservation.display_start() > now
        ):
            advanced_links.append(
                Link(
                    text=_('Edit key code'),
                    url=request.link(self.ticket, 'edit-kaba'),
                    attrs={'class': ('edit-link', 'border')}
                )
            )

        if not all(accepted):
            advanced_links.append(
                Link(
                    text=_('Accept all with message'),
                    url=request.link(
                        self.ticket, 'accept-reservation-with-message'),
                    attrs={'class': 'accept-link'}
                )
            )

        advanced_links.append(Link(
            text=_('Reject all'),
            url=request.link(self.ticket, 'reject-reservation'),
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _('Do you really want to reject all reservations?'),
                    _("Rejecting these reservations can't be undone."),
                    _('Reject reservations'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='GET',
                    redirect_after=request.url
                )
            )
        ))

        advanced_links.append(Link(
            text=_('Reject all with message'),
            url=request.link(self.ticket, 'reject-reservation-with-message'),
            attrs={'class': 'delete-link'},
        ))

        links.append(LinkGroup(
            _('Advanced'),
            links=advanced_links,
            right_side=False
        ))

        return links


@handlers.registered_handler('EVN')
class EventSubmissionHandler(Handler):

    id: UUID
    handler_title = _('Events')
    code_title = _('Events')

    @cached_property
    def collection(self) -> EventCollection:
        return EventCollection(self.session)

    @cached_property
    def event(self) -> Event | None:
        return self.collection.by_id(self.id)

    @property
    def deleted(self) -> bool:
        return self.event is None

    @cached_property
    def source(self) -> str | None:
        # values stored only when importing with cli
        return self.data.get('source')

    @cached_property
    def import_user(self) -> str | None:
        # values stored only when importing with cli
        return self.data.get('user')

    @cached_property
    def email(self) -> str | None:
        return self.event.meta.get('submitter_email') if self.event else None

    @property
    def title(self) -> str:
        return self.event.title if self.event else ''

    @property
    def subtitle(self) -> str | None:
        if self.deleted:
            return None

        assert self.event is not None
        parts = (
            self.event.meta.get('submitter_email'),
            '{:%d.%m.%Y %H:%M}'.format(self.event.localized_start)
        )

        return ', '.join(p for p in parts if p)

    @property
    def extra_data(self) -> list[str]:
        assert self.event is not None
        return [
            self.event.description or '',
            self.event.title,
            self.event.location or ''
        ]

    @property
    def undecided(self) -> bool:
        return self.event and self.event.state == 'submitted' or False

    @property
    def ticket_deletable(self) -> bool:
        # We don't want to delete the event. So we will redact the ticket
        # instead.
        return False

    @cached_property
    def group(self) -> str:
        return _('Event')

    def get_summary(
        self,
        request: OrgRequest  # type:ignore[override]
    ) -> Markup:
        assert self.event is not None
        layout = EventLayout(self.event, request)
        return render_macro(layout.macros['display_event'], request, {
            'event': self.event,
            'layout': layout,
            'show_tags': show_tags(request),
            'show_filters': show_filters(request),
        })

    def get_links(  # type:ignore[override]
        self,
        request: OrgRequest  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        if not self.event:
            return []

        links: list[Link | LinkGroup] = []

        if self.event.state == 'submitted':
            links.append(Link(
                text=_('Accept event'),
                url=request.link(self.ticket, 'publish-event'),
                attrs={'class': 'accept-link'},
            ))

        advanced_links = [
            Link(
                text=_('Edit event'),
                url=request.link(self.ticket, 'edit-event'),
                attrs={'class': ('edit-link', 'border')}
            )]

        if not self.event.source:
            advanced_links.append(
                Link(
                    text=_('Reject event'),
                    url=request.csrf_protected_url(
                        request.link(self.ticket, 'delete-event')),
                    attrs={'class': ('delete-link')},
                    traits=(
                        Confirm(
                            _('Do you really want to reject this event?'),
                            _("Rejecting this event can't be undone."),
                            _('Reject event'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=request.link(self.ticket)
                        )
                    )
                )
            )

        elif self.event.state in ('published', 'submitted'):
            advanced_links.append(
                Link(
                    text=_('Withdraw event'),
                    url=request.csrf_protected_url(
                        request.link(self.ticket, name='withdraw-event')),
                    attrs={'class': ('delete-link')},
                    traits=(
                        Confirm(
                            _('Do you really want to withdraw this event?'),
                            _('You can re-publish an imported event later.'),
                            _('Withdraw event'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='POST',
                            redirect_after=request.link(self.ticket)
                        )
                    )
                )
            )

        elif self.event.state == 'withdrawn':
            advanced_links.append(
                Link(
                    text=_('Re-publish event'),
                    url=request.link(self.ticket, 'publish-event'),
                    attrs={'class': 'accept-link'}
                )
            )

        links.append(LinkGroup(_('Advanced'), links=advanced_links,
                               right_side=False))

        return links


@handlers.registered_handler('DIR')
class DirectoryEntryHandler(Handler):

    id: UUID

    handler_title = _('Directory Entry Submissions')
    code_title = _('Directory Entry Submissions')
    invoice_items = submission_invoice_items
    refresh_invoice_items = refresh_submission_invoice_items

    @cached_property
    def collection(self) -> FormSubmissionCollection:
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self) -> FormSubmission | None:
        return self.collection.by_id(self.id)

    @cached_property
    def form(self) -> Form | None:
        return (
            self.submission.form_class(data=self.submission.data)
            if self.submission is not None else None
        )

    # FIXME: This should probably query ExtendedDirectory, since we rely
    #        on a method that only exists on ExtendedDirectory
    @cached_property
    def directory(self) -> Directory | None:
        if self.submission:
            directory_id = self.submission.meta['directory']
        else:
            directory_id = self.ticket.handler_data['directory']

        return self.session.query(Directory).filter_by(id=directory_id).first()

    @cached_property
    def entry(self) -> DirectoryEntry | None:
        if self.submission:
            id = self.submission.meta.get('directory_entry')
        else:
            id = self.ticket.handler_data.get('directory_entry')

        return self.session.query(DirectoryEntry).filter_by(id=id).first()

    @property
    def deleted(self) -> bool:
        if not self.directory:
            return True

        if self.kind == 'change-request':
            if self.submission:
                data = self.submission.meta
            else:
                data = self.ticket.handler_data

            entry = (
                self.session.query(DirectoryEntry)
                .filter_by(id=data['directory_entry'])
                .first()
            )

            if not entry:
                return True

        if self.state == 'adopted':
            name = self.ticket.handler_data.get('entry_name')
            if name is None:
                return True
            return not self.directory.entry_with_name_exists(name)

        return False

    @property
    def email(self) -> str:
        return (
            # we don't allow directory entry submissions without an email
            self.submission.email  # type:ignore[return-value]
            if self.submission is not None else ''
        )

    @property
    def submitter_name(self) -> str | None:
        submitter_name: str | None = (
            self.ticket.snapshot.get('submitter_name')
            if self.deleted else None
        )
        if submitter_name is None and self.submission is not None:
            submitter_name = self.submission.submitter_name
        return submitter_name

    @property
    def submitter_phone(self) -> str | None:
        submitter_phone: str | None = (
            self.ticket.snapshot.get('submitter_phone')
            if self.deleted else None
        )
        if submitter_phone is None and self.submission is not None:
            submitter_phone = self.submission.submitter_phone
        return submitter_phone

    @property
    def submitter_address(self) -> str | None:
        submitter_address: str | None = (
            self.ticket.snapshot.get('submitter_address')
            if self.deleted else None
        )
        if submitter_address is None and self.submission is not None:
            submitter_address = self.submission.submitter_address
        return submitter_address

    @property
    def title(self) -> str:
        return (
            self.submission.title or ''
            if self.submission is not None else ''
        )

    @property
    def subtitle(self) -> None:
        return None

    @property
    def group(self) -> str:
        if self.directory:
            return self.directory.title
        elif self.ticket.group:
            return self.ticket.group
        return '-'

    @property
    def payment(self) -> Payment | None:
        return self.submission.payment if self.submission else None

    @property
    def state(self) -> str | None:
        return self.ticket.handler_data.get('state')

    @property
    def extra_data(self) -> list[str]:
        return self.submission and [
            v for v in self.submission.data.values()
            if isinstance(v, str)
        ] or []

    @property
    def undecided(self) -> bool:
        if not self.directory or self.deleted:
            return False

        return self.state is None

    @property
    def kind(self) -> str:
        if self.submission:
            data = self.submission.meta
        else:
            data = self.ticket.handler_data

        if 'change-request' in data.get('extensions', ()):
            return 'change-request'
        else:
            return 'new-entry'

    def get_summary(
        self,
        request: OrgRequest  # type:ignore[override]
    ) -> Markup:

        assert self.form is not None
        layout = DefaultLayout(self.submission, request)

        # XXX this is a poor man's request.get_form
        self.form.request = request
        self.form.model = self.submission

        macro = layout.macros['directory_entry_submission']

        return render_macro(macro, request, {
            'form': self.form,
            'layout': layout,
            'handler': self,
        })

    def get_links(  # type:ignore[override]
        self,
        request: OrgRequest  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        links: list[Link | LinkGroup] = []

        if not self.directory or self.deleted:
            return links

        if self.state is None:
            assert self.submission is not None
            assert hasattr(self.directory, 'submission_action')
            links.append(
                Link(
                    text=_('Adopt'),
                    url=request.link(
                        self.directory.submission_action(
                            'adopt', self.submission.id
                        )
                    ),
                    attrs={'class': 'accept-link'},
                    traits=(
                        Intercooler(
                            request_method='POST',
                            redirect_after=request.url
                        ),
                    )
                )
            )

        if self.state == 'adopted':
            # FIXME: A supporter may not have permission to view the entry
            links.append(
                Link(
                    text=_('View directory entry'),
                    url=request.class_link(DirectoryEntry, {
                        'directory_name': self.directory.name,
                        'name': self.ticket.handler_data['entry_name']
                    }),
                    attrs={'class': 'view-link'},
                )
            )

        advanced_links = []

        if self.state == 'rejected':
            assert self.submission is not None
            assert hasattr(self.directory, 'submission_action')
            type = 'change' if (
                   'change-request' in self.submission.extensions) else 'entry'
            text = _('Withdraw rejection')
            if type == 'entry':
                tooltip = _('This directory entry has been rejected. Do you '
                            'want to withdraw the rejection?')
            else:
                tooltip = _('This directory change has been rejected. Do you '
                            'want to withdraw the rejection?')
            advanced_links.append(
                Link(
                    text=text,
                    url=request.link(
                        self.directory.submission_action(
                            'withdraw_rejection', self.submission.id,
                        )
                    ),
                    attrs={'class': 'undo-link', 'title': tooltip},
                    traits=(
                        Intercooler(
                            request_method='POST',
                            redirect_after=request.url
                        ),
                    ),
                )
            )

        if self.state is None:
            url_obj = URL(request.link(self.ticket, 'submission'))
            url_obj = url_obj.query_param('edit', '')
            url_obj = url_obj.query_param('title', request.translate(
                _('Edit details')))
            url = url_obj.as_string()

            advanced_links.append(
                Link(
                    text=_('Edit details'),
                    url=url,
                    attrs={'class': ('edit-link', 'border')}
                )
            )

            assert self.submission is not None
            assert hasattr(self.directory, 'submission_action')
            if 'change-request' in self.submission.extensions:
                text = _('Reject change request')
                url = request.link(
                    self.directory.submission_action(
                        'reject', self.submission.id
                    )
                )
                traits = Confirm(
                    _('Do you really want to reject this change?'), None,
                    _('Reject change'),
                    _('Cancel')
                )
            else:
                text = _('Reject entry')
                url = request.link(
                    self.directory.submission_action(
                        'reject', self.submission.id
                    )
                )
                traits = Confirm(
                    _('Do you really want to reject this entry?'),
                    None,
                    _('Reject entry'),
                    _('Cancel')
                )
            advanced_links.append(Link(
                text=text,
                url=url,
                attrs={'class': 'delete-link'},
                traits=(
                    traits,
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.url
                    )
                )
            ))

        links.append(LinkGroup(
            _('Advanced'),
            links=advanced_links,
            right_side=False
        ))

        return links


class ChatTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'CHT'}  # type:ignore
    es_type_name = 'chat_tickets'

    def reference_group(self, request: OrgRequest) -> str:
        return self.handler.title


@handlers.registered_handler('CHT')
class ChatHandler(Handler):

    handler_title = _('Chats')
    code_title = _('Chats')

    @cached_property
    def collection(self) -> ChatCollection:
        return ChatCollection(self.session)

    @cached_property
    def chat(self) -> Chat | None:
        return self.collection.by_id(self.id)

    @property
    def deleted(self) -> bool:
        return self.chat is None

    @property
    def title(self) -> str:
        if self.chat is not None:
            return f'Chat - {self.chat.customer_name}'
        else:
            return ''

    @property
    def subtitle(self) -> None:
        return None

    @property
    def group(self) -> str | None:
        return self.chat.topic if self.chat is not None else None

    @property
    def email(self) -> str:
        return self.chat.email if self.chat is not None else ''

    def get_summary(
        self,
        request: OrgRequest  # type: ignore[override]
    ) -> Markup:

        layout = DefaultLayout(self.collection, request)
        if self.chat is not None:
            return render_macro(layout.macros['display_chat'], request, {
                'chat': self.chat,
                'layout': layout
            })
        return Markup('')

    def get_links(  # type: ignore[override]
        self,
        request: OrgRequest  # type: ignore[override]
    ) -> list[Link | LinkGroup]:
        return []
