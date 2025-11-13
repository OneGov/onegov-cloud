from __future__ import annotations

import pytest

from datetime import date, datetime, timedelta, time
from faker import Faker
from functools import cached_property
from onegov.activity import Activity
from onegov.activity import ActivityCollection
from onegov.activity import Attendee
from onegov.activity import AttendeeCollection
from onegov.activity import Booking
from onegov.activity import BookingCollection
from onegov.activity import BookingPeriod
from onegov.activity import BookingPeriodCollection
from onegov.activity import Occasion
from onegov.activity import OccasionDate
from onegov.activity import OccasionNeed
from onegov.activity import OccasionCollection
from onegov.core.utils import module_path, normalize_for_url
from onegov.pay import PaymentProviderCollection
from onegov.user import User
from onegov.user import UserCollection
from psycopg2.extras import NumericRange
from sedate import standardize_date, utcnow
from sqlalchemy import inspect
from tests.shared.scenario import BaseScenario


from typing import overload, Any, Generic, Literal, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from sqlalchemy.orm import Session

    ActivityT = TypeVar('ActivityT', bound=Activity, default=Activity)
else:
    ActivityT = TypeVar('ActivityT', bound=Activity)


class Collections(Generic[ActivityT]):

    @overload
    def __init__(
        self: Collections[Activity],
        session: Session,
        activity_type: Literal['*', 'generic']
    ) -> None: ...

    @overload
    def __init__(self, session: Session, activity_type: str) -> None: ...

    def __init__(self, session: Session, activity_type: str) -> None:
        self.session = session
        self.activity_type = activity_type

    @cached_property
    def activities(self) -> ActivityCollection[ActivityT]:
        return ActivityCollection(self.session, type=self.activity_type)

    @cached_property
    def attendees(self) -> AttendeeCollection:
        return AttendeeCollection(self.session)

    @cached_property
    def bookings(self) -> BookingCollection:
        return BookingCollection(self.session)

    @cached_property
    def users(self) -> UserCollection:
        return UserCollection(self.session)

    @cached_property
    def periods(self) -> BookingPeriodCollection:
        return BookingPeriodCollection(self.session)

    @cached_property
    def occasions(self) -> OccasionCollection:
        return OccasionCollection(self.session)

    @cached_property
    def payment_providers(self) -> PaymentProviderCollection:
        return PaymentProviderCollection(self.session)


