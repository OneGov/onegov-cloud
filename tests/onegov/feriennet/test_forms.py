from __future__ import annotations

import pytest
import transaction

from datetime import datetime, timedelta, date
from decimal import Decimal
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import BookingPeriodCollection
from onegov.activity import BookingPeriodInvoiceCollection
from onegov.activity import OccasionCollection
from onegov.core.utils import Bunch
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.forms import NotificationTemplateSendForm, PeriodForm
from onegov.feriennet.forms import VacationActivityForm
from onegov.user import UserCollection
from webob.multidict import MultiDict


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity import BookingPeriod
    from onegov.feriennet.models import VacationActivity
    from sqlalchemy.orm import Session
    from uuid import UUID
    from .conftest import Scenario


def create_form(
    session: Session,
    confirmable: bool,
    start: date,
    delta: timedelta | None = None
) -> PeriodForm:

    delta = delta or timedelta(days=10)
    fmt = "%Y-%m-%d"
    start_ = start

    def iter_start() -> str:
        nonlocal start_
        start_ += delta
        return start_.strftime(fmt)

    form = PeriodForm(MultiDict([
        ('title', 'My Period'),
        ('confirmable', confirmable),
        ('finalizable', False),
        ('prebooking_start', start.strftime(fmt)),
        ('prebooking_end', iter_start()),
        ('booking_start', iter_start()),
        ('booking_end', iter_start()),
        ('execution_start', iter_start()),
        ('execution_end', iter_start())
    ]))
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)  # type: ignore[assignment]
    form.model = BookingPeriodCollection(session)
    return form


def add_period_by_form(form: PeriodForm, session: Session) -> BookingPeriod:
    # add the period like in view name='new'
    return BookingPeriodCollection(session).add(
        title=form.title.data,  # type: ignore[arg-type]
        prebooking=form.prebooking,
        booking=form.booking,  # type: ignore[arg-type]
        execution=form.execution,  # type: ignore[arg-type]
        minutes_between=form.minutes_between.data,
        confirmable=form.confirmable.data,
        finalizable=form.finalizable.data,
        active=False
    )


def edit_period_by_form(form: PeriodForm, period: BookingPeriod) -> None:
    # simulated the edit view
    form.model = period


@pytest.mark.parametrize('confirmable,start, delta', [
    (True, date(2020, 4, 1), timedelta(days=10)),
    (False, date(2020, 4, 1), timedelta(days=10)),
])
def test_period_form(
    session: Session,
    confirmable: bool,
    start: date,
    delta: timedelta
) -> None:

    # Fixes issue FER-861
    booking_start = start + 2 * delta

    form = create_form(session, confirmable, start, delta)
    assert form.confirmable.data is confirmable

    assert form.booking_start.data == booking_start
    assert form.validate()
    assert form.booking_start.data == booking_start

    period = add_period_by_form(form, session)

    if not confirmable:
        # The prebooking fields are hidden in the ui, but the user still could
        # have filled in some dates, so check if the are resetted
        assert form.prebooking == (None, None)
        assert period.prebooking_end == booking_start
        assert period.prebooking_start == booking_start

    # Generate form from model and simulate get request
    form.model = period
    assert not form.is_new
    form.process(obj=period)
    assert form.prebooking_start.data == start if confirmable \
        else booking_start

    # Start earlier, no intersections
    new_booking_start = form.booking_start.data
    form.validate()
    assert not form.errors
    if not confirmable:
        assert form.prebooking_start.data == new_booking_start
        assert form.prebooking_end.data == new_booking_start
    form.populate_obj(period)
    session.flush()

    # Start earlier, adjust prebooking
    new_booking_start = start - timedelta(days=100)
    form.booking_start.data = new_booking_start
    validated = form.validate()
    if confirmable:
        assert form.errors
        return

    assert validated
    assert form.prebooking_start.data == new_booking_start
    assert form.prebooking_end.data == new_booking_start
    form.populate_obj(period)
    session.flush()
    assert period.prebooking_start == new_booking_start
    assert period.prebooking_end == new_booking_start


def test_vacation_activity_form(session: Session, test_password: str) -> None:
    users = UserCollection(session)
    users.add(
        username='admin@example.org',
        realname='Robert Baratheon',
        password='foobar',
        role='admin')
    users.add(
        username='editor@example.org',
        realname=None,
        password='foobar',
        role='editor')
    users.add(
        username='member@example.org',
        realname=None,
        password='foobar',
        role='member')

    form = VacationActivityForm()
    form.request = Bunch(  # type: ignore[assignment]
        is_admin=True,
        current_username='editor@example.org',
        session=session
    )

    form.on_request()

    assert form.username.data == 'editor@example.org'
    assert form.username.choices == [
        ('editor@example.org', 'editor@example.org'),
        ('admin@example.org', 'Robert Baratheon')
    ]

    form.request.is_admin = False
    form.on_request()

    assert form.username is None


