from __future__ import annotations

from onegov.activity import Attendee, AttendeeCollection
from onegov.activity import BookingCollection
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.models import VacationActivity
from onegov.core.elements import Link, LinkGroup


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest
    from onegov.user import User
    from sqlalchemy.orm import Query
    from uuid import UUID


@FeriennetApp.userlinks()
def activity_links(request: FeriennetRequest, user: User) -> LinkGroup:
    activities: Query[tuple[str, str]] = (
        VacationActivityCollection(
            session=request.session,
            identity=request.identity
        )
        .query()
        .filter_by(username=user.username)
        .order_by(VacationActivity.order)
        .with_entities(
            VacationActivity.name,
            VacationActivity.title
        )
    )

    return LinkGroup(
        title=_('Activities'),
        links=[
            Link(
                title,
                request.class_link(VacationActivity, {'name': name})
            )
            for name, title in activities
        ]
    )


@FeriennetApp.userlinks()
def attendee_links(request: FeriennetRequest, user: User) -> LinkGroup:
    attendees: Query[tuple[UUID, str]] = (
        AttendeeCollection(request.session).query()
        .filter_by(username=user.username)
        .order_by(Attendee.name)
        .with_entities(Attendee.id, Attendee.name)
    )

    return LinkGroup(
        title=_('Attendees'),
        links=[
            Link(
                name,
                request.return_here(
                    request.class_link(Attendee, {'id': aid})
                )
            ) for aid, name in attendees
        ]
    )


@FeriennetApp.userlinks()
def booking_links(request: FeriennetRequest, user: User) -> LinkGroup:
    return LinkGroup(
        title=_('Bookings'),
        links=[
            Link(
                _('Bookings for ${period}', mapping={'period': period.title}),
                request.class_link(BookingCollection, {
                    'period_id': period.id,
                    'username': user.username
                })
            ) for period in request.app.periods
        ]
    )


@FeriennetApp.userlinks()
def billing_links(request: FeriennetRequest, user: User) -> LinkGroup:
    return LinkGroup(
        title=_('Billing'),
        links=[
            Link(
                _('Billing for ${period}', mapping={'period': period.title}),
                request.class_link(BillingCollection, {
                    'period_id': period.id,
                    'username': user.username
                })
            ) for period in request.app.periods
        ]
    )
