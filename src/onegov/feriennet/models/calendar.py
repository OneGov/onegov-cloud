from __future__ import annotations

import icalendar

from onegov.activity import Attendee
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import module_path
from onegov.feriennet.models import VacationActivity
from sedate import standardize_date, utcnow
from sqlalchemy import and_, select


from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from onegov.activity.models.booking import BookingState
    from onegov.feriennet.request import FeriennetRequest
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql.selectable import Alias
    from typing import NamedTuple
    from typing import Self
    from uuid import UUID

    class AttendeeCalendarRow(NamedTuple):
        uid: str
        period: str
        confirmed: bool
        title: str
        name: str
        lat: str | None
        lon: str | None
        start: datetime
        end: datetime
        meeting_point: str | None
        note: str | None
        cancelled: bool
        attendee_id: UUID
        state: BookingState
        booking_id: UUID


class Calendar:
    """ A base for all calendars that return icalendar renderings. """

    name: ClassVar[str]
    calendars: ClassVar[dict[str, type[Calendar]]] = {}

    def __init_subclass__(cls, name: str, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        assert name not in cls.calendars
        cls.name = name
        cls.calendars[name] = cls

    @classmethod
    def from_token(cls, session: Session, token: str) -> Calendar | None:
        raise NotImplementedError

    @classmethod
    def from_name_and_token(
        cls,
        session: Session,
        name: str,
        token: str
    ) -> Calendar | None:
        calendar = cls.calendars.get(name)
        if calendar is None:
            return None
        return calendar.from_token(session, token)

    def calendar(self, request: FeriennetRequest) -> bytes:
        raise NotImplementedError

    def new(self) -> icalendar.Calendar:
        calendar = icalendar.Calendar()
        calendar.add('prodid', '-//OneGov//onegov.feriennet//')
        calendar.add('version', '2.0')
        calendar.add('method', 'PUBLISH')

        return calendar


class AttendeeCalendar(Calendar, name='attendee'):
    """ Renders all confirmed activites of the given attendee. """

    def __init__(self, session: Session, attendee: Attendee) -> None:
        self.session = session
        self.attendee = attendee

    @property
    def attendee_calendar(self) -> Alias:
        return as_selectable_from_path(
            module_path('onegov.feriennet', 'queries/attendee_calendar.sql'))

    @property
    def attendee_id(self) -> str:
        return self.attendee.id.hex

    @property
    def token(self) -> str:
        return self.attendee.subscription_token

    @classmethod
    def from_token(cls, session: Session, token: str) -> Self | None:
        attendee = (
            session.query(Attendee)
            .filter_by(subscription_token=token)
            .first()
        )

        return cls(session, attendee) if attendee else None

    def calendar(self, request: FeriennetRequest) -> bytes:
        calendar = self.new()
        calendar.add('x-wr-calname', self.attendee.name)

        # refresh every 120 minutes by default (Outlook and maybe others)
        calendar.add('x-published-ttl', 'PT120M')

        for event in self.events(request):
            calendar.add_component(event)

        return calendar.to_ical()

    def events(
        self,
        request: FeriennetRequest
    ) -> Iterator[icalendar.Event]:
        session = request.session
        stmt = self.attendee_calendar

        records: Query[AttendeeCalendarRow]
        # FIXME: Should this exclude cancelled occasions, or does an accepted
        #        booking guarantee that the occassion is not cancelled?
        records = session.execute(select(stmt.c).where(and_(
            stmt.c.attendee_id == self.attendee_id,
            stmt.c.state == 'accepted',
            stmt.c.confirmed == True
        )))

        datestamp = utcnow()

        for record in records:
            event = icalendar.Event()

            event.add('uid', record.uid)
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
                    'X-APPLE-STRUCTURED-LOCATION',
                    f'geo:{record.lat},{record.lon}',
                    parameters={
                        'VALUE': 'URI',
                        'X-ADDRESS': record.meeting_point,
                        'X-APPLE-RADIUS': '50',
                        'X-TITLE': record.meeting_point
                    }
                )

            yield event