class Scenario(BaseScenario, Generic[ActivityT]):
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

    cached_attributes = (
        'activities',
        'attendees',
        'bookings',
        'occasions',
        'periods',
        'users'
    )

    activity_model: type[ActivityT]
    activity_type: str
    activities: list[ActivityT]
    attendees: list[Attendee]
    bookings: list[Booking]
    occasions: list[Occasion]
    needs: list[OccasionNeed]
    periods: list[BookingPeriod]
    users: list[User]

    def __init__(
        self,
        session: Session,
        test_password: str,
        activity_model: type[ActivityT] = Activity  # type: ignore[assignment]
    ) -> None:
        super().__init__(session, test_password)
        self.activity_model = activity_model
        self.activity_type = inspect(activity_model).polymorphic_identity

        self.faker = Faker()

        self.activities = []
        self.attendees = []
        self.bookings = []
        self.occasions = []
        self.needs = []
        self.periods = []
        self.users = []

    @cached_property
    def c(self) -> Collections[ActivityT]:
        """ Returns useful collections, lazy-loaded. """
        return Collections(self.session, self.activity_type or '*')

    @property
    def latest_activity(self) -> ActivityT | None:
        return self.activities and self.activities[-1] or None

    @property
    def latest_booking(self) -> Booking | None:
        return self.bookings and self.bookings[-1] or None

    @property
    def latest_attendee(self) -> Attendee | None:
        return self.attendees and self.attendees[-1] or None

    @property
    def latest_occasion(self) -> Occasion | None:
        return self.occasions and self.occasions[-1] or None

    @property
    def latest_need(self) -> OccasionNeed | None:
        return self.needs and self.needs[-1] or None

    @property
    def latest_period(self) -> BookingPeriod | None:
        return self.periods and self.periods[-1] or None

    @property
    def latest_user(self) -> User | None:
        return self.users and self.users[-1] or None

    @property
    def latest_username(self) -> str | None:
        return self.users and self.users[-1].username or None

    @property
    def default_username(self) -> str:
        return self.latest_username or 'admin@example.org'

    @staticmethod
    def date_offset(offset: int) -> date:
        return (datetime.now() + timedelta(days=offset)).date()

    def add_period(
        self,
        phase: str = 'wishlist',
        **columns: Any
    ) -> BookingPeriod:
        columns.setdefault('title', self.faker.sentence())
        columns.setdefault('active', True)

        if phase == 'wishlist':
            columns.setdefault('prebooking_start', self.date_offset(-1))
            columns.setdefault('prebooking_end', self.date_offset(+1))
            columns.setdefault('execution_start', self.date_offset(+10))
            columns.setdefault('execution_end', self.date_offset(+20))

            columns.setdefault('booking_start', columns['prebooking_end'])
            columns.setdefault('booking_end', columns['execution_start'])
        elif phase == 'booking':
            columns.setdefault('prebooking_start', self.date_offset(-10))
            columns.setdefault('prebooking_end', self.date_offset(-5))
            columns.setdefault('execution_start', self.date_offset(+5))
            columns.setdefault('execution_end', self.date_offset(+10))

            columns.setdefault('booking_start', columns['prebooking_end'])
            columns.setdefault('booking_end', columns['execution_start'])
        else:
            raise NotImplementedError

        period = self.add(BookingPeriod, **columns)
        self.periods.append(period)

        if columns.get('confirmed'):
            period.confirm_and_start_booking_phase()

        return period

    def add_user(
        self,
        complete_profile: bool = True,
        show_contact_data_to_others: bool = False,
        **columns: Any
    ) -> User:
        columns.setdefault('role', 'admin')
        columns.setdefault('username', self.faker.email())

        user = self.add(
            model=User,
            password_hash=self.test_password,
            **columns
        )
        self.users.append(user)

        if complete_profile:
            user.realname = (
                f'{self.faker.first_name()}\u00A0{self.faker.last_name()}')
            user.data = user.data or {}
            user.data['salutation'] = self.faker.random_element(('mr', 'ms'))
            user.data['address'] = self.faker.address()
            user.data['zip_code'] = self.faker.zipcode()
            user.data['place'] = self.faker.city()
            user.data['political_municipality'] = self.faker.city()
            user.data['emergency'] = f'123 456 789 ({self.faker.name()})'
            user.data['show_contact_data_to_others'] = (
                show_contact_data_to_others
            )

        return user

    def add_activity(self, **columns: Any) -> ActivityT:
        columns.setdefault('title', self.faker.sentence())
        columns.setdefault('name', normalize_for_url(columns['title']))
        columns.setdefault('username', self.default_username)
        columns.setdefault('state', 'preview')

        activity = self.add(self.activity_model, **columns)
        self.activities.append(activity)

        return activity

    def add_occasion(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        dates: Sequence[tuple[datetime, datetime]] | None = None,
        **columns: Any
    ) -> Occasion:
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
            assert period is not None
            offset = sum(1 for o in self.occasions if o.period == period)

            dates = ((
                datetime.combine(period.execution_start, time()) + timedelta(
                    hours=offset
                ),
                datetime.combine(period.execution_start, time()) + timedelta(
                    hours=offset + 1
                )
            ),)

        occasion = self.add(model=Occasion, **columns)
        self.occasions.append(occasion)

        for start, end in dates:
            occasion.dates.append(OccasionDate(
                start=standardize_date(start, 'Europe/Zurich'),
                end=standardize_date(end, 'Europe/Zurich'),
                timezone='Europe/Zurich'
            ))

        return occasion

    def add_need(self, **columns: Any) -> OccasionNeed:
        columns.setdefault('occasion', self.latest_occasion)
        columns.setdefault('name', self.faker.name())
        columns.setdefault('number', NumericRange(1, 5))

        need = self.add(model=OccasionNeed, **columns)
        self.needs.append(need)
        return need

    def add_attendee(self, **columns: Any) -> Attendee:
        columns.setdefault('name', self.faker.name())
        columns.setdefault('birth_date', self.faker.date_of_birth(
            minimum_age=0, maximum_age=20
        ))
        columns.setdefault('username', self.default_username)
        columns.setdefault('gender', self.faker.random_element((
            'female', 'male'
        )))

        attendee = self.add(model=Attendee, **columns)
        self.attendees.append(attendee)

        return attendee

    def add_booking(self, **columns: Any) -> Booking:
        columns.setdefault('username', self.default_username)
        columns.setdefault('attendee', self.latest_attendee)
        columns.setdefault('occasion', self.latest_occasion)

        # required by the aggregation performed on the booking
        # (in reality we always create periods, bookings and occasions in
        # separate transactions)
        self.session.flush()
        columns['period_id'] = columns['occasion'].period_id

        booking = self.add(model=Booking, **columns)
        self.bookings.append(booking)

        return booking


