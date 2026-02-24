from __future__ import annotations

import os
import pytest

from datetime import date, datetime, time, timedelta
from dateutil.rrule import MO, WE
from onegov.core.utils import Bunch
from onegov.directory.collections.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.event import Event
from onegov.form import FormDefinition
from onegov.org.forms import DaypassAllocationForm
from onegov.org.forms import EventForm
from onegov.org.forms import FindYourSpotForm
from onegov.org.forms import FormRegistrationWindowForm
from onegov.org.forms import ManageUserGroupForm
from onegov.org.forms import RoomAllocationEditForm
from onegov.org.forms import RoomAllocationForm
from onegov.org.forms import TicketAssignmentForm
from onegov.org.forms.allocation import AllocationFormHelpers
from onegov.org.forms.settings import OrgTicketSettingsForm
from onegov.reservation import LibresIntegration
from onegov.ticket import Ticket, TicketPermission
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from unittest.mock import MagicMock
from uuid import UUID
from webob.multidict import MultiDict


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm import SessionManager
    from onegov.form import Form
    from onegov.org.models import ExtendedDirectory
    from sqlalchemy.orm import Session
    from .conftest import Client, TestOrgApp


@pytest.mark.parametrize('form_class', [
    DaypassAllocationForm,
    RoomAllocationForm
])
def test_allocation_form_dates(form_class: type[Form]) -> None:
    """ Makes sure all required methods are implemented. """
    form = form_class()

    # those are customizable
    assert hasattr(form, 'dates')
    assert hasattr(form, 'whole_day')
    assert hasattr(form, 'quota')
    assert hasattr(form, 'quota_limit')
    assert hasattr(form, 'data')
    assert hasattr(form, 'partly_available')

    # those are not (yet) customizable in onegov.org
    assert not hasattr(form, 'grouped')
    assert not hasattr(form, 'raster')
    assert not hasattr(form, 'approve_manually')


def test_daypass_single_date() -> None:
    form = DaypassAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'daypasses': 4,
        'daypasses_limit': 1
    })

    assert form.dates == [(datetime(2015, 8, 4), datetime(2015, 8, 4))]
    assert form.whole_day == True
    assert form.quota == 4
    assert form.quota_limit == 1
    assert form.data == {
        'access': 'public',
        'pricing_method': 'inherit',
        'price_per_hour': 0.0,
        'price_per_item': 0.0,
        'currency': 'CHF',
    }


def test_daypass_multiple_dates() -> None:
    form = DaypassAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 8),
    })

    assert form.dates == [
        (datetime(2015, 8, 4), datetime(2015, 8, 4)),
        (datetime(2015, 8, 5), datetime(2015, 8, 5)),
        (datetime(2015, 8, 6), datetime(2015, 8, 6)),
        (datetime(2015, 8, 7), datetime(2015, 8, 7)),
        (datetime(2015, 8, 8), datetime(2015, 8, 8)),
    ]


def test_daypass_except_for() -> None:
    form = DaypassAllocationForm(data={
        'start': datetime(2015, 8, 3),
        'end': datetime(2015, 8, 6),
        'except_for': [MO.weekday, WE.weekday]
    })

    assert form.dates == [
        (datetime(2015, 8, 4), datetime(2015, 8, 4)),
        (datetime(2015, 8, 6), datetime(2015, 8, 6)),
    ]


def test_room_single_date() -> None:
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'start_time': time(12, 00),
        'end_time': time(16, 00),
        'as_whole_day': 'no'
    })

    assert form.dates == [(datetime(2015, 8, 4, 12), datetime(2015, 8, 4, 16))]
    assert form.whole_day == False
    assert form.quota == 1
    assert form.quota_limit == 1
    assert form.data == {
        'access': 'public',
        'pricing_method': 'inherit',
        'price_per_hour': 0.0,
        'price_per_item': 0.0,
        'currency': 'CHF',
    }


def test_room_whole_day() -> None:
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'as_whole_day': 'yes'
    })

    assert form.dates == [(datetime(2015, 8, 4), datetime(2015, 8, 4))]
    assert form.whole_day == True
    assert form.quota == 1
    assert form.quota_limit == 1
    assert form.data == {
        'access': 'public',
        'pricing_method': 'inherit',
        'price_per_hour': 0.0,
        'price_per_item': 0.0,
        'currency': 'CHF',
    }


