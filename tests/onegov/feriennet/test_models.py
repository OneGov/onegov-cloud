from __future__ import annotations

from markupsafe import Markup
from sedate import utcnow
from datetime import date, timedelta
from freezegun import freeze_time
from uuid import uuid4

from onegov.core.utils import Bunch
from onegov.feriennet.models.notification_template import TemplateVariables

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Scenario


def test_template_variables() -> None:

    class MockRequest:

        def __repr__(self) -> str:
            return 'MockRequest'

        def translate(self, text: str) -> str:
            return text.upper()

        def link(self, obj: object, *args: object, **kwargs: object) -> str:
            return repr(obj)

        def class_link(
            self,
            cls: type[object],
            *args: object,
            **kwargs: object
        ) -> str:
            return cls.__name__

        @property
        def app(self) -> Any:
            return Bunch(org=self)

    class MockPeriod:
        id = uuid4()
        title = 'Foobar Pass'

    t = TemplateVariables(MockRequest(), MockPeriod())  # type: ignore[arg-type]

    assert sorted(t.bound.keys()) == [
        "[ACTIVITIES]",
        "[BOOKINGS]",
        "[HOMEPAGE]",
        "[INVOICES]",
        "[PERIOD]",
    ]

    assert t.render("Welcome to [PERIOD]") == "Welcome to Foobar Pass"  # type: ignore[arg-type]
    assert t.render("Go to [INVOICES]") == (  # type: ignore[arg-type]
        'Go to <a href="BookingPeriodInvoiceCollection">INVOICES</a>')
    assert t.render("Go to [BOOKINGS]") == (  # type: ignore[arg-type]
        'Go to <a href="BookingCollection">BOOKINGS</a>')
    assert t.render("Go to [ACTIVITIES]") == (  # type: ignore[arg-type]
        'Go to <a href="VacationActivityCollection">ACTIVITIES</a>')
    assert t.render("Go to [HOMEPAGE]") == (  # type: ignore[arg-type]
        'Go to <a href="MockRequest">HOMEPAGE</a>')


def test_period(scenario: Scenario) -> None:
    scenario.add_period()
    scenario.commit()
    scenario.refresh()

    period = scenario.latest_period
    assert period is not None
    prebook = period.prebooking_start
    prebook_end = period.prebooking_end
    local_ = period.as_local_datetime
    midnight = local_(prebook)

    with freeze_time(midnight):
        # We can see that the timezone already comes to play here leading
        # to a bug that cost one persons sleep
        assert local_(date.today()) != midnight
        # so we replaced it with utcnow() to fix the error
        assert utcnow() == midnight
        assert period.phase == 'wishlist'
        assert period.is_currently_prebooking

    with freeze_time(midnight - timedelta(minutes=1)):
        period = period  # undo mypy narrowing
        assert period.phase == 'inactive'
        assert not period.wishlist_phase
        assert not period.is_currently_prebooking

    with freeze_time(local_(prebook_end) + timedelta(hours=23, minutes=59)):
        period = period  # undo mypy narrowing
        assert period.phase == 'wishlist'
        assert period.wishlist_phase
        assert period.is_currently_prebooking
        assert not period.is_prebooking_in_past

    with freeze_time(local_(prebook_end) + timedelta(days=1)):
        period = period  # undo mypy narrowing
        assert not period.is_currently_prebooking
        assert period.is_prebooking_in_past

    # exactly midnight in the chosen timezone
    with freeze_time(local_(prebook_end)):
        period = period  # undo mypy narrowing
        assert period.wishlist_phase
        assert period.is_currently_prebooking
        assert not period.is_prebooking_in_past


def test_add_vacation_activity(scenario: Scenario) -> None:

    owner = scenario.add_user(
        username='maxi@example.org',
        realname=None,
        phone='041 312 4567',
        complete_profile=False,
    )

    activity = scenario.add_activity(
        title='Visit the Donut Shop',
        username=owner.username,
        lead='Come visit the local donut shop and get some samples!',
        text=Markup('<h1>Attack of the Killer Donuts</h1>'),
        tags={'donut', 'killer', 'yummy', 'delicious'},
        user=owner,
    )

    assert activity.title == 'Visit the Donut Shop'
    assert (
        activity.lead
        == 'Come visit the local donut shop and get some samples!'
    )
    assert activity.text == Markup('<h1>Attack of the Killer Donuts</h1>')
    assert activity.username == owner.username

    assert activity.organiser == ['maxi@example.org', '041 312 4567']
    assert activity.organiser_text == 'maxi@example.org 041 312 4567'

    # set user realname and data
    owner.realname = 'Max'
    owner.data = {
        'organisation': 'Donut Lovers Inc.',
        'place': 'Donut City',
        'zip_code': '12345',
    }

    assert activity.organiser == [
        'maxi@example.org',
        'Max',
        'Donut Lovers Inc.',
        '12345',
        'Donut City',
    ]
    assert (
        activity.organiser_text
        == 'maxi@example.org Max Donut Lovers Inc. 12345 Donut City'
    )
