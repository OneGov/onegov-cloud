from arrow import utcnow
from onegov.core.html import html_to_text
from onegov.core.security import Secret
from onegov.core.templates import render_template
from onegov.fsi import FsiApp
from onegov.fsi.collections.notification_template import \
    CourseNotificationTemplateCollection
from onegov.fsi.forms.notification import NotificationForm, \
    NotificationTemplateSendForm
from onegov.fsi.layouts.notification import NotificationTemplateLayout, \
    NotificationTemplateCollectionLayout, EditNotificationTemplateLayout, \
    MailLayout, SendNotificationTemplateLayout
from onegov.fsi.models import CourseAttendee
from onegov.fsi.models.course_notification_template import \
    CourseNotificationTemplate
from onegov.fsi import _


def handle_send_email(self, request, recipients, cc_to_sender=True,
                      show_sent_count=True, attachments=None):
    """Recipients must be a list of attendee id's or attendees"""

    if not recipients:
        request.alert(_("There are no recipients matching the selection"))
    else:
        att = request.attendee
        handle_attendees = isinstance(recipients[0], CourseAttendee)
        att_ref = att if handle_attendees else att.id
        if cc_to_sender and att_ref not in recipients:
            recipients = list(recipients)
            recipients.append(att if handle_attendees else att.id)

        mail_layout = MailLayout(self, request)

        def email_iter():
            for att_id in recipients:
                if handle_attendees:
                    attendee = att_id
                else:
                    attendee = request.session.query(
                        CourseAttendee).filter_by(id=att_id).one()

                content = render_template('mail_notification.pt', request, {
                    'layout': mail_layout,
                    'title': self.subject,
                    'information': self.text_html,
                    'attendee': attendee
                })
                plaintext = html_to_text(content)

                yield request.app.prepare_email(
                    receivers=(attendee.email, ),
                    subject=self.subject,
                    content=content,
                    plaintext=plaintext,
                    category='transactional',
                    attachments=attachments or ()
                )

        request.app.send_transactional_email_batch(email_iter())
        self.last_sent = utcnow()

        if show_sent_count:
            request.success(_(
                "Successfully sent the e-mail to ${count} recipients",
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
def view_notifications(self, request):
    layout = NotificationTemplateCollectionLayout(self, request)
    # This was a workaround and should be removed in the future
    self.auto_add_templates_if_not_existing()
    has_entries = self.query().first() and True or False

    return {
        'layout': layout,
        'has_entries': has_entries
    }


@FsiApp.html(
    model=CourseNotificationTemplate,
    template='notification.pt',
    permission=Secret
)
def view_notification_details(self, request):
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
def view_edit_notification(self, request, form):

    if form.submitted(request):
        form.update_model(self)
        request.success(_("Your changes were saved"))
        collection = CourseNotificationTemplateCollection(
            request.session, course_event_id=self.course_event.id)
        return request.redirect(request.link(collection))

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
    name='embed')
def view_email_preview(self, request):

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
    form=NotificationTemplateSendForm)
def handle_send_notification(self, request, form):

    layout = SendNotificationTemplateLayout(self, request)

    if form.submitted(request):
        recipients = list(form.recipients.data)
        course = self.course_event
        request = handle_send_email(
            self, request, recipients, show_sent_count=True
        )
        return request.redirect(
            request.link(course)
        )

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Send E-Mail Now"),
        'model': self,
    }
