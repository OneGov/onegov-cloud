from __future__ import annotations

from itertools import groupby
from onegov.activity import Volunteer, VolunteerCollection
from onegov.core.security import Public, Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.forms import VolunteerForm
from onegov.feriennet.layout import DefaultLayout
from onegov.feriennet.layout import VolunteerFormLayout
from onegov.feriennet.layout import VolunteerLayout
from onegov.feriennet.models import VacationActivity
from onegov.feriennet.models import VolunteerCart
from onegov.feriennet.models import VolunteerCartAction
from operator import attrgetter
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable
    from onegov.core.types import JSON_ro, RenderData
    from onegov.activity.collections.volunteer import ReportRow
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


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

    return {
        'layout': layout,
        'title': _('Volunteers'),
        'records': records,
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

    return request.redirect(request.class_link(VolunteerCollection, {
        'period_id': self.need.occasion.period_id.hex}))


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


# Public, even though this is personal data -> the storage is limited to the
# current browser session, which is separated from other users
@FeriennetApp.json(model=VolunteerCart, permission=Public)
def view_cart(self: VolunteerCart, request: FeriennetRequest) -> JSON_ro:
    return list(self.for_frontend(DefaultLayout(self, request)))


@FeriennetApp.json(
    model=VolunteerCartAction,
    permission=Public,
    request_method='POST')
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

        for need_id in cart.ids():
            volunteers.add(
                token=token,
                need_id=need_id,
                **{
                    k: v for k, v in form.data.items() if k != 'csrf_token'
                })

        cart.clear()
        complete = True

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
