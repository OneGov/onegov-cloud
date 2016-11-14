from onegov.activity import Booking, BookingCollection
from onegov.activity import Occasion, OccasionCollection
from onegov.activity import Period, PeriodCollection
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.converters import age_range_converter
from onegov.feriennet.models import VacationActivity
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
    path='/buchungen',
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
def get_matches(request, app, period_id, username=None):
    # non-admins are limited to the ativites they own, admins may view
    # all the occasions (this differs slighty from the booking collection path)
    if not request.is_admin:
        username = request.current_username

    # the default period is the active period or the first we can find
    periods = PeriodCollection(app.session())

    if not period_id:
        period = periods.active() or periods.query().first()
    else:
        period = periods.by_id(period_id)

    if not period:
        return None

    return MatchCollection(app.session(), period, username)
