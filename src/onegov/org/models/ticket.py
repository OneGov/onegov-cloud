from functools import cached_property
from markupsafe import Markup
from onegov.chat.collections import ChatCollection
from onegov.core.templates import render_macro
from onegov.directory import Directory, DirectoryEntry
from onegov.event import EventCollection
from onegov.form import FormSubmissionCollection
from onegov.org import _
from onegov.org.layout import DefaultLayout, EventLayout
from onegov.chat import Message
from onegov.core.elements import Link, LinkGroup, Confirm, Intercooler, Trait
from onegov.org.views.utils import show_tags, show_filters
from onegov.reservation import Allocation, Resource, Reservation
from onegov.ticket import Ticket, Handler, handlers
from onegov.search.utils import extract_hashtags
from purl import URL
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy.orm import object_session


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.chat.models import Chat
    from onegov.event import Event
    from onegov.form import Form, FormSubmission
    from onegov.org.request import OrgRequest
    from onegov.pay import Payment
    from onegov.ticket.handler import _Q
    from sqlalchemy import Column
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


def ticket_submitter(ticket: Ticket) -> str | None:
    handler = ticket.handler
    mail = handler.deleted and ticket.snapshot.get('email') or handler.email
    # case of EventSubmissionHandler for imported events
    if handler.data.get('source'):
        mail = handler.data.get('user', mail)
    return mail


class OrgTicketMixin:
    """ Adds additional methods to the ticket, needed by the organisations
    implementation of it. Strictly limited to things that
    do not belong into onegov.ticket.

    """

    if TYPE_CHECKING:
        number: Column[str]
        group: Column[str]

    def reference(self, request: 'OrgRequest') -> str:
        """ Returns the reference which should be used wherever we talk about
        a ticket, but do not show it (say in an e-mail subject).

        This reference should not be changed so it stays consistent.

        If you want, you can override the content of the reference group,
        shown in brackets (see :meth:`reference_group`).

        """
        return f'{self.number} / {self.reference_group(request)}'

    def reference_group(self, request: 'OrgRequest') -> str:
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


class ReservationTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'RSV'}  # type:ignore
    es_type_name = 'reservation_tickets'


class EventSubmissionTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EVN'}  # type:ignore
    es_type_name = 'event_tickets'

    if TYPE_CHECKING:
        handler: 'EventSubmissionHandler'

    def reference_group(self, request: 'OrgRequest') -> str:
        return self.title

    def unguessable_edit_link(self, request: 'OrgRequest') -> str | None:
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


