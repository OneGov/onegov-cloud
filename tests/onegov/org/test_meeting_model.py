from __future__ import annotations

from datetime import datetime, timedelta
from markupsafe import Markup
from onegov.org.models.meeting import Meeting, MeetingCollection
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_meeting_properties_with_datetime() -> None:
    meeting = Meeting(title='Session', start_datetime=datetime(2020, 5, 1, 10))
    assert meeting.fts_suggestion == ['Session 01.05.2020']
    assert meeting.fts_last_change == datetime(2020, 5, 1, 10)
    assert meeting.title_text == 'Session (2020-05-01 10:00:00)'
    assert meeting.display_name == 'Session 01.05.2020'
    assert 'Session' in repr(meeting)


def test_meeting_properties_without_datetime() -> None:
    meeting = Meeting(title='Session', start_datetime=None)
    assert meeting.fts_suggestion == ['Session']
    assert meeting.fts_last_change is None
    assert meeting.title_text == 'Session'
    assert meeting.display_name == 'Session'


def test_meeting_past() -> None:
    assert Meeting(
        title='P', start_datetime=utcnow() - timedelta(days=1)).past is True
    assert Meeting(
        title='F', start_datetime=utcnow() + timedelta(days=1)).past is False
    assert Meeting(title='N', start_datetime=None).past is False


def test_meeting_collection(session: Session) -> None:
    meetings = MeetingCollection(session)
    assert meetings.title == 'Meeting'
    assert meetings.model_class is Meeting

    session.add(Meeting(
        title='Past', address=Markup('Hall'),
        start_datetime=utcnow() - timedelta(days=1)))
    session.add(Meeting(
        title='Future', address=Markup('Hall'),
        start_datetime=utcnow() + timedelta(days=1)))
    session.flush()

    assert meetings.query().count() == 2
    assert meetings.for_filter(past=True).query().count() == 1
    assert meetings.for_filter(past=False).query().one().title == 'Future'