def test_room_access() -> None:
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'as_whole_day': 'yes',
        'access': 'private'
    })

    assert form.dates == [(datetime(2015, 8, 4), datetime(2015, 8, 4))]
    assert form.whole_day == True
    assert form.quota == 1
    assert form.quota_limit == 1
    assert form.data == {
        'access': 'private',
        'pricing_method': 'inherit',
        'price_per_hour': 0.0,
        'price_per_item': 0.0,
        'currency': 'CHF',
    }


def test_room_pricing_method_free() -> None:
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'as_whole_day': 'yes',
        'pricing_method': 'free'
    })

    assert form.dates == [(datetime(2015, 8, 4), datetime(2015, 8, 4))]
    assert form.whole_day == True
    assert form.quota == 1
    assert form.quota_limit == 1
    assert form.data == {
        'access': 'public',
        'pricing_method': 'free',
        'price_per_hour': 0.0,
        'price_per_item': 0.0,
        'currency': 'CHF',
    }


def test_room_pricing_method_per_hour() -> None:
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'as_whole_day': 'yes',
        'pricing_method': 'per_hour',
        'price_per_hour': 30.0,
        'currency': 'USD'
    })

    assert form.dates == [(datetime(2015, 8, 4), datetime(2015, 8, 4))]
    assert form.whole_day == True
    assert form.quota == 1
    assert form.quota_limit == 1
    assert form.data == {
        'access': 'public',
        'pricing_method': 'per_hour',
        'price_per_hour': 30.0,
        'price_per_item': 0.0,
        'currency': 'USD',
    }


def test_room_pricing_method_per_item() -> None:
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'as_whole_day': 'yes',
        'pricing_method': 'per_item',
        'price_per_item': 50.0,
        'currency': 'USD'
    })

    assert form.dates == [(datetime(2015, 8, 4), datetime(2015, 8, 4))]
    assert form.whole_day == True
    assert form.quota == 1
    assert form.quota_limit == 1
    assert form.data == {
        'access': 'public',
        'pricing_method': 'per_item',
        'price_per_hour': 0.0,
        'price_per_item': 50.0,
        'currency': 'USD',
    }


def test_room_multiple_dates() -> None:
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 8),
        'start_time': time(12, 00),
        'end_time': time(16, 00)
    })

    assert form.dates == [
        (datetime(2015, 8, 4, 12), datetime(2015, 8, 4, 16)),
        (datetime(2015, 8, 5, 12), datetime(2015, 8, 5, 16)),
        (datetime(2015, 8, 6, 12), datetime(2015, 8, 6, 16)),
        (datetime(2015, 8, 7, 12), datetime(2015, 8, 7, 16)),
        (datetime(2015, 8, 8, 12), datetime(2015, 8, 8, 16)),
    ]


def test_room_except_for() -> None:
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 3),
        'end': date(2015, 8, 6),
        'start_time': time(12, 00),
        'end_time': time(16, 00),
        'except_for': [MO.weekday, WE.weekday]
    })

    assert form.dates == [
        (datetime(2015, 8, 4, 12), datetime(2015, 8, 4, 16)),
        (datetime(2015, 8, 6, 12), datetime(2015, 8, 6, 16)),
    ]


def test_generate_dates() -> None:
    helper = AllocationFormHelpers()

    assert helper.generate_dates(date(2015, 1, 1), date(2015, 1, 1)) == [
        (datetime(2015, 1, 1), datetime(2015, 1, 1))
    ]

    assert helper.generate_dates(date(2015, 1, 1), date(2015, 1, 2)) == [
        (datetime(2015, 1, 1), datetime(2015, 1, 1)),
        (datetime(2015, 1, 2), datetime(2015, 1, 2)),
    ]

    assert helper.generate_dates(
        date(2015, 1, 4), date(2015, 1, 10), weekdays=[0, 1, 2]) == [
            (datetime(2015, 1, 5), datetime(2015, 1, 5)),
            (datetime(2015, 1, 6), datetime(2015, 1, 6)),
            (datetime(2015, 1, 7), datetime(2015, 1, 7)),
    ]

    assert helper.generate_dates(date(2016, 3, 26), date(2016, 3, 28)) == [
        (datetime(2016, 3, 26), datetime(2016, 3, 26)),
        (datetime(2016, 3, 27), datetime(2016, 3, 27)),
        (datetime(2016, 3, 28), datetime(2016, 3, 28)),
    ]


