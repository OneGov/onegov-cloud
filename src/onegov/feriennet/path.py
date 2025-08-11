from __future__ import annotations

from onegov.activity import ActivityFilter
from onegov.activity import Attendee, AttendeeCollection
from onegov.activity import Booking, BookingCollection
from onegov.activity import ActivityInvoiceItem, BookingPeriodInvoiceCollection
from onegov.activity import Occasion, OccasionCollection, OccasionNeed
from onegov.activity import BookingPeriod, BookingPeriodCollection
from onegov.activity import Volunteer, VolunteerCollection
from onegov.activity.utils import is_valid_group_code
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.collections import MatchCollection
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.collections import VacationActivityCollection
from onegov.feriennet.collections.match import OccasionState
from onegov.feriennet.models import Calendar
from onegov.feriennet.models import GroupInvite
from onegov.feriennet.models import InvoiceAction, VacationActivity
from onegov.feriennet.models import NotificationTemplate
from onegov.feriennet.models import VolunteerCart
from onegov.feriennet.models import VolunteerCartAction
from onegov.org.converters import keywords_converter
from onegov.core.converters import integer_range_converter, LiteralConverter
from uuid import UUID


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity.models import BookingPeriodMeta
    from onegov.feriennet.request import FeriennetRequest


@FeriennetApp.path(
    model=VacationActivityCollection,
    path='/activities',
    converters={
        'filter': keywords_converter,
        'pages': integer_range_converter
    })
def get_vacation_activities(
    request: FeriennetRequest,
    app: FeriennetApp,
    pages: tuple[int, int] | None = None,
    filter: dict[str, list[str]] | None = None
) -> VacationActivityCollection:

    filter_obj = ActivityFilter(**filter) if filter else ActivityFilter()

    if not request.is_organiser:
        filter_obj.period_ids = (
            {app.active_period.id} if app.active_period else set())

    collection = VacationActivityCollection(
        session=app.session(),
        pages=pages,
        identity=request.identity,
        filter=filter_obj
    )

    # prevent large lookups
    return collection.by_page_range(
        collection.limit_range(collection.pages, 'down')
    )


@FeriennetApp.path(
    model=VacationActivity,
    path='/activity/{name}')
def get_vacation_activity(
    request: FeriennetRequest,
    name: str
) -> VacationActivity | None:
    return VacationActivityCollection(
        request.session, identity=request.identity).by_name(name)


@FeriennetApp.path(
    model=Occasion,
    path='/occasions/{id}',
    converters={'id': UUID})
def get_occasion(request: FeriennetRequest, id: UUID) -> Occasion | None:
    return OccasionCollection(request.session).by_id(id)


@FeriennetApp.path(
    model=BookingPeriodCollection,
    path='/periods')
def get_periods(request: FeriennetRequest) -> BookingPeriodCollection:
    return BookingPeriodCollection(request.session)


@FeriennetApp.path(
    model=BookingPeriod,
    path='/period/{id}',
    converters={'id': UUID})
def get_period(request: FeriennetRequest, id: UUID) -> BookingPeriod | None:
    return BookingPeriodCollection(request.session).by_id(id)


@FeriennetApp.path(
    model=BookingCollection,
    path='/my-bookings',
    converters={'period_id': UUID})
def get_my_bookings(
    request: FeriennetRequest,
    app: FeriennetApp,
    period_id: UUID | None = None,
    username: str | None = None
) -> BookingCollection:

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
    converters={'id': UUID})
def get_booking(request: FeriennetRequest, id: UUID) -> Booking | None:
    return BookingCollection(request.session).by_id(id)


@FeriennetApp.path(
    model=Attendee,
    path='/attendee/{id}',
    converters={'id': UUID})
def get_attendee(request: FeriennetRequest, id: UUID) -> Attendee | None:
    return AttendeeCollection(request.session).by_id(id)


@FeriennetApp.path(
    model=MatchCollection,
    path='/matching',
    converters={
        'period_id': UUID,
        'states': [LiteralConverter(OccasionState)]
    })
def get_matches(
    request: FeriennetRequest,
    app: FeriennetApp,
    period_id: UUID | None,
    states: list[OccasionState] | None = None
) -> MatchCollection | None:

    # the default period is the active period or the first we can find
    period: BookingPeriod | BookingPeriodMeta | None
    if not period_id:
        period = app.default_period
    else:
        period = BookingPeriodCollection(app.session()).by_id(period_id)

    if not period:
        return None

    return MatchCollection(app.session(), period, states)


@FeriennetApp.path(
    model=BillingCollection,
    path='/billing',
    converters={
        'period_id': UUID,
        'expand': bool,
        'payment_state': LiteralConverter('paid', 'unpaid')
    }
)
def get_billing(
    request: FeriennetRequest,
    app: FeriennetApp,
    period_id: UUID,
    username: str | None = None,
    expand: bool = False,
    state: Literal['paid', 'unpaid'] = 'unpaid'
) -> BillingCollection | None:

    # the default period is the active period or the first we can find
    period: BookingPeriod | BookingPeriodMeta | None
    if not period_id:
        period = app.default_period
    else:
        period = BookingPeriodCollection(app.session()).by_id(period_id)

    if not period:
        return None

    return BillingCollection(request, period, username, expand, state)


@FeriennetApp.path(
    model=InvoiceAction,
    path='/invoice-action/{id}/{action}',
    converters={
        'id': UUID,
        'action': LiteralConverter(
            'mark-paid',
            'mark-unpaid',
            'remove-manual'
        ),
        'extend_to': LiteralConverter('invoice', 'family')
    })
