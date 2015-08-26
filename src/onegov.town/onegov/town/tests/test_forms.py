import pytest

from datetime import date, datetime, time
from dateutil.rrule import MO, WE
from libres.db.models import Allocation
from onegov.town.forms import (
    DaypassAllocationForm,
    ReservationForm,
    RoomAllocationForm
)
from onegov.town.forms.allocation import AllocationFormHelpers


@pytest.mark.parametrize('form_class', [
    DaypassAllocationForm,
    RoomAllocationForm
])
def test_allocation_form_dates(form_class):
    """ Makes sure all required methods are implemented. """
    form = form_class()

    # those are customizable
    assert hasattr(form, 'dates')
    assert hasattr(form, 'whole_day')
    assert hasattr(form, 'quota')
    assert hasattr(form, 'quota_limit')
    assert hasattr(form, 'data')

    # those are not (yet) customizable in onegov.town
    assert not hasattr(form, 'grouped')
    assert not hasattr(form, 'raster')
    assert not hasattr(form, 'approve_manually')
    assert not hasattr(form, 'partly_available')


def test_daypass_single_date():
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
    assert not form.data


def test_daypass_multiple_dates():
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


def test_daypass_except_for():
    form = DaypassAllocationForm(data={
        'start': datetime(2015, 8, 3),
        'end': datetime(2015, 8, 6),
        'except_for': [MO.weekday, WE.weekday]
    })

    assert form.dates == [
        (datetime(2015, 8, 4), datetime(2015, 8, 4)),
        (datetime(2015, 8, 6), datetime(2015, 8, 6)),
    ]


def test_room_single_date():
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'start_time': '12:00',
        'end_time': '16:00',
        'as_whole_day': 'no'
    })

    assert form.dates == [(datetime(2015, 8, 4, 12), datetime(2015, 8, 4, 16))]
    assert form.whole_day == False
    assert form.quota == 1
    assert form.quota_limit == 1
    assert not form.data


def test_room_whole_day():
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 4),
        'as_whole_day': 'yes'
    })

    assert form.dates == [(datetime(2015, 8, 4), datetime(2015, 8, 4))]
    assert form.whole_day == True
    assert form.quota == 1
    assert form.quota_limit == 1
    assert not form.data


def test_room_multiple_dates():
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 4),
        'end': date(2015, 8, 8),
        'start_time': '12:00',
        'end_time': '16:00'
    })

    assert form.dates == [
        (datetime(2015, 8, 4, 12), datetime(2015, 8, 4, 16)),
        (datetime(2015, 8, 5, 12), datetime(2015, 8, 5, 16)),
        (datetime(2015, 8, 6, 12), datetime(2015, 8, 6, 16)),
        (datetime(2015, 8, 7, 12), datetime(2015, 8, 7, 16)),
        (datetime(2015, 8, 8, 12), datetime(2015, 8, 8, 16)),
    ]


def test_room_except_for():
    form = RoomAllocationForm(data={
        'start': date(2015, 8, 3),
        'end': date(2015, 8, 6),
        'start_time': '12:00',
        'end_time': '16:00',
        'except_for': [MO.weekday, WE.weekday]
    })

    assert form.dates == [
        (datetime(2015, 8, 4, 12), datetime(2015, 8, 4, 16)),
        (datetime(2015, 8, 6, 12), datetime(2015, 8, 6, 16)),
    ]


def test_generate_dates():
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


def test_generate_datetimes():
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


def test_reservation_form_partly_available():
    allocation = Allocation()

    allocation.timezone = 'Europe/Zurich'
    allocation.start = datetime(2015, 1, 1, 10)
    allocation.end = datetime(2015, 1, 1, 16)

    allocation.partly_available = True
    form = ReservationForm.for_allocation(allocation)()
    assert hasattr(form, 'start')
    assert hasattr(form, 'end')
    assert form.start.default == '10:00'
    assert form.end.default == '16:00'

    allocation.partly_available = False
    form = ReservationForm.for_allocation(allocation)()
    assert not hasattr(form, 'start')
    assert not hasattr(form, 'end')


def test_reservation_form_quota():
    allocation = Allocation()

    allocation.quota = 1
    allocation.quota_limit = 1
    form = ReservationForm.for_allocation(allocation)()
    assert not hasattr(form, 'quota')

    allocation.quota = 2
    allocation.quota_limit = 1
    form = ReservationForm.for_allocation(allocation)()
    assert not hasattr(form, 'quota')

    allocation.quota = 1
    allocation.quota_limit = 2
    form = ReservationForm.for_allocation(allocation)()
    assert not hasattr(form, 'quota')

    allocation.quota = 2
    allocation.quota_limit = 2
    form = ReservationForm.for_allocation(allocation)()
    assert hasattr(form, 'quota')

    allocation.quota = 2
    allocation.quota_limit = 0
    form = ReservationForm.for_allocation(allocation)()
    assert hasattr(form, 'quota')
