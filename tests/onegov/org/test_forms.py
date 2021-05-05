import pytest

from datetime import date, datetime, time, timedelta
from dateutil.rrule import MO, WE
from onegov.core.utils import Bunch
from onegov.event import Event
from onegov.form import FormDefinition
from onegov.org.forms import DaypassAllocationForm
from onegov.org.forms import EventForm
from onegov.org.forms import FormRegistrationWindowForm
from onegov.org.forms import ManageUserGroupForm
from onegov.org.forms import RoomAllocationEditForm
from onegov.org.forms import RoomAllocationForm
from onegov.org.forms.allocation import AllocationFormHelpers
from onegov.org.forms.settings import OrgTicketSettingsForm
from onegov.ticket import TicketPermission
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from unittest.mock import MagicMock
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

    # those are not (yet) customizable in onegov.org
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
        whole_day=False,
        quota=1
    ))

    assert form.dates == (
        datetime(2015, 1, 1, 12, 0),
        datetime(2015, 1, 1, 18, 0)
    )


def test_edit_room_allocation_form_whole_day():
    form = RoomAllocationEditForm(MultiDict([
        ('date', '2020-01-01'),
        ('as_whole_day', 'no'),
        ('per_time_slot', 1),
        ('start_time', '08:00'),
        ('end_time', '08:00'),
    ]))
    assert form.per_time_slot.data == 1
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)
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
    ]))

    assert form.validate()
    assert not form.errors


def test_event_form_update_apply():
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
    assert form.validate()

    event = Event()
    form.populate_obj(event)
    form = EventForm()
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)
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


def test_event_form_update_after_midnight():
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
    assert form.validate()

    event = Event()
    form.populate_obj(event)
    assert event.end.day == 17


def test_event_form_validate_weekly():
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
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)

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
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)

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
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)

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
        'tags': [],
        'repeat': 'weekly'
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


@pytest.mark.parametrize('end', ['2015-06-23', '2015-08-23'])
def test_form_registration_window_form(end):
    form = FormRegistrationWindowForm(MultiDict([
        ('start', '2015-08-23'),
        ('end', end),
        ('limit_attendees', 'no'),
        ('waitinglist', 'no'),
    ]))
    form.request = Bunch(translate=lambda txt: txt, include=lambda src: None)

    assert not form.validate()
    assert form.errors == {'end': ['Please use a stop date after the start']}


def test_user_group_form(session):
    users = UserCollection(session)
    user_a = users.add(username='a@example.org', password='a', role='member')
    user_b = users.add(username='b@example.org', password='b', role='member')
    user_c = users.add(username='c@example.org', password='c', role='member')
    user_a.logout_all_sessions = MagicMock()
    user_b.logout_all_sessions = MagicMock()
    user_c.logout_all_sessions = MagicMock()

    session.add(
        FormDefinition(
            title='A',
            name='a',
            definition='# A',
            order=0,
            checksum='x'
        )
    )
    session.flush()

    request = Bunch(session=session, current_user=None)
    form = ManageUserGroupForm()
    form.request = request
    form.on_request()

    # choices
    assert sorted([x[1] for x in form.users.choices]) == [
        'a@example.org', 'b@example.org', 'c@example.org',
    ]
    assert form.ticket_permissions.choices == [
        ('AGN-', 'AGN'),
        ('DIR-', 'DIR'),
        ('EVN-', 'EVN'),
        ('FER-', 'FER'),
        ('FRM-', 'FRM'),
        ('FRM-ABC', 'FRM: ABC'),
        ('PER-', 'PER'),
        ('RSV-', 'RSV')
    ]

    # apply / update
    groups = UserGroupCollection(session)
    group = groups.add(name='A')

    form.apply_model(group)
    assert form.name.data == 'A'
    assert form.users.data == []
    assert form.ticket_permissions.data == []

    form.name.data = 'A/B'
    form.users.data = [str(user_a.id), str(user_b.id)]
    form.ticket_permissions.data = ['EVN-', 'FRM-ABC']

    form.update_model(group)
    assert group.users.count() == 2
    assert user_a.logout_all_sessions.called is True
    assert user_b.logout_all_sessions.called is True
    assert user_c.logout_all_sessions.called is False
    assert session.query(TicketPermission).count() == 2

    form.apply_model(group)
    assert form.name.data == 'A/B'
    assert set(form.users.data) == {str(user_a.id), str(user_b.id)}
    assert set(form.ticket_permissions.data) == {'EVN-', 'FRM-ABC'}

    user_a.logout_all_sessions.reset_mock()
    user_b.logout_all_sessions.reset_mock()
    user_c.logout_all_sessions.reset_mock()

    form.name.data = 'A.1'
    form.users.data = [str(user_c.id)]
    form.ticket_permissions.data = ['PER-']
    form.update_model(group)
    assert group.users.one() == user_c
    assert user_a.logout_all_sessions.called is True
    assert user_b.logout_all_sessions.called is True
    assert user_c.logout_all_sessions.called is True
    permission = session.query(TicketPermission).one()
    assert permission.handler_code == 'PER'
    assert permission.group is None
    assert permission.user_group == group


def test_settings_ticket_permissions(session):
    group = UserGroupCollection(session).add(name='A')
    p_1 = TicketPermission(handler_code='PER', group=None, user_group=group)
    p_2 = TicketPermission(handler_code='FRM', group='ABC', user_group=group)
    session.add(p_1)
    session.add(p_2)
    session.flush()

    request = Bunch(session=session)
    form = OrgTicketSettingsForm()
    form.request = request
    form.on_request()

    assert form.permissions.choices == [
        (p_2.id.hex, 'FRM: ABC'),
        (p_1.id.hex, 'PER'),
    ]
    assert form.permissions.default == [p_2.id.hex, p_1.id.hex]
