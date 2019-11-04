import pytest
import transaction
from webtest import TestApp as Client

from onegov.fsi.collections.reservation import ReservationCollection
from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url


@pytest.mark.skip('Session merging is not working')
def test_send_reminder_mails(
        session, fsi_app, smtp, future_course_reservation):
    reservation, data = future_course_reservation

    client = Client(fsi_app)
    app_session = fsi_app.session()
    session.merge(app_session)
    collection = ReservationCollection(session)
    reservations = collection.for_reminder_mails()
    assert collection.query().count() == 1
    assert reservations.count() == 1

    job = get_cronjob_by_name(fsi_app, 'send_reminder_mails')
    job.app = fsi_app
    assert len(smtp.outbox) == 0

    url = get_cronjob_url(job)
    resp = client.get(url)
    assert len(smtp.outbox) == 1