@handlers.registered_handler('FRM')
class FormSubmissionHandler(Handler):

    id: 'UUID'

    handler_title = _("Form Submissions")
    code_title = _("Forms")

    @cached_property
    def collection(self) -> FormSubmissionCollection:
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self) -> 'FormSubmission | None':
        return self.collection.by_id(self.id)

    @cached_property
    def form(self) -> 'Form':
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
    def payment(self) -> 'Payment | None':
        return self.submission.payment if self.submission is not None else None

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
        request: 'OrgRequest'  # type:ignore[override]
    ) -> Markup:

        layout = DefaultLayout(self.submission, request)
        if self.submission is not None:
            return render_macro(layout.macros['display_form'], request, {
                'form': self.form,
                'layout': layout
            })
        return Markup('')

    def get_links(  # type:ignore[override]
        self,
        request: 'OrgRequest'  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        layout = DefaultLayout(self.submission, request)

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
                            "This is not the oldest undecided submission of "
                            "this registration window. Do you really want to "
                            "confirm this submission?"
                        ),
                        _(
                            "By confirming this submission, you will prefer "
                            "this over a submission that came in earlier."
                        ),
                        _(
                            "Confirm registration"
                        ),
                        _(
                            "Cancel"
                        )
                    ))

                links.append(
                    Link(
                        text=_("Confirm registration"),
                        url=request.return_here(
                            layout.csrf_protected_url(
                                request.link(
                                    self.submission, 'confirm-registration')
                            )
                        ),
                        attrs={'class': 'accept-link'},
                        traits=confirmation_traits
                    )
                )
                extra.append(
                    Link(
                        text=_("Deny registration"),
                        url=request.return_here(
                            layout.csrf_protected_url(
                                request.link(
                                    self.submission, 'deny-registration')
                            )
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
                        text=_("Cancel registration"),
                        url=request.return_here(
                            layout.csrf_protected_url(
                                request.link(
                                    self.submission, 'cancel-registration')
                            )
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
                    text=_("Registration Window"),
                    url=request.link(window),
                    attrs={'class': 'edit-link'}
                )
            )

        if self.submission is not None:
            url_obj = URL(request.link(self.submission))
            edit_url = url_obj.query_param('edit', '').as_string()

            (links if not links else extra).append(  # type:ignore
                Link(
                    text=_('Edit submission'),
                    url=request.return_here(edit_url),
                    attrs={'class': 'edit-link'}
                )
            )

        if extra:
            links.append(LinkGroup(
                _("Advanced"),
                links=extra,
                right_side=False
            ))

        return links


@handlers.registered_handler('RSV')
class ReservationHandler(Handler):

    id: 'UUID'

    handler_title = _("Reservations")
    code_title = _("Reservations")

    @cached_property
    def resource(self) -> Resource | None:
        if self.deleted:
            return None
        query = self.session.query(Resource)
        query = query.filter(Resource.id == self.reservations[0].resource)

        return query.one()

    def reservations_query(self) -> 'Query[Reservation]':
        # libres allows for multiple reservations with a single request (token)
        # for now we don't really have that case in onegov.org, but we
        # try to be aware of it as much as possible
        query = self.session.query(Reservation)
        query = query.filter(Reservation.token == self.id)
        query = query.order_by(Reservation.start)
        return query

    @cached_property
    def reservations(self) -> tuple[Reservation, ...]:
        return tuple(self.reservations_query())

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
    def submission(self) -> 'FormSubmission | None':
        return FormSubmissionCollection(self.session).by_id(self.id)

    @property
    def payment(self) -> 'Payment | None':
        return self.reservations and self.reservations[0].payment or None

    @property
    def deleted(self) -> bool:
        return False if self.reservations else True

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
        session: 'Session',
        query: '_Q',
        extra_parameters: dict[str, Any]
    ) -> '_Q':

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
        request: 'OrgRequest'  # type:ignore[override]
    ) -> Markup:

        layout = DefaultLayout(self.resource, request)

        parts = []
        parts.append(
            render_macro(layout.macros['reservations'], request, {
                'reservations': self.reservations,
                'layout': layout
            })
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

    def get_links(  # type:ignore[override]
        self,
        request: 'OrgRequest'  # type:ignore[override]
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
                    text=_("Accept all reservations"),
                    url=request.return_here(
                        request.link(self.reservations[0], 'accept')
                    ),
                    attrs={'class': 'accept-link'}
                )
            )

        advanced_links = []

        if self.submission:
            url_obj = URL(request.link(self.submission))
            url_obj = url_obj.query_param('edit', '')
            url_obj = url_obj.query_param('title', request.translate(
                _("Details about the reservation")))
            url = request.return_here(url_obj.as_string())

            advanced_links.append(
                Link(
                    text=_('Edit details'),
                    url=url,
                    attrs={'class': ('edit-link', 'border')}
                )
            )

        if not all(accepted):
            advanced_links.append(
                Link(
                    text=_("Accept all with message"),
                    url=request.return_here(
                        request.link(self.reservations[0],
                                     'accept-with-message')
                    ),
                    attrs={'class': 'accept-link'}
                )
            )

        advanced_links.append(Link(
            text=_("Reject all"),
            url=request.return_here(
                request.link(self.reservations[0], 'reject')
            ),
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _("Do you really want to reject all reservations?"),
                    _("Rejecting these reservations can't be undone."),
                    _("Reject reservations"),
                    _("Cancel")
                ),
                Intercooler(
                    request_method='GET',
                    redirect_after=request.url
                )
            )
        ))

        advanced_links.append(Link(
            text=_("Reject all with message"),
            url=request.return_here(
                request.link(self.reservations[0], 'reject-with-message')
            ),
            attrs={'class': 'delete-link'},
        ))

        for reservation in self.reservations:
            url_obj = URL(request.link(reservation, 'reject'))
            url_obj = url_obj.query_param(
                'reservation-id', str(reservation.id))
            url = request.return_here(url_obj.as_string())

            title = self.get_reservation_title(reservation)
            advanced_links.append(Link(
                text=_("Reject ${title}", mapping={'title': title}),
                url=url,
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _("Do you really want to reject this reservation?"),
                        _("Rejecting ${title} can't be undone.", mapping={
                            'title': title
                        }),
                        _("Reject reservation"),
                        _("Cancel")
                    ),
                    Intercooler(
                        request_method='GET',
                        redirect_after=request.url
                    )
                )
            ))

        links.append(LinkGroup(
            _("Advanced"),
            links=advanced_links,
            right_side=False
        ))

        return links


