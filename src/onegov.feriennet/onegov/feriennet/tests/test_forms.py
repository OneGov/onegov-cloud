import transaction

from datetime import datetime, timedelta, date
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
from onegov.core.utils import Bunch
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.forms import NotificationTemplateSendForm
from onegov.feriennet.forms import VacationActivityForm
from onegov.user import UserCollection


def test_vacation_activity_form(session, test_password):
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
    form.request = Bunch(
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


def test_notification_template_send_form(session):
    activities = ActivityCollection(session, type='vacation')
    attendees = AttendeeCollection(session)
    periods = PeriodCollection(session)
    occasions = OccasionCollection(session)
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

    prebooking = tuple(d.date() for d in (
        datetime.now() - timedelta(days=1),
        datetime.now() + timedelta(days=1)
    ))

    execution = tuple(d.date() for d in (
        datetime.now() + timedelta(days=10),
        datetime.now() + timedelta(days=12)
    ))

    period = periods.add(
        title="Ferienpass 2016",
        prebooking=prebooking,
        execution=execution,
        active=True
    )

    foo = activities.add("Foo", username='admin@example.org')
    foo.propose().accept()

    bar = activities.add("Bar", username='organiser@example.org')
    bar.propose().accept()

    o1 = occasions.add(
        start=datetime(2016, 11, 25, 8),
        end=datetime(2016, 11, 25, 16),
        age=(0, 10),
        spots=(0, 2),
        timezone="Europe/Zurich",
        activity=foo,
        period=period,
    )
    o1.username = admin.username

    o2 = occasions.add(
        start=datetime(2016, 11, 25, 17),
        end=datetime(2016, 11, 25, 20),
        age=(0, 10),
        spots=(0, 2),
        timezone="Europe/Zurich",
        activity=bar,
        period=period,
    )
    o2.username = organiser.username

    a1 = attendees.add(admin, 'Dustin', date(2000, 1, 1), 'male')
    a2 = attendees.add(organiser, 'Mike', date(2000, 1, 1), 'female')

    b1 = bookings.add(admin, a1, o1)
    b1.state = 'accepted'
    b1.cost = 100

    b2 = bookings.add(organiser, a2, o2)
    b2.state = 'accepted'
    b2.cost = 100

    transaction.commit()

    # create a mock request
    def request(admin):
        return Bunch(
            app=Bunch(
                active_period=periods.active()
            ),
            session=session,
            include=lambda *args: None,
            model=None,
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
    form.model = None
    form.request = request(admin=True)

    assert form.has_choices  # we still have choices (like send to users)
    assert not form.occasion.choices

    # once the request is processed, the occasions are added
    form.on_request()

    assert form.has_choices
    assert len(form.occasion.choices) == 2
    assert len(form.send_to.choices) == 7

    # if the period is inactive, there are no occasions
    periods.query().one().active = False
    transaction.commit()

    form = NotificationTemplateSendForm()
    form.model = None
    form.request = request(admin=True)

    form.on_request()
    assert len(form.occasion.choices) == 0

    # if the period is active but not confirmed, there are no recipients
    period = periods.query().one()
    period.active = True
    period.confirmed = False
    transaction.commit()

    form = NotificationTemplateSendForm()
    form.model = None
    form.request = request(admin=True)

    form.on_request()

    occasions = [c[0] for c in form.occasion.choices]

    # with organisers
    assert len(form.recipients_by_occasion(occasions, True)) == 2

    # without
    assert len(form.recipients_by_occasion(occasions, False)) == 0

    # the number of users is indepenedent of the period
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
    parent = admin.username
    bookings.query().filter_by(username=parent).one().state = 'cancelled'
    transaction.commit()

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
    assert len(form.recipients_with_wishes()) == 2
    assert len(form.recipients_with_bookings()) == 0

    # otherwise they count towards the bookings
    period = periods.query().one()
    period.confirmed = True

    transaction.commit()

    form.request = request(admin=True)
    assert len(form.recipients_with_wishes()) == 0
    assert len(form.recipients_with_bookings()) == 2

    # count the active organisers
    form.request = request(admin=True)
    assert len(form.recipients_which_are_active_organisers()) == 2

    # count the users with unpaid bills
    form.request = request(admin=True)
    assert len(form.recipients_with_unpaid_bills()) == 0

    period = periods.query().one()
    billing = BillingCollection(session, period)
    billing.create_invoices()
    transaction.commit()

    form.request = request(admin=True)
    assert len(form.recipients_with_unpaid_bills()) == 1

    # organisers are not counted as active if the occasion has been cancelled
    occasions = OccasionCollection(session)

    occasions.query().first().cancelled = True
    transaction.commit()

    form.request = request(admin=True)
    assert len(form.recipients_which_are_active_organisers()) == 1

    for occasion in occasions.query():
        occasion.cancelled = False

    transaction.commit()

    form.request = request(admin=True)
    assert len(form.recipients_which_are_active_organisers()) == 2
