""" The onegov org collection of images uploaded to the site. """
from __future__ import annotations

import morepath

from morepath.request import Response
from onegov.core.crypto import random_token
from onegov.core.elements import BackLink
from onegov.core.security import Private, Public
from onegov.event import Event, EventCollection, OccurrenceCollection
from onegov.form import merge_forms, parse_form
from onegov.org import _, OrgApp
from onegov.org.cli import close_ticket
from onegov.org.elements import Link
from onegov.org.forms import EventForm
from onegov.org.layout import EventLayout, TicketLayout
from onegov.org.mail import send_ticket_mail
from onegov.org.models import TicketMessage, EventMessage
from onegov.org.models.extensions import AccessExtension
from onegov.org.models.ticket import EventSubmissionTicket
from onegov.org.utils import emails_for_new_ticket
from onegov.org.views.utils import show_tags, show_filters
from onegov.ticket import TicketCollection
from sedate import utcnow
from uuid import UUID, uuid4
from webob import exc


from typing import overload, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from typing import TypeVar
    from webob import Response as BaseResponse

    FormT = TypeVar('FormT', bound=Form)


def get_session_id(request: OrgRequest) -> str:
    if not request.browser_session.has('event_session_id'):
        request.browser_session.event_session_id = uuid4()

    return str(request.browser_session.event_session_id)


def assert_anonymous_access_only_temporary(
    request: OrgRequest,
    event: Event,
    view_ticket: EventSubmissionTicket | None = None
) -> None:
    """ Raises exceptions if the current user is anonymous and no longer
    should be given access to the event.

    Anonymous user should be able to access when creating a new event, but not
    anymore after that (i.e. when intiated and submitted). This is done by
    checking the browser session and/or a secret token in the URL.

    """
    if request.is_manager:
        return

    if view_ticket is not None and request.is_supporter:
        return

    if event.state not in ('initiated', 'submitted'):
        raise exc.HTTPForbidden()

    if not event.meta:
        raise exc.HTTPForbidden()

    session_id = get_session_id(request)
    if session_id in event.meta.get('session_ids', []):
        return

    token = event.meta.get('token')
    if token and token == request.params.get('token'):
        event.meta.setdefault('session_ids', [])
        event.meta['session_ids'].append(session_id)
        return

    raise exc.HTTPForbidden()


@overload
def event_form(
    model: object,
    request: OrgRequest,
    form: None = None
) -> type[EventForm]: ...


@overload
def event_form(
    model: object,
    request: OrgRequest,
    form: type[FormT]
) -> type[FormT]: ...


def event_form(
    model: object,
    request: OrgRequest,
    form: type[Form] | None = None
) -> type[Form]:

    if form is None:
        form = EventForm

    # unlike typical extended models, the property of this is defined
    # on the event model, while we are only using the form extension part
    # here
    if request.app.org.event_filter_type in ('filters', 'tags_and_filters'):
        # merge event filter form
        filter_definition = request.app.org.event_filter_definition
        if filter_definition:
            form = merge_forms(form, parse_form(filter_definition))

        if request.app.org.event_filter_type == 'filters':
            if not filter_definition:
                # we need to create a subclass so we're not modifying
                # the original form class in the below statement
                form = type('EventForm', (form, ), {})

            # prevent showing tags
            form.tags = None

    if request.is_manager:
        return AccessExtension().extend_form(form, request)

    return form