def test_generate_datetimes() -> None:
    helper = AllocationFormHelpers()

    assert helper.generate_dates(
        date(2015, 1, 1), date(2015, 1, 1), time(12, 0), time(16, 0)) == [
            (datetime(2015, 1, 1, 12), datetime(2015, 1, 1, 16))
    ]

    assert helper.generate_dates(
        date(2015, 1, 1), date(2015, 1, 2), time(12, 0), time(16, 0)) == [
            (datetime(2015, 1, 1, 12), datetime(2015, 1, 1, 16)),
            (datetime(2015, 1, 2, 12), datetime(2015, 1, 2, 16))
    ]

    assert helper.generate_dates(
        date(2015, 1, 4), date(2015, 1, 10),
        time(12, 0), time(16, 0), weekdays=[0, 1, 2]) == [
            (datetime(2015, 1, 5, 12), datetime(2015, 1, 5, 16)),
            (datetime(2015, 1, 6, 12), datetime(2015, 1, 6, 16)),
            (datetime(2015, 1, 7, 12), datetime(2015, 1, 7, 16))
    ]

    assert helper.generate_dates(
        date(2015, 1, 1), date(2015, 1, 2), time(12, 0), time(0, 0)) == [
            (datetime(2015, 1, 1, 12), datetime(2015, 1, 2)),
            (datetime(2015, 1, 2, 12), datetime(2015, 1, 3))
    ]


def test_combine_datetime() -> None:
    helper: Any = AllocationFormHelpers()

    helper.date = Bunch(data=date(2015, 1, 1))
    helper.time = Bunch(data=None)
    assert helper.combine_datetime('date', 'time') == datetime(2015, 1, 1)

    helper.time = Bunch(data=time(12, 00))
    assert helper.combine_datetime('date', 'time') == datetime(2015, 1, 1, 12)

    helper.date = Bunch(data=None)
    helper.time = Bunch(data=None)
    assert helper.combine_datetime('date', 'time') is None


def test_edit_room_allocation_form() -> None:

    form = RoomAllocationEditForm()
    form.apply_dates(datetime(2015, 1, 1, 12, 0), datetime(2015, 1, 1, 18, 0))

    assert form.date.data == date(2015, 1, 1)
    assert form.start_time.data == time(12, 00)
    assert form.end_time.data == time(18, 00)

    form.as_whole_day.data = 'no'
    assert form.dates == (
        datetime(2015, 1, 1, 12, 0),
        datetime(2015, 1, 1, 18, 0)
    )

    form.as_whole_day.data = 'yes'
    assert form.dates == (
        datetime(2015, 1, 1),
        datetime(2015, 1, 2) - timedelta(microseconds=1)
    )

    form.apply_model(Bunch(  # type: ignore[arg-type]
        display_start=lambda: datetime(2015, 1, 1, 12),
        display_end=lambda: datetime(2015, 1, 1, 18),
        whole_day=False,
        quota=1,
        data=None,
    ))

    assert form.dates == (
        datetime(2015, 1, 1, 12, 0),
        datetime(2015, 1, 1, 18, 0)
    )


def test_edit_room_allocation_form_whole_day() -> None:
    form = RoomAllocationEditForm(MultiDict([
        ('date', '2020-01-01'),
        ('as_whole_day', 'no'),
        ('per_time_slot', 1),
        ('start_time', '08:00'),
        ('end_time', '08:00'),
        ('pricing_method', 'inherit')
    ]))
    assert form.per_time_slot.data == 1
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)  # type: ignore[assignment]
    assert not form.validate()
    assert form.errors == {
        'start_time': ['Start time before end time']
    }

    # skip validation if whole day
    form = RoomAllocationEditForm(MultiDict([
        ('date', '2020-01-01'),
        ('as_whole_day', 'yes'),
        ('per_time_slot', 1),
        ('start_time', '08:00'),
        ('end_time', '08:00'),
        ('pricing_method', 'inherit')
    ]))

    assert form.validate()
    assert not form.errors


