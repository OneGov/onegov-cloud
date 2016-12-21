from onegov.core.security import Private
from onegov.feriennet import _, FeriennetApp
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.forms import NotificationTemplateForm
from onegov.feriennet.layout import NotificationTemplateLayout


@FeriennetApp.html(
    model=NotificationTemplateCollection,
    permission=Private,
    template='notification_templates.pt')
def view_notification_templates(self, request):

    return {
        'title': _("Notification Templates"),
        'layout': NotificationTemplateLayout(self, request),
        'notifications': self.query()
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

    return {
        'title': title,
        'layout': NotificationTemplateLayout(self, request, title),
        'form': form
    }