def test_notification_template_send_form(session: Session) -> None:
    activities: ActivityCollection[VacationActivity]
    activities = ActivityCollection(session, type='vacation')
    attendees = AttendeeCollection(session)
    periods = BookingPeriodCollection(session)
    occasions_ = OccasionCollection(session)
    bookings = BookingCollection(session)

    users = UserCollection(session)
    admin = users.add(
        username='admin@example.org',
        realname='Robert Baratheon',
        password='foobar',
        role='admin')
    organiser = users.add(
        username='organiser@example.org',
        realname=None,
        password='foobar',
        role='editor')
    users.add(
        username='member@example.org',
        realname=None,
        password='foobar',
        role='member')

    prebooking = (
        (datetime.now() - timedelta(days=1)).date(),
        (datetime.now() + timedelta(days=1)).date()
    )

    execution = (
        (datetime.now() + timedelta(days=10)).date(),
        (datetime.now() + timedelta(days=12)).date()
    )

    period = periods.add(
        title="Ferienpass 2016",
        prebooking=prebooking,
        booking=(prebooking[1], execution[0]),
        execution=execution,
        active=True
    )

    foo = activities.add("Foo", username='admin@example.org')
    foo.propose().accept()

    bar = activities.add("Bar", username='organiser@example.org')
    bar.propose().accept()

    o1 = occasions_.add(
        start=datetime(2016, 11, 25, 8),
        end=datetime(2016, 11, 25, 16),
        age=(0, 10),
        spots=(0, 2),
        timezone="Europe/Zurich",
        activity=foo,
        period=period,
    )
    o1.username = admin.username  # type: ignore[attr-defined]

    o2 = occasions_.add(
        start=datetime(2016, 11, 25, 17),
        end=datetime(2016, 11, 25, 20),
        age=(0, 10),
        spots=(0, 2),
        timezone="Europe/Zurich",
        activity=bar,
        period=period,
    )
    o2.username = organiser.username  # type: ignore[attr-defined]

    a1 = attendees.add(admin, 'Dustin', date(2000, 1, 1), 'male')
    a2 = attendees.add(organiser, 'Mike', date(2000, 1, 1), 'female')

    b1 = bookings.add(admin, a1, o1)
    b1.state = 'accepted'
    b1.cost = Decimal('100')

    b2 = bookings.add(organiser, a2, o2)
    b2.state = 'accepted'
    b2.cost = Decimal('100')

    transaction.commit()

    # create a mock request
    def invoice_collection(
        user_id: UUID | None = None,
        period_id: UUID | None = None
    ) -> BookingPeriodInvoiceCollection:
        return BookingPeriodInvoiceCollection(
            session,
            user_id=user_id,
            period_id=period_id
        )

    def request(admin: bool) -> Any:
        return Bunch(
            app=Bunch(
                active_period=periods.active(),
                org=Bunch(
                    geo_provider='geo-mapbox',
                    open_files_target_blank=True
                ),
                invoice_collection=invoice_collection,
                periods=periods.query().all(),
                schema='',
                websockets_private_channel='',
                websockets_client_url=lambda *args: '',
                version='1.0',
                sentry_dsn=None
            ),
            session=session,
            include=lambda *args: None,
            model=Bunch(period_id=period.id),
            is_admin=admin,
            is_organiser_only=not admin and True or False,
            is_manager=admin and True or False,
            translate=lambda text, *args, **kwargs: text,
            locale='de_CH',
            current_username=(
                admin and 'admin@example.org' or 'organiser@example.org'
            )
        )

    # in the beginning there are no recipients
    form = NotificationTemplateSendForm()
    form.model = Bunch(period_id=period.id)
    form.request = request(admin=True)

    assert form.has_choices  # we still have choices (like send to users)
    assert not form.occasion.choices

    # once the request is processed, the occasions are added
    form.on_request()

    assert form.has_choices
    assert len(form.occasion.choices) == 2
    assert len(form.send_to.choices) == 7

    # if the period is not confirmed, we send to attendees wanting the occasion
    periods.query().one().confirmed = False
    bookings.query().filter_by(
        username=admin.username).one().state = 'denied'
    transaction.commit()

    form = NotificationTemplateSendForm()
    form.model = Bunch(period_id=period.id)
    form.request = request(admin=True)

    form.on_request()
    assert len(form.occasion.choices) == 2

    occasions = [c[0] for c in form.occasion.choices]
    assert len(form.recipients_by_occasion(occasions, False)) == 2
    assert len(form.recipients_by_occasion(occasions, True)) == 2

    # if the period is confirmed, we send to attendees with accepted bookings
    periods.query().one().confirmed = True
    transaction.commit()

    form = NotificationTemplateSendForm()
    form.model = Bunch(period_id=period.id)
    form.request = request(admin=True)

    form.on_request()
    assert len(form.occasion.choices) == 2

    occasions = [c[0] for c in form.occasion.choices]
    assert len(form.recipients_by_occasion(occasions, False)) == 1
    assert len(form.recipients_by_occasion(occasions, True)) == 2

    # the number of users is independent of the period
    assert len(form.recipients_by_role(('admin', 'editor', 'member'))) == 3
    assert len(form.recipients_by_role(('admin', 'editor'))) == 2
    assert len(form.recipients_by_role(('admin',))) == 1

    # if the period is confirmed, there are accepted recipients
    period = periods.query().one()
    period.active = True
    period.confirmed = True

    transaction.commit()
    assert len(form.recipients_by_occasion(occasions)) == 2

    # only accepted bookings are counted
    bookings.query().filter_by(
        username=admin.username).one().state = 'cancelled'
    transaction.commit()

    occasions = [c[0] for c in form.occasion.choices]

    # without organisers
    assert len(form.recipients_by_occasion(occasions, False)) == 1

    # with
    assert len(form.recipients_by_occasion(occasions, True)) == 2

    # inactive users may be exluded
    form.state.data = ['active']
    assert len(form.recipients_pool) == 3

    form.state.data = ['active', 'inactive']
    assert len(form.recipients_pool) == 3

    form.state.data = ['inactive']
    assert len(form.recipients_pool) == 0

    # bookings count towards the wishlist if the period is active,
    period = periods.query().one()
    period.active = True
    period.confirmed = False

    transaction.commit()
    form.request = request(admin=True)

    # do not count cancelled bookings...
    form.__dict__['period'] = period
    assert len(form.recipients_with_wishes()) == 2
    assert len(form.recipients_with_accepted_bookings()) == 0

    # otherwise they count towards the bookings
    period = periods.query().one()
    period.confirmed = True

    transaction.commit()

    form.request = request(admin=True)
    form.__dict__['period'] = period
    assert len(form.recipients_with_wishes()) == 0
    assert len(form.recipients_with_accepted_bookings()) == 1

    # count the active organisers
    form.request = request(admin=True)
    assert len(form.recipients_which_are_active_organisers()) == 2

    # count the users with unpaid bills
    form.request = request(admin=True)
    assert len(form.recipients_with_unpaid_bills()) == 0

    period = periods.query().one()
    billing = BillingCollection(request=Bunch(  # type: ignore[arg-type]
        session=session,
        app=Bunch(invoice_collection=invoice_collection)
    ), period=period)
    billing.create_invoices()
    transaction.commit()

    form.request = request(admin=True)
    assert len(form.recipients_with_unpaid_bills()) == 1

    # organisers are not counted as active if the occasion has been cancelled
    occasions_ = OccasionCollection(session)

    occasions_.query().first().cancelled = True  # type: ignore[union-attr]
    transaction.commit()

    form.request = request(admin=True)
    assert len(form.recipients_which_are_active_organisers()) == 1

    for occasion in occasions_.query():
        occasion.cancelled = False

    transaction.commit()

    form.request = request(admin=True)
    assert len(form.recipients_which_are_active_organisers()) == 2


