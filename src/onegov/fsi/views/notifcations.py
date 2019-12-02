from arrow import utcnow
from onegov.core.html import html_to_text
from onegov.core.security import Secret, Private
from onegov.core.templates import render_template
from onegov.fsi import FsiApp
from onegov.fsi.collections.notification_template import \
    CourseNotificationTemplateCollection
from onegov.fsi.forms.notification import NotificationForm, \
    NotificationTemplateSendForm
from onegov.fsi.layouts.notification import NotificationTemplateLayout, \
    NotificationTemplateCollectionLayout, EditNotificationTemplateLayout, \
    MailLayout, \
    SendNotificationTemplateLayout
from onegov.fsi.models.course_notification_template import \
    CourseNotificationTemplate
from onegov.fsi import _


@FsiApp.html(
    model=CourseNotificationTemplateCollection,
    template='notifications.pt',
    permission=Secret
)
def view_notifications(self, request):
    layout = NotificationTemplateCollectionLayout(self, request)
    # This was a workaround and should be removed in the future
    self.auto_add_templates_if_not_existing()

    return {
        'layout': layout
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
        return request.redirect(request.link(self))

    form.apply_model(self)
    layout = EditNotificationTemplateLayout(self, request)
    layout.include_editor()

    return {
        'title': layout.title,
        'model': self,
        'layout': layout,
        'form': form,
        'button_text': _('Update')
    }


@FsiApp.form(
    model=CourseNotificationTemplate,
    permission=Private,
    template='notification_template_send_form.pt',
    name='send',
    form=NotificationTemplateSendForm)
def handle_send_notification(self, request, form):

    layout = SendNotificationTemplateLayout(self, request)
    content = render_template('mail_notification.pt', request, {
        'layout': MailLayout(self, request),
        'title': self.subject,
        'notification': self.text
    })
    plaintext = html_to_text(content)

    if form.submitted(request):
        recipients = list(form.recipients.data)

        if not recipients:
            request.alert(
            _("There are no recipients matching the selection"))

        else:
            if request.current_attendee.email not in recipients:
                recipients.append(request.current_attendee.email)

            for recipient in recipients:
                request.app.send_marketing_email(
                    receivers=(recipient, ),
                    subject=self.subject,
                    content=content,
                    plaintext=plaintext,
                )

            self.last_sent = utcnow()

            request.success(_(
                "Successfully sent the e-mail to ${count} recipients",
                mapping={
                    'count': len(recipients)
                }
            ))

            return request.redirect(
                request.link(self.course_event))

    return {
        'layout': layout,
        'form': form,
        'preview_subject': self.subject,
        'preview_body': self.text,
        'edit_link': request.return_here(request.link(self, 'edit')),
        'button_text': _("Send E-Mail Now"),
        'model': self,
    }
