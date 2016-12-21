from onegov.core.security import Private
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.forms import NotificationTemplateForm
from onegov.feriennet.layout import NotificationTemplateLayout
from onegov.feriennet.models import NotificationTemplate
from onegov.org.elements import DeleteLink, Link


@FeriennetApp.html(
    model=NotificationTemplateCollection,
    permission=Private,
    template='notification_templates.pt')
def view_notification_templates(self, request):

    layout = NotificationTemplateLayout(self, request)

    def get_links(notification):
        yield Link(
            text=_("Edit"),
            url=request.link(notification, 'bearbeiten')
        )

        yield DeleteLink(
            text=_("Delete"),
            url=layout.csrf_protected_url(request.link(notification)),
            confirm=_('Do you really want to delete "${title}"?', mapping={
                'title': notification.subject,
            }),
            target='#{}'.format(notification.id.hex),
            yes_button_text=_("Delete Notification Template")
        )

    return {
        'title': _("Notification Templates"),
        'layout': layout,
        'notifications': self.query(),
        'get_links': get_links,
    }


@FeriennetApp.form(
    model=NotificationTemplateCollection,
    permission=Private,
    template='form.pt',
    name='neu',
    form=NotificationTemplateForm)
def view_notification_template_form(self, request, form):

    title = _("New Notification Template")

    if form.submitted(request):
        self.add(
            subject=form.subject.data,
            text=form.text.data
        )

        request.success(_("Successfully added a new notification template"))
        return request.redirect(request.link(self))

    layout = NotificationTemplateLayout(self, request, title)

    return {
        'title': title,
        'layout': layout,
        'form': form,
    }


@FeriennetApp.form(
    model=NotificationTemplate,
    permission=Private,
    template='form.pt',
    name='bearbeiten',
    form=NotificationTemplateForm)
def edit_notification(self, request, form):

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))

        return request.redirect(
            request.class_link(NotificationTemplateCollection))
    elif not request.POST:
        form.process(obj=self)

    title = _("Edit Notification Template")
    layout = NotificationTemplateLayout(self, request, title)

    return {
        'title': title,
        'layout': layout,
        'form': form
    }


@FeriennetApp.view(
    model=NotificationTemplate,
    permission=Private,
    request_method='DELETE')
def delete_notification(self, request):
    request.assert_valid_csrf_token()

    NotificationTemplateCollection(request.app.session()).delete(self)

    @request.after
    def remove_target(response):
        response.headers.add('X-IC-Remove', 'true')
