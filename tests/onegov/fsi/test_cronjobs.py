import pytest
import transaction
from webtest import TestApp as Client
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.models.notification_template import FsiNotificationTemplate
from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url


@pytest.mark.skip('Causses infinite recusrion upon rendering template')
def test_send_reminder_mails(
        fsi_app, smtp, future_course_reservation, planner):

    session = fsi_app.session()
    planner, data = planner(session)
    assert planner.id
    reservation, data = future_course_reservation(session)
    reservation.course_event.template = FsiNotificationTemplate(
        owner_id=planner.id,
        subject='S',
        text='T')

    transaction.commit()
    reservations = ReservationCollection(session).for_reminder_mails()
    assert reservations.count() == 1

    client = Client(fsi_app)
    job = get_cronjob_by_name(fsi_app, 'send_reminder_mails')
    job.app = fsi_app

    assert len(smtp.outbox) == 0
    url = get_cronjob_url(job)
    resp = client.get(url)
    assert len(smtp.outbox) == 1
