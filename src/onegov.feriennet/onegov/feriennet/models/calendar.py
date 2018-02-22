import icalendar

from onegov.activity import Attendee
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import module_path
from onegov.feriennet.models import VacationActivity
from sedate import standardize_date, utcnow
from sqlalchemy import and_, select


class Calendar(object):
    """ A base for all calendars that return icalendar renderings. """

    calendars = {}

    def __init_subclass__(cls, name, **kwargs):
        super().__init_subclass__(**kwargs)

        assert name not in cls.calendars
        cls.name = name
        cls.calendars[name] = cls

    @classmethod
    def from_name_and_token(cls, session, name, token):
        calendar = cls.calendars.get(name)
        return calendar and calendar.from_token(session, token)

    def calendar(self, request):
        raise NotImplementedError

    def new(self):
        calendar = icalendar.Calendar()
        calendar.add('prodid', '-//OneGov//onegov.feriennet//')
        calendar.add('version', '2.0')
        calendar.add('method', 'PUBLISH')

        return calendar


class AttendeeCalendar(Calendar, name='attendee'):
    """ Renders all confirmed activites of the given attendee. """

    attendee_calendar = as_selectable_from_path(
        module_path('onegov.feriennet', 'queries/attendee_calendar.sql'))

    def __init__(self, session, attendee):
        self.session = session
        self.attendee = attendee

    @property
    def attendee_id(self):
        return self.attendee.id.hex

    @property
    def token(self):
        return self.attendee.subscription_token

    @classmethod
    def from_token(cls, session, token):
        attendee = session.query(Attendee)\
            .filter_by(subscription_token=token)\
            .first()

        return attendee and cls(session, attendee)

    def calendar(self, request):
        calendar = self.new()
        calendar.add('x-wr-calname', self.attendee.name)

        # refresh every 120 minutes by default (Outlook and maybe others)
        calendar.add('x-published-ttl', 'PT120M')

        for event in self.events(request):
            calendar.add_component(event)

        return calendar.to_ical()

    def events(self, request):
        session = request.session
        stmt = self.attendee_calendar

        records = session.execute(select(stmt.c).where(and_(
            stmt.c.attendee_id == self.attendee_id,
            stmt.c.state == 'accepted',
            stmt.c.confirmed == True
        )))

        datestamp = utcnow()

        for record in records:
            event = icalendar.Event()

            event.add('uid', record.booking_id.hex)
            event.add('summary', record.title)

            if record.note:
                event.add('description', record.note)

            event.add('dtstart', standardize_date(record.start, 'UTC'))
            event.add('dtend', standardize_date(record.end, 'UTC'))
            event.add('dtstamp', datestamp)
            event.add('url', request.class_link(
                VacationActivity, {'name': record.name}))

            if record.meeting_point:
                event.add('location', record.meeting_point)

            if record.lat and record.lon:
                event.add('geo', (float(record.lat), float(record.lon)))

            if record.meeting_point and record.lat and record.lon:
                event.add(
                    "X-APPLE-STRUCTURED-LOCATION",
                    f"geo:{record.lat},{record.lon}",
                    parameters={
                        "VALUE": "URI",
                        "X-ADDRESS": record.meeting_point,
                        "X-APPLE-RADIUS": "50",
                        "X-TITLE": record.meeting_point
                    }
                )

            yield event
