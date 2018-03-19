from onegov.activity import Booking, BookingCollection
from onegov.activity import InvoiceItemCollection, InvoiceItem
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import Period, PeriodCollection
from onegov.activity import Attendee, AttendeeCollection
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.converters import age_range_converter
from onegov.feriennet.converters import date_range_converter
from onegov.feriennet.models import Calendar
from onegov.feriennet.models import InvoiceAction, VacationActivity
from onegov.feriennet.models import NotificationTemplate
from uuid import UUID


@FeriennetApp.path(
    model=VacationActivityCollection,
    path='/activities',
    converters=dict(
        tags=[str],
        states=[str],
        durations=[int],
        age_ranges=[age_range_converter],
        owners=[str],
        period_ids=[UUID],
        dateranges=[date_range_converter],
        weekdays=[int],
        municipalities=[str],
        available=[str]
    ))
def get_vacation_activities(request, app, page=0,
                            tags=None,
                            states=None,
                            durations=None,
                            age_ranges=None,
                            owners=None,
                            period_ids=None,
                            dateranges=None,
                            weekdays=None,
                            municipalities=None,
                            available=None):

    if not request.is_organiser:
        period = app.active_period
        period_ids = period and [period.id] or None

    return VacationActivityCollection(
        session=app.session(),
        page=page,
        identity=request.identity,
        tags=tags,
        states=states,
        durations=durations,
        age_ranges=age_ranges,
        owners=owners,
        period_ids=period_ids,
        dateranges=dateranges,
        weekdays=weekdays,
        municipalities=municipalities,
        available=available
    )


@FeriennetApp.path(
    model=VacationActivity,
    path='/activity/{name}')
def get_vacation_activity(request, app, name):
    return VacationActivityCollection(
        app.session(), identity=request.identity).by_name(name)


@FeriennetApp.path(
    model=Occasion,
    path='/occasions/{id}',
    converters=dict(id=UUID))
def get_occasion(request, app, id):
    return OccasionCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=PeriodCollection,
    path='/periods')
def get_periods(request, app):
    return PeriodCollection(app.session())


@FeriennetApp.path(
    model=Period,
    path='/period/{id}',
    converters=dict(id=UUID))
def get_period(request, app, id):
    return PeriodCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=BookingCollection,
    path='/my-bookings',
    converters=dict(period_id=UUID))
def get_my_bookings(request, app, period_id=None, username=None):
    # only admins can actually specify the username
    if not request.is_admin:
        username = request.current_username

    # the default username is the current user
    if not username:
        username = request.current_username

    # the default period is the active period or the first we can find
    if not period_id:
        period = app.default_period

        if period:
            period_id = period.id

    return BookingCollection(app.session(), period_id, username)


@FeriennetApp.path(
    model=Booking,
    path='/booking/{id}',
    converters=dict(id=UUID))
def get_booking(request, app, id):
    return BookingCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=Attendee,
    path='/attendee/{id}',
    converters=dict(id=UUID))
def get_attendee(request, app, id):
    return AttendeeCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=MatchCollection,
    path='/matching',
    converters=dict(period_id=UUID, states=[str]))
def get_matches(request, app, period_id, states=None):
    # the default period is the active period or the first we can find
    if not period_id:
        period = app.default_period
    else:
        period = PeriodCollection(app.session()).by_id(period_id)

    if not period:
        return None

    return MatchCollection(app.session(), period, states)


@FeriennetApp.path(
    model=BillingCollection,
    path='/billing',
    converters=dict(period_id=UUID))
def get_billing(request, app, period_id, username=None, expand=False):
    # the default period is the active period or the first we can find
    if not period_id:
        period = app.default_period
    else:
        period = PeriodCollection(app.session()).by_id(period_id)

    if not period:
        return None

    return BillingCollection(app.session(), period, username, expand)


@FeriennetApp.path(
    model=InvoiceAction,
    path='/invoice-action/{id}/{action}',
    converters=dict(id=UUID))
def get_invoice_action(request, app, id, action, extend_to=None):
    action = InvoiceAction(
        session=app.session(),
        id=id,
        action=action,
        extend_to=extend_to
    )
    return action.valid and action or None


@FeriennetApp.path(
    model=InvoiceItemCollection,
    path='/my-bills')
def get_my_invoies(request, app, username=None, invoice=None):

    # only admins can actually specify the username and/or invoice
    if not request.is_admin:
        username = request.current_username
        invoice = None

    # the default username is the current user
    if not username:
        username = request.current_username

    return InvoiceItemCollection(app.session(), username, invoice)


@FeriennetApp.path(
    model=InvoiceItem,
    path='/invoice-item/{id}')
def get_my_invoice_item(request, app, id):
    return InvoiceItemCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=OccasionAttendeeCollection,
    path='/attendees/{activity_name}',
    converters=dict(period_id=UUID))
def get_occasion_attendee_collection(request, app, activity_name,
                                     period_id=None):

    # load the activity
    activity = get_vacation_activity(request, app, activity_name)

    if not activity:
        return None

    # the default period is the active period or the first we can find
    if not period_id:
        period = app.default_period
    else:
        period = PeriodCollection(app.session()).by_id(period_id)

    if not period:
        return None

    # non-admins are automatically limited to the activites they own
    if request.is_admin:
        username = None
    else:
        username = request.current_username

    return OccasionAttendeeCollection(
        app.session(), period, activity, username)


@FeriennetApp.path(
    model=NotificationTemplateCollection,
    path='/notifications')
def get_notification_template_collection(request, app):
    return NotificationTemplateCollection(app.session())


@FeriennetApp.path(
    model=NotificationTemplate,
    path='/notification/{id}',
    converters=dict(id=UUID))
def get_notification_template(request, app, id):
    return NotificationTemplateCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=Calendar,
    path='/calendar/{name}/{token}')
def get_calendar(request, name, token):
    return Calendar.from_name_and_token(request.session, name, token)
