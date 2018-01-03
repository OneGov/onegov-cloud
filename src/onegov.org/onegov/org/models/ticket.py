from cached_property import cached_property
from onegov.core.templates import render_macro
from onegov.directory import Directory, DirectoryEntry
from onegov.event import EventCollection
from onegov.form import FormSubmissionCollection
from onegov.org import _
from onegov.org.layout import DefaultLayout, EventLayout
from onegov.org.models.message import TicketNote
from onegov.org.new_elements import Link, LinkGroup, Confirm, Intercooler
from onegov.reservation import Allocation, Resource, Reservation
from onegov.ticket import Ticket, Handler, handlers
from purl import URL
from sqlalchemy.orm import object_session


class OrgTicketExtraText(object):

    @property
    def extra_localized_text(self):
        q = object_session(self).query(TicketNote)
        q = q.filter_by(channel_id=self.number)
        q = q.filter_by(type='ticket_note')
        q = q.with_entities(TicketNote.text)

        return ' '.join(n.text for n in q if n.text)


class FormSubmissionTicket(OrgTicketExtraText, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FRM'}
    es_type_name = 'submission_tickets'


class ReservationTicket(OrgTicketExtraText, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'RSV'}
    es_type_name = 'reservation_tickets'


class EventSubmissionTicket(OrgTicketExtraText, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EVN'}
    es_type_name = 'event_tickets'


class DirectoryEntryTicket(OrgTicketExtraText, Ticket):
    __mapper_args__ = {'polymorphic_identity': 'DIR'}
    es_type_name = 'directory_tickets'


@handlers.registered_handler('FRM')
class FormSubmissionHandler(Handler):

    handler_title = _("Form Submissions")

    @cached_property
    def collection(self):
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self):
        return self.collection.by_id(self.id)

    @cached_property
    def form(self):
        return self.submission.form_class(data=self.submission.data)

    @property
    def deleted(self):
        return self.submission is None

    @property
    def email(self):
        return self.submission.email

    @property
    def title(self):
        return self.submission.title

    @property
    def subtitle(self):
        return None

    @property
    def group(self):
        return self.submission.form.title

    @property
    def payment(self):
        return self.submission and self.submission.payment

    @property
    def extra_data(self):
        return self.submission and [
            v for v in self.submission.data.values()
            if isinstance(v, str)
        ]

    def get_summary(self, request):
        layout = DefaultLayout(self.submission, request)
        return render_macro(layout.macros['display_form'], request, {
            'form': self.form,
            'layout': layout
        })

    def get_links(self, request):
        links = []

        edit_link = URL(request.link(self.submission))
        edit_link = edit_link.query_param('edit', '').as_string()

        links.append(
            Link(
                text=_('Edit submission'),
                url=request.return_here(edit_link),
                attrs={'class': 'edit-link'}
            )
        )

        return links


@handlers.registered_handler('RSV')
class ReservationHandler(Handler):

    handler_title = _("Reservations")

    @cached_property
    def resource(self):
        query = self.session.query(Resource)
        query = query.filter(Resource.id == self.reservations[0].resource)

        return query.one()

    @cached_property
    def reservations(self):
        # libres allows for multiple reservations with a single request (token)
        # for now we don't really have that case in onegov.org, but we
        # try to be aware of it as much as possible
        query = self.session.query(Reservation)
        query = query.filter(Reservation.token == self.id)
        query = query.order_by(Reservation.start)

        return query.all()

    @cached_property
    def submission(self):
        return FormSubmissionCollection(self.session).by_id(self.id)

    @property
    def payment(self):
        return self.reservations and self.reservations[0].payment

    @property
    def deleted(self):
        return False if self.reservations else True

    @property
    def extra_data(self):
        return self.submission and [
            v for v in self.submission.data.values()
            if isinstance(v, str)
        ]

    @property
    def email(self):
        # the e-mail is the same over all reservations
        return self.reservations[0].email

    @property
    def title(self):
        parts = []

        for ix, reservation in enumerate(self.reservations):
            parts.append(self.get_reservation_title(reservation))

            if ix == 4:
                parts.append('…')
                break

        return ', '.join(parts)

    def get_reservation_title(self, reservation):
        return self.resource.reservation_title(reservation)

    @property
    def subtitle(self):
        if self.submission:
            return ', '.join(
                p for p in (self.email, self.submission.title) if p)
        elif self.reservations:
            return self.email
        else:
            return None

    @property
    def group(self):
        return self.resource.title

    @classmethod
    def handle_extra_parameters(cls, session, query, extra_parameters):
        if 'allocation_id' in extra_parameters:
            allocations = session.query(Allocation.group)
            allocations = allocations.filter(
                Allocation.id == int(extra_parameters['allocation_id']))

            tokens = session.query(Reservation.token)
            tokens = tokens.filter(
                Reservation.target.in_(allocations.subquery()))

            handler_ids = tuple(t[0].hex for t in tokens.all())

            if handler_ids:
                query = query.filter(Ticket.handler_id.in_(handler_ids))
            else:
                query = query.filter(False)

        return query

    def get_summary(self, request):
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

        return ''.join(parts)

    def get_links(self, request):

        if self.deleted:
            return []

        links = []

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
            link = URL(request.link(self.submission))
            link = link.query_param('edit', '')
            link = link.query_param('title', request.translate(
                _("Details about the reservation")))
            link = request.return_here(link.as_string())

            advanced_links.append(
                Link(
                    text=_('Edit details'),
                    url=link,
                    attrs={'class': ('edit-link', 'border')}
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
                    _("Reject reservations")
                ),
                Intercooler(
                    request_method='GET',
                    redirect_after=request.url
                )
            )
        ))

        for reservation in self.reservations:
            link = URL(request.link(reservation, 'reject'))
            link = link.query_param('reservation-id', reservation.id)
            link = request.return_here(link.as_string())

            title = self.get_reservation_title(reservation)
            advanced_links.append(Link(
                text=_("Reject ${title}", mapping={'title': title}),
                url=link,
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _("Do you really want to reject this reservation?"),
                        _("Rejecting ${title} can't be undone.", mapping={
                            'title': title
                        }),
                        _("Reject reservation")
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

    handler_title = _("Events")

    @cached_property
    def collection(self):
        return EventCollection(self.session)

    @cached_property
    def event(self):
        return self.collection.by_id(self.id)

    @property
    def deleted(self):
        return self.event is None

    @cached_property
    def email(self):
        return self.event.meta.get('submitter_email')

    @property
    def title(self):
        return self.event.title

    @property
    def subtitle(self):
        if self.deleted:
            return None

        parts = (
            self.event.meta.get('submitter_email'),
            '{:%d.%m.%Y %H:%M}'.format(self.event.start)
        )

        return ', '.join(p for p in parts if p)

    @property
    def extra_data(self):
        return [
            self.event.description,
            self.event.title,
            self.event.location
        ]

    @cached_property
    def group(self):
        return _("Event")

    def get_summary(self, request):
        layout = EventLayout(self.event, request)
        return render_macro(layout.macros['display_event'], request, {
            'event': self.event,
            'layout': layout
        })

    def get_links(self, request):

        links = []
        layout = EventLayout(self.event, request)

        if self.event and self.event.state == 'submitted':
            links.append(Link(
                text=_("Accept event"),
                url=request.return_here(request.link(self.event, 'publish')),
                attrs={'class': 'accept-link'},
            ))

        if self.event:
            links.append(LinkGroup(_("Advanced"), links=(
                Link(
                    text=_('Edit event'),
                    url=request.return_here(
                        request.link(self.event, 'edit')
                    ),
                    attrs={'class': ('edit-link', 'border')}
                ),
                Link(
                    text=_("Reject event"),
                    url=layout.csrf_protected_url(request.link(self.event)),
                    attrs={'class': ('delete-link')},
                    traits=(
                        Confirm(
                            _("Do you really want to reject this event?"),
                            _("Rejecting this event can't be undone."),
                            _("Reject event")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=request.link(self.ticket)
                        )
                    )
                )
            ), right_side=False))

        return links


@handlers.registered_handler('DIR')
class DirectoryEntryHandler(Handler):

    handler_title = _("Directory Entry Submissions")

    @cached_property
    def collection(self):
        return FormSubmissionCollection(self.session)

    @cached_property
    def submission(self):
        return self.collection.by_id(self.id)

    @cached_property
    def form(self):
        return self.submission.form_class(data=self.submission.data)

    @cached_property
    def directory(self):
        if self.submission:
            directory_id = self.submission.meta['directory']
        else:
            directory_id = self.ticket.handler_data['directory']

        return self.session.query(Directory).filter_by(id=directory_id).first()

    @property
    def deleted(self):
        if not self.directory:
            return True

        if self.state == 'adopted':
            name = self.ticket.handler_data.get('entry_name')
            return not self.directory.entry_with_name_exists(name)

        return False

    @property
    def email(self):
        return self.submission.email

    @property
    def title(self):
        return self.submission.title

    @property
    def subtitle(self):
        return None

    @property
    def group(self):
        return self.directory.title

    @property
    def payment(self):
        return self.submission and self.submission.payment

    @property
    def state(self):
        return self.ticket.handler_data.get('state')

    @property
    def extra_data(self):
        return self.submission and [
            v for v in self.submission.data.values()
            if isinstance(v, str)
        ]

    def get_summary(self, request):
        layout = DefaultLayout(self.submission, request)
        return render_macro(layout.macros['display_form'], request, {
            'form': self.form,
            'layout': layout
        })

    def get_links(self, request):

        links = []

        if not self.directory or self.deleted:
            return links

        if self.state is None:
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

        advanced_links = []

        if self.state is None:
            link = URL(request.link(self.submission))
            link = link.query_param('edit', '')
            link = link.query_param('title', request.translate(
                _("Edit details")))
            link = request.return_here(link.as_string())

            advanced_links.append(
                Link(
                    text=_('Edit details'),
                    url=link,
                    attrs={'class': ('edit-link', 'border')}
                )
            )

            advanced_links.append(Link(
                text=_("Reject"),
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
                        _("Reject entry")
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
