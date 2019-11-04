from datetime import timedelta

from sedate import utcnow
from sqlalchemy import and_

from onegov.core.templates import render_template
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.models.reservation import Reservation
from onegov.fsi.layout import MailLayout
from onegov.fsi import _, FsiApp


def send_scheduled_reminders(request):
    reservations = ReservationCollection(request.session).for_reminder_mails()

    for res in reservations:
        if not res.course_event.template:
            continue
        template = res.course_event.template
        subject = _('Reminder for course: ${name}',
                    mapping={'name': res.course.name})
        content = render_template(
            'mail_layout.pt', request,
            {
                'layout': MailLayout(template, request),
                'title': subject,
                'notification': res.template.text
                        })

        request.app.send_marketing_email(
                    receivers=(res.attendee.email, ),
                    subject=subject,
                    content=content)
        res.reminder_sent = utcnow()


@FsiApp.cronjob(hour=8, minute=30, timezone='Europe/Zurich')
def send_reminder_mails(request):
    send_scheduled_reminders(request)