@pytest.fixture(scope='function')
def owner(session: Session) -> User:
    return UserCollection(session).add(
        username='owner@example.org',
        password='hunter2',
        role='editor'
    )


@pytest.fixture(scope='function')
def secondary_owner(session: Session) -> User:
    return UserCollection(session).add(
        username='secondary@example.org',
        password='hunter2',
        role='editor'
    )


@pytest.fixture(scope='function')
def member(session: Session) -> User:
    return UserCollection(session).add(
        username='member@example.org',
        password='hunter2',
        role='member'
    )


@pytest.fixture(scope='function')
def collections(session: Session) -> Collections:
    return Collections(session, 'generic')


@pytest.fixture(scope='function')
def prebooking_period(collections: Collections) -> BookingPeriod:
    """ Returns a period which is currently in the prebooking phase. """

    s, e = (
        utcnow().date() - timedelta(days=10),
        utcnow().date() + timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s, e),
        booking=(e + timedelta(days=1), e + timedelta(days=9)),
        execution=(e + timedelta(days=10), e + timedelta(days=20)),
        active=True
    )


@pytest.fixture(scope='function')
def execution_period(collections: Collections) -> BookingPeriod:
    """ Returns a period which is currently in the execution phase. """

    s, e = (
        utcnow().date() - timedelta(days=10),
        utcnow().date() + timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s - timedelta(days=20), s - timedelta(days=10)),
        booking=(s - timedelta(days=9), s - timedelta(days=1)),
        execution=(s, e),
        active=True
    )


@pytest.fixture(scope='function')
def inactive_period(collections: Collections) -> BookingPeriod:
    """ Returns a previously used period """

    s, e = (
        utcnow().date() - timedelta(days=100),
        utcnow().date() - timedelta(days=10)
    )

    return collections.periods.add(
        title="Testperiod",
        prebooking=(s - timedelta(days=20), s - timedelta(days=10)),
        booking=(s - timedelta(days=9), s - timedelta(days=1)),
        execution=(s, e),
        active=False
    )


@pytest.fixture(scope='session')
def postfinance_xml() -> Iterator[str]:
    xml = 'camt.053_P_CH0309000000250090342_380000000_0_2016053100163801.xml'
    xml_path = module_path('tests.onegov.activity', '/fixtures/' + xml)

    with open(xml_path, 'r') as f:
        yield f.read()


@pytest.fixture(scope='session')
def postfinance_qr_xml() -> Iterator[str]:
    xml = 'CAMT053_280324-1.xml'
    xml_path = module_path('tests.onegov.activity', '/fixtures/' + xml)

    with open(xml_path, 'r') as f:
        yield f.read()


@pytest.fixture(scope='function')
def scenario(
    request: pytest.FixtureRequest,
    session: Session,
    test_password: str
) -> Iterator[Scenario]:

    session.add(User(
        username='admin@example.org',
        password_hash=test_password,
        role='admin'
    ))
    session.add(User(
        username='editor@example.org',
        password_hash=test_password,
        role='editor'
    ))

    yield Scenario(session, test_password)