@OrgApp.view(
    model=Event,
    name='publish',
    permission=Private
)
def publish_event(
    self: Event,
    request: OrgRequest,
    view_ticket: EventSubmissionTicket | None = None
) -> RenderData | BaseResponse:
    """ Publish an event. """

    if self.state == 'initiated':
        request.warning(
            _('The event submitter has not yet completed his submission'))
        return request.redirect(request.link(self))
    if self.state == 'published':
        request.warning(
            _('This event has already been published'))
        return request.redirect(request.link(self))

    if self.meta and 'session_ids' in self.meta:
        del self.meta['session_ids']
    if self.meta and 'token' in self.meta:
        del self.meta['token']

    self.publish()

    ticket = TicketCollection(request.session).by_handler_id(self.id.hex)
    if view_ticket is not None and view_ticket != ticket:
        # if we access this through the ticket it had better match
        raise exc.HTTPNotFound()

    if not ticket:
        request.success(_("Successfully created the event '${title}'",
                        mapping={'title': self.title}))
        return request.redirect(request.link(
            OccurrenceCollection(request.session)
        ))

    request.success(_('You have accepted the event ${title}', mapping={
        'title': self.title
    }))

    if not self.source:
        # prevent sending emails for imported events when published via ticket
        send_ticket_mail(
            request=request,
            template='mail_event_accepted.pt',
            subject=_('Your event was accepted'),
            receivers=(self.meta['submitter_email'], ),
            ticket=ticket,
            content={
                'model': self,
                'ticket': ticket
            }
        )

    EventMessage.create(self, ticket, request, 'published')

    if view_ticket is not None:
        return request.redirect(request.link(view_ticket))

    return request.redirect(request.link(self))


@OrgApp.view(
    model=EventSubmissionTicket,
    name='publish-event',
    permission=Private
)
def publish_event_from_ticket(
    self: EventSubmissionTicket,
    request: OrgRequest
) -> RenderData | BaseResponse:

    event = self.handler.event
    if event is None or event.state != 'submitted':
        raise exc.HTTPNotFound()

    return publish_event(
        event,
        request,
        view_ticket=self
    )


@OrgApp.form(
    model=OccurrenceCollection,
    name='new',
    template='form.pt',
    form=event_form,
    permission=Public
)
def handle_new_event(
    self: OccurrenceCollection,
    request: OrgRequest,
    form: EventForm,
    layout: EventLayout | None = None
) -> RenderData | BaseResponse:
    """ Add a new event.

    The event is created and the user is redirected to a view where he can
    review his submission and submit it finally.

    """

    self.title = title = _('Submit an event')  # type:ignore[attr-defined]

    terms: str = _(
        "Only events taking place inside the town or events related to "
        "town societies are published. Events which are purely commercial are "
        "not published. There's no right to be published and already "
        "published events may be removed from the page without notification "
        "or reason."
    )

    if request.app.custom_event_form_lead is not None:
        terms = request.app.custom_event_form_lead

    if form.submitted(request):
        assert form.title.data is not None
        event = EventCollection(self.session).add(
            title=form.title.data,
            start=form.start,
            end=form.end,
            timezone=form.timezone,
        )
        event.meta.update({
            'session_ids': [get_session_id(request)],
            'token': random_token()
        })
        form.populate_obj(event)

        return morepath.redirect(request.link(event))

    # FIXME: This is pretty hacky, if this page happened to show the editbar
    #        then we would actually crash, the reason we don't crash is that
    #        we set the title on the model, this is pretty hacky, we should
    #        add a proper layout for this
    layout = layout or EventLayout(self, request)  # type:ignore
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'form_width': 'large',
        'lead': terms,
        'button_text': _('Continue'),
        'show_tags': show_tags(request),
        'show_filters': show_filters(request),
    }


@OrgApp.form(
    model=OccurrenceCollection,
    name='enter-event',
    template='form.pt',
    form=event_form,
    permission=Private
)
def handle_new_event_without_workflow(
    self: OccurrenceCollection,
    request: OrgRequest,
    form: EventForm,
    layout: EventLayout | None = None
) -> RenderData | BaseResponse:
    """ Create and submit a new event.

    The event is created and ticket workflow is skipped by setting
    the state to 'submitted'.

    """

    self.title = title = _('Add event')  # type:ignore[attr-defined]

    if form.submitted(request):
        assert form.title.data is not None
        event = EventCollection(self.session).add(
            title=form.title.data,
            start=form.start,
            end=form.end,
            timezone=form.timezone,
        )
        event.meta.update({
            'session_ids': [get_session_id(request)],
            'token': random_token()
        })
        event.state = 'submitted'
        form.populate_obj(event)
        return morepath.redirect(request.link(event, 'publish'))
    else:
        event_id = request.params.get('event_id')
        if event_id and isinstance(event_id, str):
            event_obj = EventCollection(self.session).by_id(UUID(event_id))
            if event_obj:
                form.process(obj=event_obj)

    # FIXME: same hack as in above view, add a proper layout
    layout = layout or EventLayout(self, request)  # type:ignore
    layout.editbar_links = []
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'form_width': 'large',
        'lead': '',
        'button_text': _('Submit'),
        'show_tags': show_tags(request),
        'show_filters': show_filters(request),
    }