@handlers.registered_handler('EVN')
class EventSubmissionHandler(Handler):

    id: 'UUID'
    handler_title = _("Events")
    code_title = _("Events")

    @cached_property
    def collection(self) -> EventCollection:
        return EventCollection(self.session)

    @cached_property
    def event(self) -> 'Event | None':
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
        return _("Event")

    def get_summary(
        self,
        request: 'OrgRequest'  # type:ignore[override]
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
        request: 'OrgRequest'  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        links: list[Link | LinkGroup] = []
        # FIXME: We only use EventLayout to generate a csrf_protected_url
        #        This should probably be moved to an utils function
        layout = EventLayout(self.event, request)  # type:ignore[arg-type]

        if self.event and self.event.state == 'submitted':
            links.append(Link(
                text=_("Accept event"),
                url=request.return_here(request.link(self.event, 'publish')),
                attrs={'class': 'accept-link'},
            ))
        if not self.event:
            return links

        advanced_links = [
            Link(
                text=_('Edit event'),
                url=request.return_here(request.link(self.event, 'edit')),
                attrs={'class': ('edit-link', 'border')}
            )]

        if not self.event.source:
            advanced_links.append(
                Link(
                    text=_("Reject event"),
                    url=layout.csrf_protected_url(
                        request.link(self.event)),
                    attrs={'class': ('delete-link')},
                    traits=(
                        Confirm(
                            _("Do you really want to reject this event?"),
                            _("Rejecting this event can't be undone."),
                            _("Reject event"),
                            _("Cancel")
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
                    text=_("Withdraw event"),
                    url=layout.csrf_protected_url(request.link(
                        self.event, name='withdraw')),
                    attrs={'class': ('delete-link')},
                    traits=(
                        Confirm(
                            _("Do you really want to withdraw this event?"),
                            _("You can re-publish an imported event later."),
                            _("Withdraw event"),
                            _("Cancel")
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
                    text=_("Re-publish event"),
                    url=request.return_here(
                        request.link(self.event, 'publish')),
                    attrs={'class': 'accept-link'}
                )
            )

        links.append(LinkGroup(_("Advanced"), links=advanced_links,
                               right_side=False))

        return links


@handlers.registered_handler('DIR')
class DirectoryEntryHandler(Handler):

    id: 'UUID'

    handler_title = _("Directory Entry Submissions")
    code_title = _("Directory Entry Submissions")

    @cached_property
    def collection(self) -> FormSubmissionCollection:
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self) -> 'FormSubmission | None':
        return self.collection.by_id(self.id)

    @cached_property
    def form(self) -> 'Form | None':
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
    def payment(self) -> 'Payment | None':
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
        request: 'OrgRequest'  # type:ignore[override]
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
        request: 'OrgRequest'  # type:ignore[override]
    ) -> list[Link | LinkGroup]:

        links: list[Link | LinkGroup] = []

        if not self.directory or self.deleted:
            return links

        if self.state is None:
            assert self.submission is not None
            assert hasattr(self.directory, 'submission_action')
            links.append(
                Link(
                    text=_("Adopt"),
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
            links.append(
                Link(
                    text=_("View directory entry"),
                    url=request.class_link(DirectoryEntry, {
                        'directory_name': self.directory.name,
                        'name': self.ticket.handler_data['entry_name']
                    }),
                    attrs={'class': 'view-link'},
                )
            )

        if self.state == 'rejected':
            # may put link into group (advanced) to kind a hide a bit
            assert self.submission is not None
            assert hasattr(self.directory, 'submission_action')
            links.append(
                Link(
                    text=_("Withdraw rejection"),
                    url=request.link(
                        self.directory.submission_action(
                            'withdraw_rejection', self.submission.id
                        )
                    ),
                    attrs={'class': 'undo-link'},
                    traits=(
                        Intercooler(
                            request_method='POST',
                            redirect_after=request.url
                        ),
                    )
                )
            )

        advanced_links = []

        if self.state is None:
            url_obj = URL(request.link(self.submission))
            url_obj = url_obj.query_param('edit', '')
            url_obj = url_obj.query_param('title', request.translate(
                _("Edit details")))
            url = request.return_here(url_obj.as_string())

            advanced_links.append(
                Link(
                    text=_('Edit details'),
                    url=url,
                    attrs={'class': ('edit-link', 'border')}
                )
            )

            assert self.submission is not None
            assert hasattr(self.directory, 'submission_action')
            advanced_links.append(Link(
                text=_("Reject entry"),
                url=request.link(
                    self.directory.submission_action(
                        'reject', self.submission.id
                    )
                ),
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _("Do you really want to reject this entry?"),
                        _("This cannot be undone."),
                        _("Reject entry"),
                        _("Cancel")
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=request.url
                    )
                )
            ))

        links.append(LinkGroup(
            _("Advanced"),
            links=advanced_links,
            right_side=False
        ))

        return links


class ChatTicket(OrgTicketMixin, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'CHT'}  # type:ignore
    es_type_name = 'chat_tickets'

    def reference_group(self, request: 'OrgRequest') -> str:
        return self.handler.title


@handlers.registered_handler('CHT')
class ChatHandler(Handler):

    handler_title = _("Chats")
    code_title = _("Chats")

    @cached_property
    def collection(self) -> ChatCollection:
        return ChatCollection(self.session)

    @cached_property
    def chat(self) -> 'Chat | None':
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
        request: 'OrgRequest'  # type: ignore[override]
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
        request: 'OrgRequest'  # type: ignore[override]
    ) -> list[Link | LinkGroup]:
        return []
