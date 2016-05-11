from cached_property import cached_property
from libres.db.models import Allocation, Reservation
from onegov.core import utils
from onegov.core.templates import render_macro
from onegov.event import EventCollection
from onegov.form import FormSubmissionCollection
from onegov.libres import Resource
from onegov.ticket import Ticket, Handler, handlers
from onegov.town import _
from onegov.town.elements import DeleteLink, Link, LinkGroup
from onegov.town.layout import DefaultLayout, EventLayout
from onegov.town.utils import correct_time_range
from purl import URL


class FormSubmissionTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'FRM'}
    es_type_name = 'submission_tickets'


class ReservationTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'RSV'}
    es_type_name = 'reservation_tickets'


class EventSubmissionTicket(Ticket):
    __mapper_args__ = {'polymorphic_identity': 'EVN'}
    es_type_name = 'event_tickets'


@handlers.registered_handler('FRM')
class FormSubmissionHandler(Handler):

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
    def extra_data(self):
        return self.submission and [
            v for v in self.submission.data.values()
            if not utils.is_non_string_iterable(v)
        ]

    def get_summary(self, request):
        layout = DefaultLayout(self.submission, request)
        return render_macro(layout.macros['display_form'], request, {
            'form': self.form,
            'layout': layout
        })

    def get_links(self, request):

        edit_link = URL(request.link(self.submission))
        edit_link = edit_link.query_param('edit', '')
        edit_link = edit_link.query_param('return-to', request.url)

        return [
            Link(
                text=_('Edit submission'),
                url=edit_link.as_string(),
                classes=('edit-link', )
            )
        ]


@handlers.registered_handler('RSV')
class ReservationHandler(Handler):

    @cached_property
    def resource(self):
        query = self.session.query(Resource)
        query = query.filter(Resource.id == self.reservations[0].resource)

        return query.one()

    @cached_property
    def reservations(self):
        # libres allows for multiple reservations with a single request (token)
        # for now we don't really have that case in onegov.town, but we
        # try to be aware of it as much as possible
        query = self.session.query(Reservation)
        query = query.filter(Reservation.token == self.id)
        query = query.order_by(Reservation.start)

        return query.all()

    @cached_property
    def submission(self):
        return FormSubmissionCollection(self.session).by_id(self.id)

    @property
    def deleted(self):
        return False if self.reservations else True

    @property
    def extra_data(self):
        return self.submission and [
            v for v in self.submission.data.values()
            if not utils.is_non_string_iterable(v)
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
        if self.resource.type == 'daypass':
            template = '{start:%d.%m.%Y} ({quota})'
        elif self.resource.type == 'room':
            template = '{start:%d.%m.%Y} {start:%H:%M} - {end:%H:%M}'
        else:
            raise NotImplementedError

        return correct_time_range(
            template.format(
                start=reservation.display_start(),
                end=reservation.display_end(),
                quota=reservation.quota
            )
        )

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
            link = URL(request.link(self.reservations[0], 'annehmen'))
            link = link.query_param('return-to', request.url)

            links.append(
                Link(
                    text=_("Accept all reservations"),
                    url=link.as_string(),
                    classes=('accept-link', )
                )
            )

        reject_all_link = URL(request.link(self.reservations[0], 'absagen'))
        reject_all_link = reject_all_link.query_param('return-to', request.url)

        reject = LinkGroup(
            _("Reject reservations"),
            [
                DeleteLink(
                    text=_("Reject all"),
                    url=reject_all_link.as_string(),
                    confirm=_(
                        "Do you really want to reject all reservations?"
                    ),
                    extra_information=_(
                        "Rejecting these reservations can't be undone."
                    ),
                    yes_button_text=_("Reject reservations"),
                    request_method='GET',
                    redirect_after=request.url
                )
            ],
            right_side=False
        )

        for reservation in self.reservations:
            link = URL(request.link(reservation, 'absagen'))
            link = link.query_param('reservation-id', reservation.id)
            link = link.query_param('return-to', request.url)
            title = self.get_reservation_title(reservation)
            reject.links.append(
                DeleteLink(
                    text=_("Reject ${title}", mapping={'title': title}),
                    url=link.as_string(),
                    confirm=_(
                        "Do you really want to reject this reservation?"
                    ),
                    extra_information=_(
                        "Rejecting ${title} can't be undone.", mapping={
                            'title': title
                        }
                    ),
                    yes_button_text=_("Reject reservation"),
                    request_method='GET',
                    redirect_after=request.url
                )
            )

        links.append(reject)

        if self.submission:
            link = URL(request.link(self.submission))
            link = link.query_param('edit', '')
            link = link.query_param('return-to', request.url)
            link = link.query_param('title', request.translate(
                _("Details about the reservation"))
            )

            links.append(
                Link(
                    text=_('Edit details'),
                    url=link.as_string(),
                    classes=('edit-link', )
                )
            )

        return links


@handlers.registered_handler('EVN')
class EventSubmissionHandler(Handler):

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
        if not self.event:
            return []

        links = []
        if self.event.state == 'submitted':
            link = URL(request.link(self.event, 'publish'))
            link = link.query_param('return-to', request.link(self.ticket))
            links.append(Link(
                text=_("Accept event"),
                url=link.as_string(),
                classes=('accept-link', ),
            ))

        links.append(DeleteLink(
            text=_("Reject event"),
            url=request.link(self.event),
            confirm=_("Do you really want to reject this event?"),
            extra_information=_(
                "Rejecting this event can't be undone."
            ),
            yes_button_text=_("Reject event"),
            redirect_after=request.link(self.ticket)
        ))

        link = URL(request.link(self.event, 'bearbeiten'))
        link = link.query_param('return-to', request.url)
        links.append(Link(
            text=_('Edit event'),
            url=link.as_string(),
            classes=('edit-link', )
        ))

        return links
