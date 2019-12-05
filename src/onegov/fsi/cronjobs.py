from sedate import utcnow

from onegov.core.templates import render_template
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi import _, FsiApp
from onegov.fsi.layouts.notification import MailLayout
from onegov.fsi.models.course_notification_template import \
    CourseNotificationTemplate


def send_scheduled_reminders(request):
    reservations = ReservationCollection(request.session).for_reminder_mails()

    for res in reservations:
        assert res.course_event.template
        template = request.session.query(
            CourseNotificationTemplate).filter_by(
            course_event_id=res.course_event.id).one()
        title = _('Reminder for course: ${name}',
                  mapping={'name': res.course.name})
        content = render_template(
            'mail_layout.pt', request,
            {
                'layout': MailLayout(res, request),
                'title': title,
                'notification': template.text
            })
        mail = res.attendee.email
        request.app.send_marketing_email(
            receivers=(mail, ),
            subject=template.subject,
            content=content
        )
        res.reminder_sent = utcnow()


# @FsiApp.cronjob(hour=8, minute=30, timezone='Europe/Zurich')
# def send_reminder_mails(request):
#     send_scheduled_reminders(request)
