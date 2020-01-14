from onegov.activity import ActivityFilter
from onegov.activity import Attendee, AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import InvoiceCollection, InvoiceItem
from onegov.activity import Occasion, OccasionCollection, OccasionNeed
from onegov.activity import Period, PeriodCollection
from onegov.activity import Volunteer, VolunteerCollection
from onegov.activity.utils import is_valid_group_code
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.models import Calendar
from onegov.feriennet.models import GroupInvite
from onegov.feriennet.models import InvoiceAction, VacationActivity
from onegov.feriennet.models import NotificationTemplate
from onegov.feriennet.models import VolunteerCart
from onegov.feriennet.models import VolunteerCartAction
from onegov.org.converters import keywords_converter
from onegov.core.converters import integer_range_converter
from uuid import UUID


@FeriennetApp.path(
    model=VacationActivityCollection,
    path='/activities',
    converters={
        'filter': keywords_converter,
        'pages': integer_range_converter
    })
def get_vacation_activities(request, app, pages=None, filter=None):
    filter = filter and ActivityFilter(**filter) or ActivityFilter()

    if not request.is_organiser:
        filter.period_ids = app.active_period and [app.active_period.id]

    collection = VacationActivityCollection(
        session=app.session(),
        pages=pages,
        identity=request.identity,
        filter=filter
    )

    # prevent large lookups
    return collection.by_page_range(
        collection.limit_range(collection.pages, 'down')
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
def get_billing(request, app, period_id,
                username=None, expand=False, state='unpaid'):
    # the default period is the active period or the first we can find
    if not period_id:
        period = app.default_period
    else:
        period = PeriodCollection(app.session()).by_id(period_id)

    if not period:
        return None

    return BillingCollection(request, period, username, expand, state)


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
    model=InvoiceCollection,
    path='/my-bills',
    converters=dict(invoice=UUID))
def get_my_invoices(request, app, username=None, invoice=None):
    # only admins can actually specify the username/invoice
    if not request.is_admin:
        username, invoice = None, None

    # the default username is the current user
    if not username:
        username = request.current_username

    # the default period is the active period
    if not invoice:
        invoice = request.app.default_period and request.app.default_period.id

    # at this point the username has to exist...
    user_id = request.app.user_ids_by_name.get(username)

    # ...as well as the invoice
    if not user_id or not invoice:
        return None

    # XXX username should be user_id, invoice should be period_id
    # this should be changed, but needs to be changed by replacing
    # the username everywhere
    return app.invoice_collection(period_id=invoice, user_id=user_id)


@FeriennetApp.path(
    model=InvoiceItem,
    path='/invoice-item/{id}')
def get_my_invoice_item(request, app, id):
    return request.session.query(InvoiceItem).filter_by(id=id).first()


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
    converters=dict(id=UUID, period_id=UUID))
def get_notification_template(request, app, id, period_id):
    template = NotificationTemplateCollection(app.session()).by_id(id)

    if template:
        template.period_id = period_id or app.active_period.id

    return template


@FeriennetApp.path(
    model=Calendar,
    path='/calendar/{name}/{token}')
def get_calendar(request, name, token):
    return Calendar.from_name_and_token(request.session, name, token)


@FeriennetApp.path(
    model=GroupInvite,
    path='/join/{group_code}')
def get_group_invite(app, request, group_code, username=None):
    group_code = group_code.upper()

    if not is_valid_group_code(group_code):
        return None

    if not request.is_admin:
        username = request.current_username

    invite = GroupInvite(request.session, group_code, username)
    return invite.exists and invite or None


@FeriennetApp.path(
    model=OccasionNeed,
    path='/occasion-need/{id}',
    converters=dict(id=UUID))
def get_occasion_need(request, id):
    return request.session.query(OccasionNeed).filter_by(id=id).first()


@FeriennetApp.path(
    model=VolunteerCart,
    path='/volunteer-cart')
def get_volunteer_cart(request):
    return VolunteerCart.from_request(request)


@FeriennetApp.path(
    model=VolunteerCartAction,
    path='/volunteer-cart-action/{action}/{target}',
    converters=dict(target=UUID))
def get_volunteer_cart_action(request, action, target):
    return VolunteerCartAction(action, target)


@FeriennetApp.path(
    model=VolunteerCollection,
    path='/volunteers/{period_id}',
    converters=dict(period_id=UUID))
def get_volunteers(request, period_id):
    if not request.app.show_volunteers(request):
        return None

    period = request.app.periods_by_id.get(period_id.hex)

    if not period:
        return None

    return VolunteerCollection(request.session, period)


@FeriennetApp.path(
    model=Volunteer,
    path='/volunteer/{id}',
    converters=dict(id=UUID))
def get_volunteer(request, id):
    return VolunteerCollection(request.session, None).by_id(id)
