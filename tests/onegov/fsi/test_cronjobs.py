from onegov.fsi.collections.course_event import CourseEventCollection

from tests.onegov.org.common import get_cronjob_by_name, get_cronjob_url, \
    get_mail


def test_send_reminder_mails(client_with_db, smtp):
    app = client_with_db.app
    session = app.session()
    events = CourseEventCollection(session).get_past_reminder_date()
    # empty and future course event, future contains two reservations
    assert events.count() == 2

    job = get_cronjob_by_name(app, 'send_reminder_mails')
    job.app = app
    assert len(smtp.outbox) == 0
    url = get_cronjob_url(job)
    client_with_db.get(url)
    # planner_future_res and attendee_future_res
    assert len(smtp.outbox) == 2

    message = get_mail(client_with_db.app.smtp.outbox, 0)
    assert message['subject'] == '=?utf-8?q?Erinnerung_Kursdurchf=C3=BChrung?='
