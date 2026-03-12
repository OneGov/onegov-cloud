from __future__ import annotations

from collections import OrderedDict

from markupsafe import Markup


from onegov.activity import BookingPeriodCollection
from onegov.core.elements import BackLink
from onegov.core.html import html_to_text, sanitize_html
from onegov.core.security import Secret
from onegov.core.templates import render_template
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.forms import NotificationTemplateForm
from onegov.feriennet.forms import NotificationTemplateSendForm
from onegov.feriennet.layout import NotificationTemplateCollectionLayout
from onegov.feriennet.layout import NotificationTemplateLayout
from onegov.feriennet.models import NotificationTemplate
from onegov.feriennet.models.notification_template import TemplateVariables
from onegov.org.elements import DeleteLink, Link
from onegov.org.layout import DefaultMailLayout
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import EmailJsonDict, RenderData
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


def get_variables(request: FeriennetRequest) -> dict[str, str]:
    period = BookingPeriodCollection(request.session).active()
    variables = TemplateVariables(request, period).bound

    return OrderedDict(
        (token, variables[token].__doc__) for token in sorted(variables)
    )


@FeriennetApp.html(
    model=NotificationTemplateCollection,
    permission=Secret,
    template='notification_templates.pt')
def view_notification_templates(
    self: NotificationTemplateCollection,
    request: FeriennetRequest
) -> RenderData:

    layout = NotificationTemplateCollectionLayout(self, request)

    def get_links(notification: NotificationTemplate) -> Iterator[Link]:
        if not request.app.active_period:
            return

        yield Link(
            text=_('Edit'),
            url=request.link(notification, 'edit')
        )

        yield DeleteLink(
            text=_('Delete'),
            url=layout.csrf_protected_url(request.link(notification)),
            confirm=_('Do you really want to delete "${title}"?', mapping={
                'title': notification.subject,
            }),
            target=f'#{notification.id.hex}',
            yes_button_text=_('Delete Notification Template')
        )

        yield Link(
            text=_('Use Template'),
            url=request.link(notification, 'send')
        )

    return {
        'title': _('Notification Templates'),
        'layout': layout,
        'notifications': self.query(),
        'get_links': get_links,
    }


@FeriennetApp.form(
    model=NotificationTemplateCollection,
    permission=Secret,
    template='notification_template_form.pt',
    name='new',
    form=NotificationTemplateForm)
def view_notification_template_form(
    self: NotificationTemplateCollection,
    request: FeriennetRequest,
    form: NotificationTemplateForm
) -> RenderData | Response:

    title = _('New Notification Template')

    if form.submitted(request):
        self.add(
            subject=form.subject.data,
            text=form.text.data
        )

        request.success(_('Successfully added a new notification template'))
        return request.redirect(request.link(self))
    layout = NotificationTemplateCollectionLayout(self, request, title)
    layout.edit_mode = True

    return {
        'title': title,
        'layout': layout,
        'form': form,
        'variables': get_variables(request),
    }


@FeriennetApp.form(
    model=NotificationTemplate,
    permission=Secret,
    template='notification_template_form.pt',
    name='edit',
    form=NotificationTemplateForm)
def edit_notification(
    self: NotificationTemplate,
    request: FeriennetRequest,
    form: NotificationTemplateForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))

        return request.redirect(
            request.class_link(NotificationTemplateCollection))
    elif not request.POST:
        form.process(obj=self)

    layout = NotificationTemplateLayout(self, request)
    layout.edit_mode = True
    layout.editmode_links[1] = BackLink(attrs={'class': 'cancel-link'})

    return {
        'title': _('Edit'),
        'layout': layout,
        'form': form,
        'variables': get_variables(request)
    }


@FeriennetApp.view(
    model=NotificationTemplate,
    permission=Secret,
    request_method='DELETE')
def delete_notification(
    self: NotificationTemplate,
    request: FeriennetRequest
) -> None:

    request.assert_valid_csrf_token()

    NotificationTemplateCollection(request.session).delete(self)

    @request.after
    def remove_target(response: Response) -> None:
        response.headers.add('X-IC-Remove', 'true')


@FeriennetApp.form(
    model=NotificationTemplate,
    permission=Secret,
    template='notification_template_send_form.pt',
    name='send',
    form=NotificationTemplateSendForm
)
def handle_send_notification(
    self: NotificationTemplate,
    request: FeriennetRequest,
    form: NotificationTemplateSendForm
) -> RenderData | Response:

    period = BookingPeriodCollection(request.session).active()
    variables = TemplateVariables(request, period)
    layout = NotificationTemplateLayout(self, request)

    subject = variables.render(Markup(self.subject))  # nosec: B704
    message = variables.render(sanitize_html(self.text))

    if form.submitted(request):
        recipients = form.recipients

        if not recipients:
            request.alert(_('There are no recipients matching the selection'))
        else:
            content = render_template('mail_notification.pt', request, {
                'layout': DefaultMailLayout(self, request),
                'title': subject,
                'notification': message,
            })
            plaintext = html_to_text(content)

            def email_iter() -> Iterator[EmailJsonDict]:
                for recipient in recipients:
                    yield request.app.prepare_email(
                        receivers=(recipient, ),
                        subject=subject,
                        content=content,
                        plaintext=plaintext,
                        category='transactional'
                    )

                assert request.current_username is not None
                if request.current_username not in recipients:
                    yield request.app.prepare_email(
                        receivers=(request.current_username, ),
                        subject=subject,
                        content=content,
                        plaintext=plaintext,
                        category='transactional'
                    )

            request.app.send_transactional_email_batch(email_iter())
            self.last_sent = utcnow()

            request.success(_(
                'Successfully sent the e-mail to ${count} recipients',
                mapping={
                    'count': len(recipients)
                }
            ))

            return request.redirect(
                request.class_link(NotificationTemplateCollection))

    return {
        'title': _('Mailing'),
        'layout': layout,
        'form': form,
        'preview_subject': subject,
        'preview_body': message,
        'edit_link': request.return_here(request.link(self, 'edit')),
        'button_text': _('Send E-Mail Now'),
        'model': self,
        'period': form.period,
    }