def test_find_your_spot_form_single_room() -> None:
    request: Any = Bunch(POST=MultiDict([
        # 1 hour
        ('duration', '1'),
        ('duration', '0'),
        ('start', date.today().isoformat()),
        ('end', date.today().isoformat()),
        ('start_time', '08:00'),
        ('end_time', '09:00'),
        ('weekdays', '1'),
        ('weekdays', '4'),
        ('on_holidays', 'yes'),
        ('during_school_holidays', 'yes'),
        ('auto_reserve_available_slots', 'no'),
    ]))
    form = FindYourSpotForm(request.POST)
    form.request = request
    form.apply_rooms([Bunch(  # type: ignore[list-item]
        id=UUID('01234567-0123-0123-0123-000000000001'),
        title='Room 1'
    )])
    assert form.validate()
    assert form.duration.data == timedelta(hours=1)
    assert form.start.data == date.today()
    assert form.end.data == date.today()
    assert form.start_time.data == time(8, 0)
    assert form.end_time.data == time(9, 0)
    assert not form.rooms
    assert 'for_every_room' not in (  # type: ignore[misc]
        value
        for value, _label in form.auto_reserve_available_slots.choices
    )
    assert form.weekdays.data == [1, 4]
    assert form.on_holidays.data == 'yes'
    assert form.during_school_holidays.data == 'yes'
    assert form.auto_reserve_available_slots.data == 'no'


def test_find_your_spot_form_multiple_rooms() -> None:
    rooms: list[Any] = [
        Bunch(
            id=UUID('01234567-0123-0123-0123-000000000001'),
            title='Room 1'
        ),
        Bunch(
            id=UUID('01234567-0123-0123-0123-000000000002'),
            title='Room 2'
        ),
        Bunch(
            id=UUID('01234567-0123-0123-0123-000000000003'),
            title='Room 3'
        ),
    ]
    request: Any = Bunch(POST=MultiDict([
        # 30 minutes
        ('duration', '0'),
        ('duration', '30'),
        ('start', date.today().isoformat()),
        ('end', date.today().isoformat()),
        ('start_time', '08:00'),
        ('end_time', '09:00'),
        ('rooms', '01234567-0123-0123-0123-000000000001'),
        ('rooms', '01234567-0123-0123-0123-000000000003'),
        ('weekdays', '1'),
        ('weekdays', '4'),
        ('on_holidays', 'yes'),
        ('during_school_holidays', 'yes'),
        ('auto_reserve_available_slots', 'for_every_room'),
    ]))
    form = FindYourSpotForm(request.POST)
    form.request = request
    form.apply_rooms(rooms)
    assert form.validate()
    assert form.duration.data == timedelta(minutes=30)
    assert form.start.data == date.today()
    assert form.end.data == date.today()
    assert form.start_time.data == time(8, 0)
    assert form.end_time.data == time(9, 0)
    assert form.rooms.data == [rooms[0].id, rooms[2].id]
    assert form.weekdays.data == [1, 4]
    assert form.on_holidays.data == 'yes'
    assert form.during_school_holidays.data == 'yes'
    assert form.auto_reserve_available_slots.data == 'for_every_room'


def test_event_form_update_apply(session: Session) -> None:
    form = EventForm(MultiDict([
        ('description', 'Rendez-vous automnal des médecines.'),
        ('email', 'info@example.org'),
        ('end_date', ''),
        ('end_time', '18:00'),
        ('location', 'Salon du mieux-vivre à Saignelégier'),
        ('organizer', 'Société de Médecine'),
        ('start_date', '2015-06-16'),
        ('start_time', '09:30'),
        ('tags', 'Congress'),
        ('tags', 'Health'),
        ('title', 'Salon du mieux-vivre, 16e édition'),
        ('repeat', 'without')
    ]))
    form.request = Bunch(  # type: ignore[assignment]
        session=session,
        app=Bunch(
            org=Bunch(event_filter_type='tags')
        )
    )
    assert form.validate()

    event = Event()
    form.populate_obj(event)

    form = EventForm()
    form.request = Bunch(  # type: ignore[assignment]
        translate=lambda txt: txt,
        include=lambda src: None,
        app=Bunch(
            org=Bunch(event_filter_type='tags')
        )
    )
    form.process(obj=event)
    assert form.data['description'] == 'Rendez-vous automnal des médecines.'
    assert form.data['email'] == 'info@example.org'
    assert form.data['end_date'] == None
    assert form.data['end_time'] == time(18, 0)
    assert form.data['location'] == 'Salon du mieux-vivre à Saignelégier'
    assert form.data['start_date'] == date(2015, 6, 16)
    assert form.data['start_time'] == time(9, 30)
    assert form.data['organizer'] == 'Société de Médecine'
    assert sorted(form.data['tags']) == ['Congress', 'Health']
    assert form.data['title'] == 'Salon du mieux-vivre, 16e édition'
    assert form.data['weekly'] == None


