from onegov.activity import Attendee, AttendeeCollection
from onegov.activity import BookingCollection
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.models import VacationActivity
from onegov.org.new_elements import Link, LinkGroup


@FeriennetApp.userlinks()
def activity_links(request, user):
    activities = VacationActivityCollection(
        session=request.session,
        identity=request.identity
    )

    activities = activities.query()
    activities = activities.filter_by(username=user.username)
    activities = activities.order_by(VacationActivity.order)

    activities = activities.with_entities(
        VacationActivity.name, VacationActivity.title)

    return LinkGroup(
        title=_("Activities"),
        links=[
            Link(
                activity.title,
                request.class_link(VacationActivity, {'name': activity.name})
            )
            for activity in activities
        ]
    )


@FeriennetApp.userlinks()
def attendee_links(request, user):
    attendees = AttendeeCollection(request.session).query()
    attendees = attendees.filter_by(username=user.username)
    attendees = attendees.order_by(Attendee.name)
    attendees = attendees.with_entities(Attendee.id, Attendee.name)

    return LinkGroup(
        title=_("Attendees"),
        links=[
            Link(
                attendee.name,
                request.return_here(
                    request.class_link(Attendee, {'id': attendee.id})
                )
            ) for attendee in attendees
        ]
    )


@FeriennetApp.userlinks()
def booking_links(request, user):
    return LinkGroup(
        title=_("Bookings"),
        links=[
            Link(
                _("Bookings for ${period}", mapping={'period': period.title}),
                request.class_link(BookingCollection, {
                    'period_id': period.id,
                    'username': user.username
                })
            ) for period in request.app.periods
        ]
    )


@FeriennetApp.userlinks()
def billing_links(request, user):
    return LinkGroup(
        title=_("Billing"),
        links=[
            Link(
                _("Billing for ${period}", mapping={'period': period.title}),
                request.class_link(BillingCollection, {
                    'period_id': period.id,
                    'username': user.username
                })
            ) for period in request.app.periods
        ]
    )
