from __future__ import annotations

from sedate import utcnow

from onegov.core.templates import render_template
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi import _, FsiApp
from onegov.fsi.layouts.notification import MailLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.fsi.request import FsiRequest


def send_scheduled_reminders(request: FsiRequest) -> None:

    events = CourseEventCollection(
        request.session,
        show_locked=True,
        show_hidden=True
    ).get_past_reminder_date()

    for course_event in events:
        if not course_event.attendees.count():
            continue
        template = course_event.reminder_template

        if not template or template.last_sent:
            continue

        title = _('Reminder for course event: ${name}',
                  mapping={'name': course_event.course.name})

        for attendee in course_event.attendees:
            content = render_template('mail_notification.pt', request, {
                'layout': MailLayout(template, request),
                'title': title,
                'notification': template.text_html,
                'attendee': attendee
            })
            request.app.send_transactional_email(
                receivers=(attendee.email, ),
                subject=template.subject,
                content=content
            )
        template.last_sent = utcnow()


@FsiApp.cronjob(hour=8, minute=30, timezone='Europe/Zurich')
def send_reminder_mails(request: FsiRequest) -> None:
    send_scheduled_reminders(request)