def test_event_form_update_after_midnight(session: Session) -> None:
    form = EventForm(MultiDict([
        ('email', 'info@example.org'),
        ('end_time', '8:00'),
        ('start_date', '2015-06-16'),
        ('start_time', '09:30'),
        ('title', 'Salon du mieux-vivre, 16e édition'),
        ('organizer', 'Société de Médecine'),
        ('location', 'Salon du mieux-vivre à Saignelégier'),
        ('repeat', 'without')
    ]))
    form.request = Bunch(  # type: ignore[assignment]
        session=session,
        app=Bunch(
            org=Bunch(event_filter_type='tags')
        )
    )
    assert form.validate()

    event = Event()
    form.populate_obj(event)
    assert event.end.day == 17


def test_event_form_validate_weekly() -> None:
    form = EventForm(MultiDict([
        ('email', 'info@example.org'),
        ('end_date', '2015-06-23'),
        ('end_time', '18:00'),
        ('start_date', '2015-06-16'),
        ('start_time', '09:30'),
        ('title', 'Salon du mieux-vivre, 16e édition'),
        ('location', 'Salon du mieux-vivre à Saignelégier'),
        ('organizer', 'Société de Médecine'),
        ('weekly', 'MO'),
        ('repeat', 'weekly')
    ]))
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)  # type: ignore[assignment]

    assert not form.validate()
    assert form.errors == {
        'weekly': ['The weekday of the start date must be selected.']
    }

    form = EventForm(MultiDict([
        ('email', 'info@example.org'),
        ('end_date', ''),
        ('end_time', '18:00'),
        ('start_date', '2015-06-16'),
        ('start_time', '09:30'),
        ('title', 'Salon du mieux-vivre, 16e édition'),
        ('location', 'Salon du mieux-vivre à Saignelégier'),
        ('organizer', 'Société de Médecine'),
        ('weekly', 'TU'),
        ('repeat', 'weekly')
    ]))
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)  # type: ignore[assignment]

    assert not form.validate()
    assert form.errors == {
        'end_date': ['Please set and end date if the event is recurring.']
    }

    form = EventForm(MultiDict([
        ('email', 'info@example.org'),
        ('end_date', '2015-06-23'),
        ('end_time', '18:00'),
        ('start_date', '2015-06-16'),
        ('start_time', '09:30'),
        ('title', 'Salon du mieux-vivre, 16e édition'),
        ('location', 'Salon du mieux-vivre à Saignelégier'),
        ('organizer', 'Société de Médecine'),
        ('repeat', 'weekly')
    ]))
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)  # type: ignore[assignment]

    assert not form.validate()
    assert form.errors == {
        'weekly': ['Please select a weekday if the event is recurring.']
    }


def test_event_form_create_rrule(session: Session) -> None:

    def occurrences(form: EventForm) -> list[date]:
        event = Event()
        form.populate_obj(event)
        return [occurrence.date() for occurrence in event.occurrence_dates()]

    form = EventForm(data={
        'start_time': time(9, 30),
        'end_time': time(18, 0),
        'start_date': date(2015, 6, 1),
        'end_date': date(2015, 6, 7),
        'weekly': ['MO'],
        'tags': [],
        'repeat': 'weekly'
    })
    form.request = Bunch(  # type: ignore[assignment]
        session=session,
        app=Bunch(
            org=Bunch(event_filter_type='tags')
        )
    )

    assert occurrences(form) == [date(2015, 6, 1)]

    form.end_date.data = date(2015, 6, 8)
    assert occurrences(form) == [date(2015, 6, 1), date(2015, 6, 8)]

    form.end_date.data = date(2015, 6, 15)
    assert occurrences(form) == [date(2015, 6, day) for day in (1, 8, 15)]

    form.end_date.data = date(2015, 6, 10)
    form.weekly.data = ['MO', 'WE']
    assert occurrences(form) == [date(2015, 6, day) for day in (1, 3, 8, 10)]

    form.start_date.data = date(2015, 6, 3)
    form.end_date.data = date(2015, 6, 10)
    form.weekly.data = ['MO', 'WE', 'FR']
    assert occurrences(form) == [date(2015, 6, day) for day in (3, 5, 8, 10)]


@pytest.mark.parametrize('end', ['2015-06-23', '2015-08-23'])
def test_form_registration_window_form(end: str) -> None:
    form = FormRegistrationWindowForm(MultiDict([
        ('start', '2015-08-23'),
        ('end', end),
        ('limit_attendees', 'no'),
        ('waitinglist', 'no'),
    ]))
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)  # type: ignore[assignment]
    form.model = Bunch(registration_windows=[])  # type: ignore[assignment]

    assert not form.validate()
    assert form.errors == {'end': ['Please use a stop date after the start']}


