from __future__ import annotations

import os

from onegov.fsi.collections.course_event import CourseEventCollection
from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_send_reminder_mails(client_with_db: Client) -> None:
    client = client_with_db
    app = client.app
    session = app.session()
    events = CourseEventCollection(session).get_past_reminder_date()
    # empty and future course event, future contains two reservations
    assert events.count() == 2

    job = get_cronjob_by_name(app, 'send_reminder_mails')
    assert job is not None
    job.app = app
    assert len(os.listdir(client.app.maildir)) == 0
    url = get_cronjob_url(job)
    client_with_db.get(url)
    # planner_future_res and attendee_future_res
    assert len(os.listdir(client.app.maildir)) == 2

    message = client.get_email(0)
    assert message['Subject'] == 'Erinnerung Kursdurchführung'
