from __future__ import annotations

from onegov.core.security import Secret
from onegov.core.templates import render_template
from onegov.fsi import FsiApp
from onegov.fsi.collections.notification_template import (
    CourseNotificationTemplateCollection)
from onegov.fsi.forms.notification import (
    NotificationForm, NotificationTemplateSendForm)
from onegov.fsi.layouts.notification import (
    NotificationTemplateLayout, NotificationTemplateCollectionLayout,
    EditNotificationTemplateLayout, MailLayout, SendNotificationTemplateLayout)
from onegov.fsi.models import CourseAttendee
from onegov.fsi.models.course_notification_template import (
    CourseNotificationTemplate)
from onegov.fsi import _
from sedate import utcnow


from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath
    from collections.abc import Iterable, Iterator, Sequence
    from onegov.core.mail import Attachment
    from onegov.core.types import EmailJsonDict, RenderData
    from onegov.fsi.request import FsiRequest
    from uuid import UUID
    from webob import Response


def handle_send_email(
    self: CourseNotificationTemplate,
    request: FsiRequest,
    recipients: Sequence[UUID] | Sequence[CourseAttendee],
    cc_to_sender: bool = True,
    show_sent_count: bool = True,
    attachments: Iterable[Attachment | StrPath] | None = None
) -> FsiRequest:
    """Recipients must be a list of attendee id's or attendees"""

    if not recipients:
        request.alert(_('There are no recipients matching the selection'))
        return request

    att = request.attendee
    assert att is not None
    if not isinstance(recipients[0], CourseAttendee):
        recipients = (
            request.session.query(CourseAttendee)
            .filter(CourseAttendee.id.in_(recipients))
            .all()
        )
    else:
        recipients = cast('Sequence[CourseAttendee]', recipients)

    if cc_to_sender and att not in recipients:
        recipients = list(recipients)
        recipients.append(att)

    mail_layout = MailLayout(self, request)

    def email_iter() -> Iterator[EmailJsonDict]:
        for attendee in recipients:
            content = render_template('mail_notification.pt', request, {
                'layout': mail_layout,
                'title': self.subject,
                'information': self.text_html,
                'attendee': attendee
            })

            yield request.app.prepare_email(
                receivers=(attendee.email, ),
                subject=self.subject,
                content=content,
                category='transactional',
                attachments=attachments or ()
            )

    request.app.send_transactional_email_batch(email_iter())
    self.last_sent = utcnow()

    if show_sent_count:
        request.success(_(
            'Successfully sent the e-mail to ${count} recipients',
            mapping={
                'count': len(recipients)
            }
        ))
    return request


@FsiApp.html(
    model=CourseNotificationTemplateCollection,
    template='notifications.pt',
    permission=Secret
)
def view_notifications(
    self: CourseNotificationTemplateCollection,
    request: FsiRequest
) -> RenderData:

    layout = NotificationTemplateCollectionLayout(self, request)
    # This was a workaround and should be removed in the future
    self.auto_add_templates_if_not_existing()
    has_entries = request.session.query(self.query().exists()).scalar()

    return {
        'layout': layout,
        'has_entries': has_entries
    }


@FsiApp.html(
    model=CourseNotificationTemplate,
    template='notification.pt',
    permission=Secret
)
def view_notification_details(
    self: CourseNotificationTemplate,
    request: FsiRequest
) -> RenderData:
    return {
        'layout': NotificationTemplateLayout(self, request)
    }


@FsiApp.form(
    model=CourseNotificationTemplate,
    template='form.pt',
    form=NotificationForm,
    name='edit',
    permission=Secret
)
def view_edit_notification(
    self: CourseNotificationTemplate,
    request: FsiRequest,
    form: NotificationForm
) -> RenderData | Response:

    if form.submitted(request):
        form.update_model(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.apply_model(self)
    layout = EditNotificationTemplateLayout(self, request)

    return {
        'title': layout.title,
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.html(
    model=CourseNotificationTemplate,
    template='mail_notification.pt',
    permission=Secret,
    name='embed'
)
def view_email_preview(
    self: CourseNotificationTemplate,
    request: FsiRequest
) -> RenderData:

    layout = MailLayout(self, request)

    return {
        'model': self,
        'layout': layout,
        'title': self.subject,
        'information': self.text_html,
        'attendee': request.attendee
    }


@FsiApp.form(
    model=CourseNotificationTemplate,
    permission=Secret,
    template='notification_template_send_form.pt',
    name='send',
    form=NotificationTemplateSendForm
)
def handle_send_notification(
    self: CourseNotificationTemplate,
    request: FsiRequest,
    form: NotificationTemplateSendForm
) -> RenderData | Response:

    layout = SendNotificationTemplateLayout(self, request)

    if form.submitted(request):
        assert form.recipients.data is not None
        recipients = list(form.recipients.data)
        course = self.course_event
        request = handle_send_email(
            self, request, recipients, show_sent_count=True
        )
        return request.redirect(request.link(course))

    return {
        'layout': layout,
        'form': form,
        'button_text': _('Send E-Mail Now'),
        'model': self,
    }
