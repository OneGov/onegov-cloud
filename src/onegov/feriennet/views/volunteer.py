from __future__ import annotations

from itertools import groupby
from datetime import date

from markupsafe import Markup
from onegov.activity import Volunteer, VolunteerCollection
from onegov.core.security import Public, Secret, Private
from onegov.core.templates import render_macro
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.forms import VolunteerForm
from onegov.feriennet.layout import DefaultLayout
from onegov.feriennet.layout import VolunteerFormLayout
from onegov.feriennet.layout import VolunteerLayout
from onegov.org.mail import send_ticket_mail
from onegov.feriennet.models import VacationActivity
from onegov.feriennet.models import VolunteerCart
from onegov.feriennet.models import VolunteerCartAction
from onegov.org.models import TicketMessage, TicketChatMessage
from onegov.org.models.ticket import VolunteerTicket
from onegov.ticket import Ticket, TicketCollection
from operator import attrgetter
from uuid import uuid4
from webob import exc, Response


from typing import TYPE_CHECKING

from onegov.town6.layout import DefaultMailLayout
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.core.types import JSON_ro, RenderData
    from onegov.activity.collections.volunteer import ReportRow
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


def get_age(
        birth_date: date
) -> int:
    today = date.today()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


@FeriennetApp.html(
    model=VolunteerCollection,
    template='volunteers.pt',
    permission=Secret)
def view_volunteers(
    self: VolunteerCollection,
    request: FeriennetRequest
) -> RenderData:

    layout = VolunteerLayout(self, request)

    def grouped(
        records: Iterable[ReportRow],
        name: str
    ) -> tuple[tuple[ReportRow, ...], ...]:

        return tuple(
            tuple(g) for k, g in groupby(records, key=attrgetter(name)))

    records = tuple(self.report())
    if records:
        has_needs = True
    else:
        has_needs = False

    def state_change(record: ReportRow, state: str) -> str:
        assert record.volunteer_id is not None
        url = request.class_link(
            Volunteer, name=state, variables={'id': record.volunteer_id.hex})
        return layout.csrf_protected_url(url)

    def activity_link(activity_name: str) -> str:
        return request.class_link(VacationActivity, {'name': activity_name})

    tickets = {t.id: t for t in TicketCollection(
        request.session).query().filter(
        Ticket.handler_code == 'VOL',
    ).all()}

    return {
        'layout': layout,
        'title': _('Volunteers'),
        'records': records,
        'tickets': tickets,
        'grouped': grouped,
        'periods': request.app.periods,
        'period': self.period,
        'model': self,
        'has_needs': has_needs,
        'state_change': state_change,
        'activity_link': activity_link,
    }


@FeriennetApp.view(
    model=Volunteer,
    permission=Secret,
    name='open',
    request_method='POST')
def handle_open(self: Volunteer, request: FeriennetRequest) -> Response:
    request.assert_valid_csrf_token()
    self.state = 'open'

    return request.redirect(request.class_link(VolunteerCollection, {
        'period_id': self.need.occasion.period_id.hex}))


@FeriennetApp.view(
    model=Volunteer,
    permission=Secret,
    name='contacted',
    request_method='POST')
def handle_contacted(
    self: Volunteer,
    request: FeriennetRequest
) -> Response:

    request.assert_valid_csrf_token()
    self.state = 'contacted'

    return request.redirect(request.link(self, name='ticket_volunteer'))


@FeriennetApp.view(
    model=Volunteer,
    permission=Secret,
    name='confirmed',
    request_method='POST')
def handle_confirmed(
    self: Volunteer,
    request: FeriennetRequest
) -> Response:

    request.assert_valid_csrf_token()
    self.state = 'confirmed'

    return request.redirect(request.class_link(VolunteerCollection, {
        'period_id': self.need.occasion.period_id.hex}))


@FeriennetApp.view(
    model=Volunteer,
    permission=Secret,
    name='remove',
    request_method='POST')