def get_invoice_action(
    request: InvoiceAction,
    app: FeriennetApp,
    id: UUID,
    action: Literal['mark-paid', 'mark-unpaid', 'remove-manual'],
    extend_to: Literal['invoice', 'family'] | None = None
) -> InvoiceAction | None:

    action_obj = InvoiceAction(
        session=app.session(),
        id=id,
        action=action,
        extend_to=extend_to
    )
    return action_obj if action_obj.valid else None


@FeriennetApp.path(
    model=BookingPeriodInvoiceCollection,
    path='/my-bills',
    converters={'invoice': UUID})
def get_my_invoices(
    request: FeriennetRequest,
    app: FeriennetApp,
    username: str | None = None,
    invoice: UUID | None = None
) -> BookingPeriodInvoiceCollection | None:

    # only admins can actually specify the username/invoice
    if not request.is_admin:
        username, invoice = None, None

    # the default username is the current user
    if not username:
        username = request.current_username

    # the default period is the active period
    if not invoice and request.app.default_period:
        invoice = request.app.default_period.id

    user_id = request.app.user_ids_by_name.get(username)

    # the invoice has to exist
    if not invoice:
        return None

    # XXX username should be user_id, invoice should be period_id
    # this should be changed, but needs to be changed by replacing
    # the username everywhere
    return app.invoice_collection(period_id=invoice, user_id=user_id)


@FeriennetApp.path(
    model=ActivityInvoiceItem,
    path='/invoice-item/{id}',
    converters={'id': UUID})
def get_my_invoice_item(
    request: FeriennetRequest,
    id: UUID
) -> ActivityInvoiceItem | None:
    return request.session.query(ActivityInvoiceItem).filter_by(id=id).first()


@FeriennetApp.path(
    model=OccasionAttendeeCollection,
    path='/attendees/{activity_name}',
    converters={'period_id': UUID})
def get_occasion_attendee_collection(
    request: FeriennetRequest,
    app: FeriennetApp,
    activity_name: str,
    period_id: UUID | None = None
) -> OccasionAttendeeCollection | None:

    # load the activity
    activity = get_vacation_activity(request, activity_name)

    if not activity:
        return None

    # the default period is the active period or the first we can find
    period: BookingPeriod | BookingPeriodMeta | None
    if not period_id:
        period = app.default_period
    else:
        period = BookingPeriodCollection(app.session()).by_id(period_id)

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
def get_notification_template_collection(
    app: FeriennetApp
) -> NotificationTemplateCollection:
    return NotificationTemplateCollection(app.session())


@FeriennetApp.path(
    model=NotificationTemplate,
    path='/notification/{id}',
    converters={'id': UUID, 'period_id': UUID})
def get_notification_template(
    app: FeriennetApp,
    id: UUID,
    period_id: UUID | None
) -> NotificationTemplate | None:

    template = NotificationTemplateCollection(app.session()).by_id(id)

    if not period_id and not app.active_period:
        return None

    if template:
        if not period_id:
            assert app.active_period is not None
            period_id = app.active_period.id
        template.period_id = period_id

    return template


@FeriennetApp.path(
    model=Calendar,
    path='/calendar/{name}/{token}')
def get_calendar(
    request: FeriennetRequest,
    name: str,
    token: str
) -> Calendar | None:
    return Calendar.from_name_and_token(request.session, name, token)


@FeriennetApp.path(
    model=GroupInvite,
    path='/join/{group_code}')
def get_group_invite(
    request: FeriennetRequest,
    group_code: str,
    username: str | None = None
) -> GroupInvite | None:

    group_code = group_code.upper()

    if not is_valid_group_code(group_code):
        return None

    if not request.is_admin or not username:
        username = request.current_username

    invite = GroupInvite(request.session, group_code, username)
    return invite.exists and invite or None


@FeriennetApp.path(
    model=OccasionNeed,
    path='/occasion-need/{id}',
    converters={'id': UUID})
def get_occasion_need(
    request: FeriennetRequest,
    id: UUID
) -> OccasionNeed | None:
    return request.session.query(OccasionNeed).filter_by(id=id).first()


@FeriennetApp.path(
    model=VolunteerCart,
    path='/volunteer-cart')
def get_volunteer_cart(request: FeriennetRequest) -> VolunteerCart:
    return VolunteerCart.from_request(request)


@FeriennetApp.path(
    model=VolunteerCartAction,
    path='/volunteer-cart-action/{action}/{target}',
    converters={'action': LiteralConverter('add', 'remove'), 'target': UUID})
def get_volunteer_cart_action(
    request: FeriennetRequest,
    action: Literal['add', 'remove'],
    target: UUID
) -> VolunteerCartAction:
    return VolunteerCartAction(action, target)


@FeriennetApp.path(
    model=VolunteerCollection,
    path='/volunteers/{period_id}',
    converters={'period_id': UUID})
def get_volunteers(
    request: FeriennetRequest,
    period_id: UUID
) -> VolunteerCollection | None:

    if not period_id:
        return None

    if not request.app.show_volunteers(request):
        return None

    period = request.app.periods_by_id.get(period_id.hex)

    if not period:
        return None

    return VolunteerCollection(request.session, period)


@FeriennetApp.path(
    model=Volunteer,
    path='/volunteer/{id}',
    converters={'id': UUID})
def get_volunteer(request: FeriennetRequest, id: UUID) -> Volunteer | None:
    return VolunteerCollection(request.session, None).by_id(id)
