import transaction

from cached_property import cached_property
from contextlib import contextmanager
from datetime import datetime, timedelta, time
from faker import Faker
from onegov.activity import Activity
from onegov.activity import ActivityCollection
from onegov.activity import AttendeeCollection
from onegov.activity import BookingCollection
from onegov.activity import OccasionCollection
from onegov.activity import PeriodCollection
from onegov.activity.models import Attendee
from onegov.activity.models import Booking
from onegov.activity.models import Occasion
from onegov.activity.models import OccasionDate
from onegov.activity.models import Period
from onegov.core.utils import normalize_for_url
from onegov.pay import PaymentProviderCollection
from onegov.user import UserCollection
from onegov.user.models import User
from sedate import standardize_date
from sqlalchemy import inspect


class Collections(object):

    def __init__(self, session, activity_type):
        self.session = session
        self.activity_type = activity_type

    @cached_property
    def activities(self):
        return ActivityCollection(self.session, type=self.activity_type)

    @cached_property
    def attendees(self):
        return AttendeeCollection(self.session)

    @cached_property
    def bookings(self):
        return BookingCollection(self.session)

    @cached_property
    def users(self):
        return UserCollection(self.session)

    @cached_property
    def periods(self):
        return PeriodCollection(self.session)

    @cached_property
    def occasions(self):
        return OccasionCollection(self.session)

    @cached_property
    def payment_providers(self):
        return PaymentProviderCollection(self.session)