def handle_remove(self: Volunteer, request: FeriennetRequest) -> Response:
    request.assert_valid_csrf_token()
    request.session.delete(self)

    return request.redirect(request.class_link(VolunteerCollection, {
        'period_id': self.need.occasion.period_id.hex}))


def get_confirmed(
        request: FeriennetRequest,
        need_id: str,
) -> int:
    return request.session.query(Volunteer).filter(
        Volunteer.need_id == need_id,
        Volunteer.state == 'confirmed'
    ).count()


def state_change(request: FeriennetRequest,
                 volunteer: Volunteer,
                 state: str,
                 layout: DefaultLayout) -> str:
    assert volunteer.id is not None
    url = request.class_link(
        Volunteer, name=state, variables={'id': volunteer.id.hex})
    return layout.csrf_protected_url(url)


@FeriennetApp.view(
    model=Volunteer,
    permission=Secret,
    name='ticket_contacted',
    request_method='POST')
def handle_ticket_contacted(self: Volunteer, request: FeriennetRequest) -> str:
    request.assert_valid_csrf_token()
    self.state = 'contacted'

    layout = DefaultLayout(self, request)

    return render_macro(
        layout.macros['volunteer_submission'],
        request,
        {
            'layout': layout,
            'subscription': self,
            'get_confirmed': get_confirmed,
            'get_age': get_age,
            'state_change': state_change,
            'ticket_state': 'pending'
        }
    )


@FeriennetApp.view(
    model=Volunteer,
    permission=Secret,
    name='ticket_open',
    request_method='POST')
def handle_ticket_open(self: Volunteer, request: FeriennetRequest) -> str:
    request.assert_valid_csrf_token()
    self.state = 'open'

    layout = DefaultLayout(self, request)

    return render_macro(
        layout.macros['volunteer_submission'],
        request,
        {
            'layout': layout,
            'subscription': self,
            'get_confirmed': get_confirmed,
            'get_age': get_age,
            'state_change': state_change,
            'ticket_state': 'pending'
        }
    )


@FeriennetApp.view(
    model=Volunteer,
    permission=Secret,
    name='ticket_confirmed',
    request_method='POST')
def handle_ticket_confirmed(self: Volunteer, request: FeriennetRequest) -> str:
    request.assert_valid_csrf_token()
    self.state = 'confirmed'

    layout = DefaultLayout(self, request)

    return render_macro(
        layout.macros['volunteer_submission'],
        request,
        {
            'layout': layout,
            'subscription': self,
            'get_confirmed': get_confirmed,
            'get_age': get_age,
            'state_change': state_change,
            'ticket_state': 'pending'
        }
    )


@FeriennetApp.view(
    model=Volunteer,
    permission=Secret,
    name='ticket_cancelled',
    request_method='POST')
def handle_ticket_cancelled(self: Volunteer, request: FeriennetRequest) -> str:
    request.assert_valid_csrf_token()
    self.state = 'cancelled'

    layout = DefaultLayout(self, request)

    return render_macro(
        layout.macros['volunteer_submission'],
        request,
        {
            'layout': layout,
            'subscription': self,
            'get_confirmed': get_confirmed,
            'get_age': get_age,
            'state_change': state_change,
            'ticket_state': 'pending'
        }
    )


# Public, even though this is personal data -> the storage is limited to the
# current browser session, which is separated from other users
@FeriennetApp.json(model=VolunteerCart, permission=Public, open_data=True)
def view_cart(self: VolunteerCart, request: FeriennetRequest) -> JSON_ro:
    return list(self.for_frontend(DefaultLayout(self, request)))


@FeriennetApp.json(
    model=VolunteerCartAction,
    permission=Public,
    request_method='POST',
    open_data=False
)
def execute_cart_action(
    self: VolunteerCartAction,
    request: FeriennetRequest
) -> JSON_ro:

    # FIXME: Despite the reasons listed below we should try to do better
    #
    # The CSRF check is disabled here, to make it easier to build the URL
    # in Javascript. This should be an exception, as this function here does
    # not provide a big attack surface, if any.
    #
    # request.assert_valid_csrf_token()

    return self.execute(request, VolunteerCart.from_request(request))


