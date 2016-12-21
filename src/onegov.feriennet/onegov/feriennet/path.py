from onegov.activity import Booking, BookingCollection
from onegov.activity import InvoiceItemCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import Period, PeriodCollection
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.converters import age_range_converter
from onegov.feriennet.models import InvoiceAction, VacationActivity
from onegov.feriennet.models import NotificationTemplate
from uuid import UUID


@FeriennetApp.path(
    model=VacationActivityCollection,
    path='/angebote',
    converters=dict(
        tags=[str],
        states=[str],
        durations=[int],
        age_ranges=[age_range_converter],
        owners=[str],
        period_ids=[UUID]
    ))
def get_vacation_activities(request, app, page=0,
                            tags=None,
                            states=None,
                            durations=None,
                            age_ranges=None,
                            owners=None,
                            period_ids=None):

    return VacationActivityCollection(
        session=app.session(),
        page=page,
        identity=request.identity,
        tags=tags,
        states=states,
        durations=durations,
        age_ranges=age_ranges,
        owners=owners,
        period_ids=period_ids
    )


@FeriennetApp.path(
    model=VacationActivity,
    path='/angebot/{name}')
def get_vacation_activity(request, app, name):
    return VacationActivityCollection(
        app.session(), identity=request.identity).by_name(name)


@FeriennetApp.path(
    model=Occasion,
    path='/durchfuehrungen/{id}',
    converters=dict(id=UUID))
def get_occasion(request, app, id):
    return OccasionCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=PeriodCollection,
    path='/perioden')
def get_periods(request, app):
    return PeriodCollection(app.session())


@FeriennetApp.path(
    model=Period,
    path='/periode/{id}',
    converters=dict(id=UUID))
def get_period(request, app, id):
    return PeriodCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=BookingCollection,
    path='/meine-buchungen',
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
        periods = PeriodCollection(app.session())
        period = periods.active() or periods.query().first()

        if period:
            period_id = period.id

    return BookingCollection(app.session(), period_id, username)


@FeriennetApp.path(
    model=Booking,
    path='/buchung/{id}',
    converters=dict(id=UUID))
def get_booking(request, app, id):
    return BookingCollection(app.session()).by_id(id)


@FeriennetApp.path(
    model=MatchCollection,
    path='/zuteilungen',
    converters=dict(period_id=UUID))
def get_matches(request, app, period_id):
    # the default period is the active period or the first we can find
    periods = PeriodCollection(app.session())

    if not period_id:
        period = periods.active() or periods.query().first()
    else:
        period = periods.by_id(period_id)

    if not period:
        return None

    return MatchCollection(app.session(), period)


@FeriennetApp.path(
    model=BillingCollection,
    path='/rechnungen',
    converters=dict(period_id=UUID))
def get_billing(request, app, period_id, username=None, expand=False):
    # the default period is the active period or the first we can find
    periods = PeriodCollection(app.session())

    if not period_id:
        period = periods.active() or periods.query().first()
    else:
        period = periods.by_id(period_id)

    if not period:
        return None

    return BillingCollection(app.session(), period, username, expand)


@FeriennetApp.path(
    model=InvoiceAction,
    path='/rechnungsaktion/{id}/{action}',
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
    path='/meine-rechnungen')
def get_my_invoies(request, app, username=None):

    # only admins can actually specify the username
    if not request.is_admin:
        username = request.current_username

    # the default username is the current user
    if not username:
        username = request.current_username

    return InvoiceItemCollection(app.session(), username)


@FeriennetApp.path(
    model=OccasionAttendeeCollection,
    path='/teilnehmer',
    converters=dict(period_id=UUID))
def get_occasion_attendee_collection(request, app, period_id=None):

    periods = PeriodCollection(app.session())

    if not period_id:
        period = periods.active() or periods.query().first()
    else:
        period = periods.by_id(period_id)

    if not period:
        return None

    # non-admins are automatically limited to the activites they own
    if request.is_admin:
        username = None
    else:
        username = request.current_username

    return OccasionAttendeeCollection(app.session(), period, username)


@FeriennetApp.path(
    model=NotificationTemplateCollection,
    path='/mitteilungen')
def get_notification_template_collection(request, app):
    return NotificationTemplateCollection(app.session())


@FeriennetApp.path(
    model=NotificationTemplate,
    path='/mitteilung/{id}',
    converters=dict(id=UUID))
def get_notification_template(request, app, id):
    return NotificationTemplateCollection(app.session()).by_id(id)
