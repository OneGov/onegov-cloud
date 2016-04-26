import pytest

from datetime import date, datetime, time, timedelta
from dateutil.rrule import MO, WE
from onegov.core.utils import Bunch
from onegov.event import Event
from onegov.town.forms import (
    DaypassAllocationForm,
    EventForm,
    RoomAllocationEditForm,
    RoomAllocationForm,
)
from onegov.town.forms.allocation import AllocationFormHelpers
from webob.multidict import MultiDict


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
    assert hasattr(form, 'partly_available')

    # those are not (yet) customizable in onegov.town
    assert not hasattr(form, 'grouped')
    assert not hasattr(form, 'raster')
    assert not hasattr(form, 'approve_manually')


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
        'start_time': time(12, 00),
        'end_time': time(16, 00),
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


def test_room_except_for():
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

    assert helper.generate_dates(date(2016, 3, 26), date(2016, 3, 28)) == [
        (datetime(2016, 3, 26), datetime(2016, 3, 26)),
        (datetime(2016, 3, 27), datetime(2016, 3, 27)),
        (datetime(2016, 3, 28), datetime(2016, 3, 28)),
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


def test_combine_datetime():
    helper = AllocationFormHelpers()

    helper.date = Bunch(data=date(2015, 1, 1))
    helper.time = Bunch(data=None)
    assert helper.combine_datetime('date', 'time') == datetime(2015, 1, 1)

    helper.time = Bunch(data=time(12, 00))
    assert helper.combine_datetime('date', 'time') == datetime(2015, 1, 1, 12)

    helper.date = Bunch(data=None)
    helper.time = Bunch(data=None)
    assert helper.combine_datetime('date', 'time') is None


def test_edit_room_allocation_form():

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

    form.apply_model(Bunch(
        display_start=lambda: datetime(2015, 1, 1, 12),
        display_end=lambda: datetime(2015, 1, 1, 18),
        whole_day=False
    ))

    assert form.dates == (
        datetime(2015, 1, 1, 12, 0),
        datetime(2015, 1, 1, 18, 0)
    )


def test_event_form_update_apply():
    form = EventForm(MultiDict([
        ('description', 'Rendez-vous automnal des médecines.'),
        ('email', 'info@example.org'),
        ('end_date', ''),
        ('end_time', '18:00'),
        ('location', 'Salon du mieux-vivre à Saignelégier'),
        ('start_date', '2015-06-16'),
        ('start_time', '09:30'),
        ('tags', 'Congress'),
        ('tags', 'Health'),
        ('title', 'Salon du mieux-vivre, 16e édition'),
    ]))
    assert form.validate()

    event = Event()
    form.populate_obj(event)
    form = EventForm()
    form.process(obj=event)
    assert form.data['description'] == 'Rendez-vous automnal des médecines.'
    assert form.data['email'] == 'info@example.org'
    assert form.data['end_date'] == None
    assert form.data['end_time'] == time(18, 0)
    assert form.data['location'] == 'Salon du mieux-vivre à Saignelégier'
    assert form.data['start_date'] == date(2015, 6, 16)
    assert form.data['start_time'] == time(9, 30)
    assert sorted(form.data['tags']) == ['Congress', 'Health']
    assert form.data['title'] == 'Salon du mieux-vivre, 16e édition'
    assert form.data['weekly'] == None


def test_event_form_update_after_midnight():
    form = EventForm(MultiDict([
        ('email', 'info@example.org'),
        ('end_time', '8:00'),
        ('start_date', '2015-06-16'),
        ('start_time', '09:30'),
        ('title', 'Salon du mieux-vivre, 16e édition'),
    ]))
    assert form.validate()

    event = Event()
    form.populate_obj(event)
    assert event.end.day == 17


def test_event_form_validate():
    form = EventForm(MultiDict([
        ('email', 'info@example.org'),
        ('end_date', '2015-06-23'),
        ('end_time', '18:00'),
        ('start_date', '2015-06-16'),
        ('start_time', '09:30'),
        ('title', 'Salon du mieux-vivre, 16e édition'),
        ('weekly', 'MO'),
    ]))
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
        ('weekly', 'TU'),
    ]))
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
    ]))
    assert not form.validate()
    assert form.errors == {
        'weekly': ['Please select a weekday if the event is recurring.']
    }


def test_event_form_create_rrule():

    def occurrences(form):
        event = Event()
        form.populate_obj(event)
        return [occurrence.date() for occurrence in event.occurrence_dates()]

    form = EventForm(data={
        'start_time': time(9, 30),
        'end_time': time(18, 0),
        'start_date': date(2015, 6, 1),
        'end_date': date(2015, 6, 7),
        'weekly': ['MO'],
        'tags': []
    })
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
