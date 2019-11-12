from onegov.fsi import FsiApp
from onegov.fsi.collections.notification_template import \
    FsiNotificationTemplateCollection
from onegov.fsi.forms.notification import NotificationForm
from onegov.fsi.layouts.notification import NotificationTemplateLayout, \
    NotificationTemplateCollectionLayout, EditNotificationTemplateLayout
from onegov.fsi.models.notification_template import FsiNotificationTemplate
from onegov.fsi import _


@FsiApp.html(
    model=FsiNotificationTemplateCollection, template='notifications.pt')
def view_notifications(self, request):
    layout = NotificationTemplateCollectionLayout(self, request)
    self.auto_add_templates_if_not_existing()

    return {
        'notifications': self.query().all(),
        'layout': layout
    }


@FsiApp.html(
    model=FsiNotificationTemplate, template='notification.pt')
def view_notifications(self, request):
    return {
        'layout': NotificationTemplateLayout(self, request)
    }


@FsiApp.html(
    model=FsiNotificationTemplate,
    template='info_notification.pt',
    name='send')
def view_notifications(self, request):
    return {
        'layout': NotificationTemplateLayout(self, request)
    }


@FsiApp.form(
    model=FsiNotificationTemplate,
    template='form.pt',
    form=NotificationForm,
    name='edit'
)
def view_edit_notification(self, request, form):

    if form.submitted(request):
        form.update_model(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self))

    form.apply_model(self)
    layout = EditNotificationTemplateLayout(self, request)

    return {
        'title': layout.title,
        'model': self,
        'layout': layout,
        'form': form
    }

# @FsiApp.form(
#     model=FsiNotificationTemplate,
#     permission=Secret,
#     template='notification_template_send_form.pt',
#     name='send',
#     form=object)
# def handle_send_notification(self, request, form):
#
#     variables = TemplateVariables(request)
#     layout = NotificationTemplateLayout(self, request)
#
#     if form.submitted(request):
#         recipients = form.recipients
#
#         if not recipients:
#             request.alert(
#             _("There are no recipients matching the selection"))
#         else:
#             # current = request.current_username
#
#             # if current not in recipients:
#             #     recipients.add(current)
#
#             subject = variables.render(self.subject)
#             content = render_template('mail_notification.pt', request, {
#                 'layout': DefaultMailLayout(self, request),
#                 'title': subject,
#                 'notification': variables.render(self.text)
#             })
#             plaintext = html_to_text(content)
#
#             for recipient in recipients:
#                 request.app.send_marketing_email(
#                     receivers=(recipient, ),
#                     subject=subject,
#                     content=content,
#                     plaintext=plaintext,
#                 )
#
#             self.last_sent = utcnow()
#
#             request.success(_(
#                 "Successfully sent the e-mail to ${count} recipients",
#                 mapping={
#                     'count': len(recipients)
#                 }
#             ))
#
#             return request.redirect(
#                 request.class_link(NotificationTemplateCollection))
#
#     return {
#         'title': _("Mailing"),
#         'layout': layout,
#         'form': form,
#         'preview_subject': variables.render(self.subject),
#         'preview_body': variables.render(self.text),
#         'edit_link': request.return_here(request.link(self, 'edit')),
#         'button_text': _("Send E-Mail Now"),
#         'model': self,
#         'period': form.period,
#     }