@pytest.mark.parametrize('recipient_count,roles,states', [
    (2, ['admin', 'editor'], ['active']),
    (4, ['admin', 'editor'], ['active', 'inactive']),
    (1, ['editor'], ['inactive']),
])
def test_notification_send_template_by_role(
    scenario: Scenario,
    recipient_count: int,
    roles: list[str],
    states: list[str]
) -> None:
    # Check by_role with inactive users
    # in the beginning there are no recipients

    session = scenario.session

    users = UserCollection(session)
    # add each role active and not active
    for username in (
            'admin@example.org',
            'editor@example.org',
    ):
        role = username.split('@')[0]
        users.add(username=username, password='foobar', role=role)
        users.add(username=f'ex_{username}', password='foobar', role=role,
                  active=False)

    scenario.add_period()
    scenario.commit()
    scenario.refresh()
    period = scenario.latest_period
    assert period is not None

    form = NotificationTemplateSendForm(MultiDict([
        ('send_to', 'by_role'),
        *(('roles', role) for role in roles),
        *(('state', s) for s in states)
    ]))
    assert form.send_to.data == 'by_role'
    assert form.roles.data == roles
    assert form.state.data == states

    form.request = Bunch(session=session)  # type: ignore[assignment]
    form.model = Bunch(period_id=period.id)
    assert len(form.recipients) == recipient_count