@OrgApp.html(
    model=Event,
    template='event.pt',
    permission=Public,
    request_method='GET'
)
@OrgApp.html(
    model=Event,
    template='event.pt',
    permission=Public,
    request_method='POST'
)
def view_event(
    self: Event,
    request: OrgRequest,
    layout: EventLayout | None = None
) -> RenderData | BaseResponse:
    """ View an event.

    If the event is not already submitted, the submit form is displayed.

    A logged-in user can view all events and might edit them, an anonymous user
    will be redirected.
    """
    assert_anonymous_access_only_temporary(request, self)

    session = request.session
    ticket = TicketCollection(session).by_handler_id(self.id.hex)

    if 'complete' in request.POST:
        if self.state == 'initiated':
            self.submit()

            if not ticket:
                with session.no_autoflush:
                    ticket = TicketCollection(session).open_ticket(
                        handler_code='EVN', handler_id=self.id.hex
                    )
                    TicketMessage.create(ticket, request, 'opened', 'external')

                send_ticket_mail(
                    request=request,
                    template='mail_ticket_opened.pt',
                    subject=_('Your request has been registered'),
                    receivers=(self.meta['submitter_email'],),
                    ticket=ticket,
                )
                for email in emails_for_new_ticket(request, ticket):
                    send_ticket_mail(
                        request=request,
                        template='mail_ticket_opened_info.pt',
                        subject=_('New ticket'),
                        ticket=ticket,
                        receivers=(email, ),
                        content={
                            'model': ticket
                        }
                    )

                request.app.send_websocket(
                    channel=request.app.websockets_private_channel,
                    message={
                        'event': 'browser-notification',
                        'title': request.translate(_('New ticket')),
                        'created': ticket.created.isoformat()
                    },
                    groupids=request.app.groupids_for_ticket(ticket),
                )

                if request.auto_accept(ticket):
                    try:
                        assert request.auto_accept_user is not None
                        ticket.accept_ticket(request.auto_accept_user)
                        request.view(self, name='publish')
                    except Exception:
                        request.warning(_('Your request could not be '
                                          'accepted automatically!'))
                    else:
                        close_ticket(ticket, request.auto_accept_user, request)

        request.success(_('Thank you for your submission!'))

        return morepath.redirect(request.link(ticket, 'status'))

    return {
        'completable': self.state in ('initiated', 'submitted'),
        'edit_url': request.link(self, 'edit'),
        'event': self,
        'layout': layout or EventLayout(self, request),
        'ticket': ticket,
        'title': self.title,
        'show_tags': show_tags(request),
        'show_filters': show_filters(request),
    }


@OrgApp.form(
    model=Event,
    name='edit',
    template='form.pt',
    permission=Public,
    form=event_form
)
def handle_edit_event(
    self: Event,
    request: OrgRequest,
    form: EventForm,
    layout: EventLayout | TicketLayout | None = None,
    view_ticket: EventSubmissionTicket | None = None,
) -> RenderData | BaseResponse:
    """ Edit an event.

    An anonymous user might edit an initiated event, a logged in user can also
    edit all events.

    """

    assert_anonymous_access_only_temporary(request, self)

    if form.submitted(request):
        form.populate_obj(self)

        ticket = TicketCollection(request.session).by_handler_id(self.id.hex)
        if view_ticket is not None and view_ticket != ticket:
            # if we're accessing through the ticket it had better be the same
            raise exc.HTTPNotFound()

        if ticket:
            EventMessage.create(self, ticket, request, 'changed')
        request.success(_('Your changes were saved'))
        if view_ticket is not None:
            return request.redirect(request.link(view_ticket))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = layout or EventLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editmode_links[1] = BackLink(attrs={'class': 'cancel-link'})
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': self.title,
        'form': form,
        'form_width': 'large'
    }


