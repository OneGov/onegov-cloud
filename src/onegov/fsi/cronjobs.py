from sedate import utcnow

from onegov.core.templates import render_template
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi import _, FsiApp
from onegov.fsi.layouts.notification import MailLayout
from onegov.fsi.models.course_notification_template import \
    CourseNotificationTemplate


def send_scheduled_reminders(request):
    events = CourseEventCollection(request.session)

    for event in events:
        pass
        # template = res.course_event.reminder_template
        # assert template
        # assert res.attendee
        # title = _('Reminder for course: ${name}',
        #           mapping={'name': res.course.name})
        # content = render_template('mail_notification.pt', request, {
        #         'layout': MailLayout(res.course_event, request),
        #         'title': title,
        #         'notification': template.text_html,
        #         'attendee': res.attendee
        #     })
        # request.app.send_marketing_email(
        #     receivers=(res.attendee.email, ),
        #     subject=template.subject,
        #     content=content
        # )
        # template.last_sent = utcnow()


@FsiApp.cronjob(hour=8, minute=30, timezone='Europe/Zurich')
def send_reminder_mails(request):
    send_scheduled_reminders(request)