@pytest.mark.parametrize('start, end', [
    ('2000-01-05', '2000-01-10'),
    ('2000-01-05', '2000-01-15'),
    ('2000-01-15', '2000-01-16'),
    ('2000-01-15', '2000-01-25'),
    ('2000-01-20', '2000-01-25'),
])
def test_form_registration_window_form_existing(start: str, end: str) -> None:
    form = FormRegistrationWindowForm(MultiDict([
        ('start', start),
        ('end', end),
        ('limit_attendees', 'no'),
        ('waitinglist', 'no'),
    ]))
    form.request = Bunch(  # type: ignore[assignment]
        translate=lambda txt: txt,
        include=lambda src: None,
        app=Bunch(
            org=Bunch(geo_provider=None, open_files_target_blank=False),
            schema='',
            websockets_private_channel='',
            websockets_client_url=lambda *args: '',
            version='1.0',
            sentry_dsn=None
        ),
        is_manager=True,
        locale='de_CH',
        url=''
    )
    form.model = Bunch(registration_windows=[  # type: ignore[assignment]
        Bunch(start=date(2000, 1, 10), end=date(2000, 1, 20))
    ])

    assert not form.validate()
    assert isinstance(form.errors['start'], list)
    assert form.errors['start'][0].interpolate() == (
        'The date range overlaps with an existing registration window '
        '(10.01.2000 - 20.01.2000).'
    )
    assert isinstance(form.errors['end'], list)
    assert form.errors['end'][0].interpolate() == (
        'The date range overlaps with an existing registration window '
        '(10.01.2000 - 20.01.2000).'
    )