@OrgApp.form(
    model=EventSubmissionTicket,
    name='edit-event',
    template='form.pt',
    permission=Public,
    form=event_form
)
def handle_edit_event_from_ticket(
    self: EventSubmissionTicket,
    request: OrgRequest,
    form: EventForm,
    layout: TicketLayout | None = None
) -> RenderData | BaseResponse:

    event = self.handler.event
    if event is None:
        raise exc.HTTPNotFound()

    if layout is None:
        layout = TicketLayout(self, request)

    layout.breadcrumbs[-1].attrs['href'] = request.link(self)

    return handle_edit_event(
        event,
        request,
        form,
        layout,
        view_ticket=self,
    )


@OrgApp.view(
    model=Event,
    name='withdraw',
    request_method='POST',
    permission=Private
)
def handle_withdraw_event(self: Event, request: OrgRequest) -> None:
    """ Withdraws an (imported) event. """

    request.assert_valid_csrf_token()

    if not self.source or self.state not in ('published', 'submitted'):
        raise exc.HTTPForbidden()

    self.withdraw()
    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(self.id.hex)
    if ticket:
        EventMessage.create(self, ticket, request, 'withdrawn')


@OrgApp.view(
    model=EventSubmissionTicket,
    name='withdraw-event',
    request_method='POST',
    permission=Private
)
def handle_withdraw_event_from_ticket(
    self: EventSubmissionTicket,
    request: OrgRequest
) -> None:

    event = self.handler.event
    if event is None:
        raise exc.HTTPNotFound()

    handle_withdraw_event(event, request)


@OrgApp.view(
    model=Event,
    request_method='DELETE',
    permission=Private
)
def handle_delete_event(self: Event, request: OrgRequest) -> None:
    """ Delete an event. """

    request.assert_valid_csrf_token()

    # Create a snapshot of the ticket to keep the useful information.
    tickets = TicketCollection(request.session)
    ticket = tickets.by_handler_id(self.id.hex)

    if ticket:
        ticket.create_snapshot(request)

        send_ticket_mail(
            request=request,
            template='mail_event_rejected.pt',
            subject=_('Your event was rejected'),
            receivers=(self.meta['submitter_email'], ),
            ticket=ticket,
            content={
                'model': self,
                'ticket': ticket
            }
        )

        EventMessage.create(self, ticket, request, 'deleted')

    EventCollection(request.session).delete(self)


@OrgApp.view(
    model=EventSubmissionTicket,
    name='delete-event',
    request_method='DELETE',
    permission=Private
)
def handle_delete_event_from_ticket(
    self: EventSubmissionTicket,
    request: OrgRequest
) -> None:

    event = self.handler.event
    if event is None or event.source:
        raise exc.HTTPNotFound()

    handle_delete_event(event, request)


@OrgApp.view(
    model=Event,
    name='ical',
    permission=Public
)
def ical_export_event(self: Event, request: OrgRequest) -> Response:
    """ Returns the event with all occurrences as ics. """

    try:
        url = request.link(self.occurrences[0])
    except IndexError:
        url = EventLayout(self, request).events_url

    return Response(
        self.as_ical(url=url),
        content_type='text/calendar',
        content_disposition='inline; filename=calendar.ics'
    )


@OrgApp.view(
    model=Event,
    name='latest',
    permission=Public
)
def view_latest_event(self: Event, request: OrgRequest) -> BaseResponse:
    """ Redirects to the latest occurrence of an event that is, either the
    next future event or the last event in the past if there are no more
    future events.

    """

    if not self.occurrences:
        # redirect to the event instead
        return morepath.redirect(request.link(self))

    now = utcnow()

    for occurrence in self.occurrences:
        if now < occurrence.start:
            return morepath.redirect(request.link(occurrence))

    return morepath.redirect(request.link(occurrence))