@FeriennetApp.form(
    model=VolunteerCart,
    permission=Public,
    form=VolunteerForm,
    template='volunteer_form.pt',
    name='submit')
def submit_volunteer(
    self: VolunteerCart,
    request: FeriennetRequest,
    form: VolunteerForm
) -> RenderData:

    layout = VolunteerFormLayout(self, request)
    request.include('volunteer-cart')
    complete = False

    if form.submitted(request):
        volunteers = VolunteerCollection(request.session, period=None)
        cart = VolunteerCart.from_request(request)
        token = uuid4()
        subscriptions = []

        for need_id in cart.ids():
            volunteer = volunteers.add(
                token=token,
                need_id=need_id,
                **{
                    k: v for k, v in form.data.items() if k != 'csrf_token'
                })
            subscriptions.append(volunteer)

        cart.clear()
        with request.session.no_autoflush:
            ticket = TicketCollection(request.session).open_ticket(
                handler_code='VOL', handler_id=token.hex
            )
            TicketMessage.create(ticket, request, 'opened', 'external')
        complete = True

        subject = request.translate(_('Subscription as a volunteer'))
        custom_text_before_list = Markup(  # nosec: B704
            request.app.org.meta.get('before_list_text', '').strip())
        custom_text_after_list = Markup(  # nosec: B704
            request.app.org.meta.get('after_list_text', '').strip())

        send_ticket_mail(
            request=request,
            template='mail_volunteer_subscription.pt',
            subject=subject,
            receivers=(subscriptions[0].email, ),
            ticket=ticket,
            force=True,
            content={
                'layout': DefaultMailLayout(self, request),
                'title': subject,
                'subscriptions': subscriptions,
                'custom_text_before_list': custom_text_before_list,
                'custom_text_after_list': custom_text_after_list,
            }
        )
    else:
        form.process(obj=self)

    return {
        'layout': layout,
        'form': form,
        'title': _('Register as Volunteer'),
        'complete': complete,
        'cart_url': request.class_link(VolunteerCart),
        'cart_submit_url': request.class_link(VolunteerCart, name='submit'),
        'cart_action_url': request.class_link(VolunteerCartAction, {
            'action': 'action',
            'target': 'target',
        }),
    }


@FeriennetApp.view(
    model=VolunteerTicket,
    name='send-status-mail',
    permission=Private
)
def send_final_submission_states(
    self: VolunteerTicket,
    request: FeriennetRequest
) -> Response | None:

    if self.handler.deleted:
        raise exc.HTTPNotFound()

    if any(v.state in (
        'open', 'contacted') for v in self.handler.volunteer_cart):
        request.alert(_(
            'Not all subscriptions are in a final state. Please '
            'make sure all subscriptions are either confirmed or rejected.'))
    else:
        recipient = self.handler.email
        if recipient:

            custom_text_before_list = Markup(  # nosec: B704
            request.app.org.meta.get('before_status_list_text', '').strip())
            custom_text_after_list = Markup(  # nosec: B704
            request.app.org.meta.get('after_status_list_text', '').strip())
            assert request.current_username
            TicketChatMessage.create(
                self,
                request,
                text=request.translate(_(
                    'The subscriptions have been processed and the status '
                    'mail has been sent to the volunteer.')),
                owner=request.current_username,
                recipient=recipient,
                notify=False,
                origin='internal'
            )
            send_ticket_mail(
                request=request,
                template='mail_final_submission_states.pt',
                subject=_(
                    'Your subscriptions as a volunteer have been processed.'),
                receivers=(recipient, ),
                ticket=self,
                force=True,
                content={
                    'model': self,
                    'subscriptions': self.handler.volunteer_cart,
                    'custom_text_before_list': custom_text_before_list,
                    'custom_text_after_list': custom_text_after_list,
                }
            )
            request.success(_(
                'Successfully sent ${count} emails',
                mapping={'count': 1}
            ))
        else:
            request.alert(_('The submitter email is not available'))

    if request.headers.get('X-IC-Request'):
        return None
    return request.redirect(request.link(self))