def test_user_group_form(
    session_manager: SessionManager,
    session: Session
) -> None:

    users = UserCollection(session)
    user_a = users.add(username='a@example.org', password='a', role='member')
    user_b = users.add(username='b@example.org', password='b', role='member')
    user_c = users.add(username='c@example.org', password='c', role='member')
    user_a.logout_all_sessions = MagicMock()  # type: ignore[method-assign]
    user_b.logout_all_sessions = MagicMock()  # type: ignore[method-assign]
    user_c.logout_all_sessions = MagicMock()  # type: ignore[method-assign]

    formdefinition = FormDefinition(
        title='A-1',
        name='a',
        definition='# A',
        order='0',
        checksum='x'
    )

    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(session, type='extended')
    directory = directories.add(
        title="Trainers",
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )

    integration = LibresIntegration()
    integration.session_manager = session_manager
    integration.configure_libres()
    resources = integration.libres_resources
    resource = resources.add(
        title='Kitchen',
        type='room',
        timezone='Europe/Zurich'
    )

    formdefinition_ticket = Ticket(
        number='1',
        title='Existing FRM',
        group='A-1',
        handler_code='FRM',
        handler_id='existing-id-1'
    )

    deleted_formdefinition_ticket = Ticket(
        number='2',
        title='Deleted FRM',
        group='A-2',
        handler_code='FRM',
        handler_id='deleted-id-1'
    )

    deleted_directory_ticket = Ticket(
        number='3',
        title='Deleted DIR',
        group='Deleted',
        handler_code='DIR',
        handler_id='deleted-id-2'
    )

    deleted_reservation_ticket = Ticket(
        number='4',
        title='Deleted RSV',
        group='Deleted',
        handler_code='RSV',
        handler_id='deleted-id-3'
    )


    session.add_all((
        formdefinition, directory, resource, formdefinition_ticket,
        deleted_formdefinition_ticket, deleted_directory_ticket,
        deleted_reservation_ticket
    ))
    session.flush()

    request: Any = Bunch(
        session=session,
        app=Bunch(session=lambda: session),
        current_user=None,
        link=lambda *args, **kwargs: '#dummy',
    )
    form = ManageUserGroupForm()
    form.model = None
    form.request = request
    form.on_request()

    # choices
    assert sorted([x[1] for x in form.users.choices]) == [
        'a@example.org', 'b@example.org', 'c@example.org',
    ]
    assert ('EVN', 'EVN') in form.ticket_permissions.choices
    assert ('FRM', 'FRM') in form.ticket_permissions.choices
    assert ('RSV', 'RSV') in form.ticket_permissions.choices
    # make sure distinct union query works
    assert isinstance(form.ticket_permissions.choices, list)
    assert form.ticket_permissions.choices.count(('FRM-A-1', 'FRM: A-1')) == 1
    assert ('FRM-A-2', 'FRM: A-2') in form.ticket_permissions.choices
    assert ('PER', 'PER') in form.ticket_permissions.choices
    assert ('DIR', 'DIR') in form.ticket_permissions.choices
    assert ('DIR-Trainers', 'DIR: Trainers') in form.ticket_permissions.choices
    assert ('DIR-Deleted', 'DIR: Deleted') in form.ticket_permissions.choices
    assert ('RSV-Kitchen', 'RSV: Kitchen') in form.ticket_permissions.choices
    assert ('RSV-Deleted', 'RSV: Deleted') in form.ticket_permissions.choices
    assert ('EVN', 'EVN') in form.immediate_notification.choices
    assert ('FRM', 'FRM') in form.immediate_notification.choices
    assert ('FRM-A-1', 'FRM: A-1') in form.immediate_notification.choices
    assert ('FRM-A-2', 'FRM: A-2') in form.immediate_notification.choices
    assert ('PER', 'PER') in form.immediate_notification.choices
    assert ('DIR', 'DIR') in form.immediate_notification.choices
    assert (
        'DIR-Trainers', 'DIR: Trainers'
    ) in form.immediate_notification.choices
    assert (
        'DIR-Deleted', 'DIR: Deleted'
    ) in form.immediate_notification.choices
    assert (
        'RSV-Kitchen', 'RSV: Kitchen'
    ) in form.immediate_notification.choices
    assert (
        'RSV-Deleted', 'RSV: Deleted'
    ) in form.immediate_notification.choices

    # apply / update
    groups = UserGroupCollection(session)
    group = groups.add(name='A')

    form.model = group
    form.apply_model(group)
    assert form.name.data == 'A'
    assert form.users.data == []
    assert form.ticket_permissions.data == []

    form.name.data = 'A/B'
    form.name.raw_data = ['A/B']
    form.users.data = [str(user_a.id), str(user_b.id)]
    form.ticket_permissions.data = ['EVN', 'FRM-A-1', 'RSV-Kitchen']
    form.immediate_notification.data = ['EVN', 'DIR-Trainers']
    assert form.validate()

    form.update_model(group)
    session.flush()
    assert group.users.count() == 2
    assert user_a.logout_all_sessions.called is True
    assert user_b.logout_all_sessions.called is True
    assert user_c.logout_all_sessions.called is False
    assert session.query(TicketPermission).count() == 4

    form.apply_model(group)
    assert form.name.data == 'A/B'
    assert set(form.users.data) == {str(user_a.id), str(user_b.id)}
    assert set(form.ticket_permissions.data) == {
        'EVN', 'FRM-A-1', 'RSV-Kitchen'
    }
    assert set(form.immediate_notification.data) == {'EVN', 'DIR-Trainers'}

    user_a.logout_all_sessions.reset_mock()
    user_b.logout_all_sessions.reset_mock()
    user_c.logout_all_sessions.reset_mock()
    # undo mypy narrowing
    user_a.logout_all_sessions = user_a.logout_all_sessions  # type: ignore[method-assign]
    user_b.logout_all_sessions = user_b.logout_all_sessions  # type: ignore[method-assign]
    user_c.logout_all_sessions = user_c.logout_all_sessions  # type: ignore[method-assign]

    form.name.data = 'A.1'
    form.name.raw_data = ['A.1']
    form.users.data = [str(user_c.id)]
    form.ticket_permissions.data = ['PER']
    form.immediate_notification.data = ['EVN', 'PER']
    assert form.validate()
    form.update_model(group)
    session.flush()
    assert group.users.one() == user_c
    assert user_a.logout_all_sessions.called is True
    assert user_b.logout_all_sessions.called is True
    assert user_c.logout_all_sessions.called is True
    assert session.query(TicketPermission).count() == 2

    form.immediate_notification.data = ['PER']
    assert form.validate()
    form.update_model(group)
    session.flush()
    permission = session.query(TicketPermission).one()
    assert permission.handler_code == 'PER'
    assert permission.group is None
    assert permission.user_group == group
    assert permission.exclusive is True
    assert permission.immediate_notification is True


