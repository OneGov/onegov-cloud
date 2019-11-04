from onegov.core.security import Secret
from onegov.fsi import FsiApp
from onegov.fsi.models.notification_template import FsiNotificationTemplate


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
#             request.alert(_("There are no recipients matching the selection"))
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