class Scenario(object):
    """ Helper class to ease the setup of testing fixtures for Feriennet.

    Feriennet has often repetitive steps to get to a test scenario. A period
    needs to be added, an activity, an occasion, an attendee and so on.

    This class offers to do this with the twist that it'll use the order in
    which its methods are being called as extra information.

    So if we add an activity and on the next line add an occasion, the occasion
    will automatically be added to the last created activity.

    This is usually something we might want to be explicit about, but for our
    tests this is helps us cut down on the amount of code needed to setup a
    certain scenario, while making it clearer what we are setting up.

    For example:

        scenario.add_period(confirmed=True)
        scenario.add_activity(title="Learn How to Program")
        scenario.add_occasion()
        scenario.add_attendee()
        scenario.add_booking()

    Here we create a period with an activity in it that has an occasion for
    which an attendee has a booking.

    """

    def __init__(self, session, test_password, activity_model=Activity):
        self.session = session
        self.activity_model = activity_model
        self.activity_type = inspect(activity_model).polymorphic_identity
        self.test_password = test_password

        self.faker = Faker()

        self.activities = []
        self.attendees = []
        self.bookings = []
        self.occasions = []
        self.periods = []
        self.users = []

    def __getattribute__(self, name):
        if name.startswith('add_') and not transaction.manager._txn:
            transaction.begin()

        return super().__getattribute__(name)

    def commit(self):
        transaction.commit()

    @contextmanager
    def update(self):
        self.refresh()
        yield
        self.commit()

    def refresh(self):
        transaction.begin()

        caches = (
            'activities',
            'attendees',
            'bookings',
            'occasions',
            'periods',
            'users'
        )

        for name in caches:
            cache = getattr(self, name)

            for ix, item in enumerate(cache):
                cache[ix] = self.session.merge(item)
                self.session.refresh(cache[ix])

    @cached_property
    def c(self):
        """ Returns useful collections, lazy-loaded. """
        return Collections(self.session, self.activity_type or '*')

    @property
    def latest_activity(self):
        return self.activities and self.activities[-1] or None

    @property
    def latest_booking(self):
        return self.bookings and self.bookings[-1] or None

    @property
    def latest_attendee(self):
        return self.attendees and self.attendees[-1] or None

    @property
    def latest_occasion(self):
        return self.occasions and self.occasions[-1] or None

    @property
    def latest_period(self):
        return self.periods and self.periods[-1] or None

    @property
    def latest_user(self):
        return self.users and self.users[-1] or None

    @property
    def latest_username(self):
        return self.users and self.users[-1].username or None

    @property
    def default_username(self):
        return self.latest_username or 'admin@example.org'

    def date_offset(self, offset):
        return (datetime.now() + timedelta(days=offset)).date()

    def add(self, model, **columns):
        obj = model(**columns)
        self.session.add(obj)

        return obj

    def add_period(self, phase='wishlist', **columns):
        columns.setdefault('title', self.faker.sentence())
        columns.setdefault('active', True)

        if phase == 'wishlist':
            columns.setdefault('prebooking_start', self.date_offset(-1))
            columns.setdefault('prebooking_end', self.date_offset(+1))
            columns.setdefault('execution_start', self.date_offset(+10))
            columns.setdefault('execution_end', self.date_offset(+20))
        elif phase == 'booking':
            columns.setdefault('prebooking_start', self.date_offset(-10))
            columns.setdefault('prebooking_end', self.date_offset(-5))
            columns.setdefault('execution_start', self.date_offset(-1))
            columns.setdefault('execution_end', self.date_offset(+1))
        else:
            raise NotImplementedError

        self.periods.append(self.add(Period, **columns))

        return self.latest_period

    def add_user(self, complete_profile=True, **columns):
        columns.setdefault('role', 'admin')
        columns.setdefault('username', self.faker.email())

        self.users.append(self.add(
            model=User,
            password_hash=self.test_password,
            **columns
        ))

        if complete_profile:
            user = self.latest_user
            user.data = user.data or {}
            user.data['salutation'] = self.faker.random_element(('mr', 'ms'))
            user.data['first_name'] = self.faker.first_name()
            user.data['last_name'] = self.faker.last_name()
            user.data['address'] = self.faker.address()
            user.data['zip_code'] = self.faker.zipcode()
            user.data['place'] = self.faker.city()
            user.data['emergency'] = f'123456 ({self.faker.name()})'

        return self.latest_user

    def add_activity(self, **columns):
        columns.setdefault('title', self.faker.sentence())
        columns.setdefault('name', normalize_for_url(columns['title']))
        columns.setdefault('username', self.default_username)
        columns.setdefault('state', 'preview')

        self.activities.append(self.add(self.activity_model, **columns))

        return self.latest_activity

    def add_occasion(self, start=None, end=None, dates=None, **columns):
        assert not (dates and start and end)

        columns.setdefault('period', self.latest_period)
        columns.setdefault('activity', self.latest_activity)
        columns.setdefault('age', (0, 20))
        columns.setdefault('spots', (0, 20))

        for key in ('age', 'spots'):
            columns[key] = OccasionCollection.to_half_open_interval(
                *columns[key])

        if not dates and (start and end):
            dates = ((start, end), )

        if not dates:
            period = self.latest_period
            offset = sum(1 for o in self.occasions if o.period == period)

            dates = ((
                datetime.combine(period.execution_start, time()) + timedelta(
                    hours=offset
                ),
                datetime.combine(period.execution_start, time()) + timedelta(
                    hours=offset + 1
                )
            ),)

        self.occasions.append(self.add(model=Occasion, **columns))

        for start, end in dates:
            self.latest_occasion.dates.append(OccasionDate(
                start=standardize_date(start, 'Europe/Zurich'),
                end=standardize_date(end, 'Europe/Zurich'),
                timezone='Europe/Zurich'
            ))

        return self.latest_occasion

    def add_attendee(self, **columns):
        columns.setdefault('name', self.faker.name())
        columns.setdefault('birth_date', self.faker.date_of_birth())
        columns.setdefault('username', self.default_username)
        columns.setdefault('gender', self.faker.random_element((
            'female', 'male'
        )))

        self.attendees.append(self.add(model=Attendee, **columns))

        return self.latest_attendee

    def add_booking(self, **columns):
        columns.setdefault('username', self.default_username)
        columns.setdefault('attendee', self.latest_attendee)
        columns.setdefault('occasion', self.latest_occasion)

        # required by the aggregation performed on the booking
        # (in reality we always create periods, bookings and occasions in
        # separate transactions)
        self.session.flush()
        columns['period_id'] = columns['occasion'].period_id

        self.bookings.append(self.add(model=Booking, **columns))

        return self.latest_booking