def test_settings_ticket_permissions(session: Session) -> None:
    group = UserGroupCollection(session).add(name='A')
    p_1 = TicketPermission(handler_code='PER', group=None, user_group=group)
    p_2 = TicketPermission(handler_code='FRM', group='ABC', user_group=group)
    p_3 = TicketPermission(
        handler_code='DIR',
        group='EFG',
        user_group=group,
        exclusive=False,
        immediate_notification=True
    )
    session.add(p_1)
    session.add(p_2)
    session.add(p_3)
    session.flush()

    request: Any = Bunch(session=session, translate=lambda x: str(x))
    form = OrgTicketSettingsForm()
    form.request = request
    form.on_request()

    assert form.permissions.choices == [
        (p_2.id.hex, 'FRM: ABC'),
        (p_1.id.hex, 'PER'),
    ]
    assert form.permissions.default == [p_2.id.hex, p_1.id.hex]


def test_ticket_assignment_form(session: Session) -> None:
    users = UserCollection(session)
    user_a = users.add(username='a', password='pwd', role='admin')
    users.add(username='e', password='pwd', role='editor')
    users.add(username='m', password='pwd', role='member')

    request: Any = Bunch(
        session=session,
        has_permission=lambda m, p, u: u.role != 'member'
    )
    form = TicketAssignmentForm(data={'user': user_a.id})
    form.model = None
    form.request = request
    form.on_request()

    assert sorted(name for id_, name in form.user.choices) == ['a', 'e']  # type: ignore[misc]
    assert form.username == 'a'


def test_price_submission_vat_not_set(client: Client[TestOrgApp]) -> None:
    # initially, the vat is not set on an instance. This shall not lead to vat
    # show anywhere

    expected_values = [
        'abbafan@swisscom.ch',
        '1',
        'Stück(e)',
        'Totalbetrag',
        '128.00 CHF',
    ]

    client.login_admin()
    page = client.get('/forms').click('Formular', index=1)
    page.form['title'] = 'Musicaltickets Mamma Mia!'
    page.form['definition'] = """
    Email *= @@@
    Betrag mit Preis = 0..8 (64 CHF)
    """
    assert 'show_vat' not in page
    page = page.form.submit().follow()
    page.form['email'] = 'abbafan@swisscom.ch'
    page.form['betrag_mit_preis'] = '2'
    confirm = page.form.submit().follow()

    for value in expected_values:
        assert value in confirm
    assert 'MwSt' not in confirm
    confirm.form.submit().follow()

    # test confirmation mail
    assert len(os.listdir(client.app.maildir)) == 1
    mail = client.get_email(0, 0)
    assert mail is not None
    assert ('Musicaltickets Mamma Mia!: Ihre Anfrage wurde erfasst' in
            mail['Subject'])
    for value in expected_values:
        assert value in mail['TextBody']
    assert 'MwSt' not in confirm

    # test ticket
    ticket = client.get('/tickets/ALL/open').click('FRM-')
    for value in expected_values:
        assert value in ticket
    assert 'MwSt' not in confirm


def test_price_submission_vat_set(client: Client[TestOrgApp]) -> None:
    expected_values = [
        'black@bear.ch',
        '1',
        'Stück(e)',
        'Totalbetrag',
        '99.00 CHF'
    ]

    # set vat rate
    client.login_admin()
    page = client.get('/vat-settings')
    page.form['vat_rate'] = '8.1'
    page.form.submit()

    page = client.get('/forms').click('Formular', index=1)
    page.form['title'] = 'Bio Teddybären'
    page.form['definition'] = """
    Email *= @@@
    Betrag mit Preis = 0..5 (99 CHF)
    """
    page.form['show_vat'].checked = True
    page = page.form.submit().follow()
    page.form['email'] = 'black@bear.ch'
    page.form['betrag_mit_preis'] = '1'
    confirm = page.form.submit().follow()

    for value in expected_values:
        assert value in confirm
    assert '8.1% enthalten' in confirm
    assert '8.1% enthalten: 7.42 CHF' not in confirm
    confirm.form.submit().follow()

    # test confirmation mail
    assert len(os.listdir(client.app.maildir)) == 1
    mail = client.get_email(0, 0)
    assert mail is not None
    assert 'Bio Teddybären: Ihre Anfrage wurde erfasst' in mail['Subject']
    for value in expected_values:
        assert value in mail['TextBody']
    assert '8.1% enthalten: 7.42 CHF' in mail['TextBody']

    # test ticket
    ticket = client.get('/tickets/ALL/open').click('FRM-')
    for value in expected_values:
        assert value in ticket
    assert '8.1% enthalten: 7.42 CHF' in ticket
