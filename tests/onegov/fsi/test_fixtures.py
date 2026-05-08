from __future__ import annotations

from onegov.fsi.models.course_attendee import CourseAttendee
from onegov.fsi.models.course_event import CourseEvent
from onegov.fsi.models.course_subscription import CourseSubscription


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from sqlalchemy.orm import Session
    from .conftest import TestFsiApp


def test_db_mock_function_session(
    session: Session,
    db_mock_session: Callable[[Session], Session]
) -> None:
    session = db_mock_session(session)

    assert session.query(CourseAttendee).first()
    assert session.query(CourseEvent).first()
    assert session.query(CourseSubscription).count() == 2


def test_db_mock_app_session(
    fsi_app: TestFsiApp,
    db_mock_session: Callable[[Session], Session]
) -> None:
    session = fsi_app.session()
    session = db_mock_session(session)

    assert session.query(CourseAttendee).first()
    assert session.query(CourseEvent).first()
    assert session.query(CourseSubscription).count() == 2
