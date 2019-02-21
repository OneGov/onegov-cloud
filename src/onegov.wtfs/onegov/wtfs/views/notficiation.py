from morepath import redirect
from onegov.wtfs import _
from onegov.wtfs import WtfsApp
from onegov.wtfs.collections import NotificationCollection
from onegov.wtfs.forms import NotificationForm
from onegov.wtfs.layouts import AddNotificationLayout
from onegov.wtfs.layouts import EditNotificationLayout
from onegov.wtfs.layouts import NotificationLayout
from onegov.wtfs.layouts import NotificationsLayout
from onegov.wtfs.models import Notification
from onegov.wtfs.security import AddModel
from onegov.wtfs.security import DeleteModel
from onegov.wtfs.security import EditModel
from onegov.wtfs.security import ViewModel


@WtfsApp.html(
    model=NotificationCollection,
    template='notifications.pt',
    permission=ViewModel
)
def view_notifications(self, request):
    """ View the list of notifications. """

    return {'layout': NotificationsLayout(self, request)}


@WtfsApp.form(
    model=NotificationCollection,
    name='add',
    template='form.pt',
    permission=AddModel,
    form=NotificationForm
)
def add_notification(self, request, form):
    """ Create a new notification. """

    layout = AddNotificationLayout(self, request)

    if form.submitted(request):
        notification = Notification.create(request)
        form.update_model(notification)
        request.message(_("Notification added."), 'success')
        return redirect(layout.success_url)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url
    }


@WtfsApp.html(
    model=Notification,
    template='notification.pt',
    permission=ViewModel
)
def view_notification(self, request):
    """ View a single notification. """

    return {'layout': NotificationLayout(self, request)}


@WtfsApp.form(
    model=Notification,
    name='edit',
    template='form.pt',
    permission=EditModel,
    form=NotificationForm
)
def edit_notification(self, request, form):
    """ Edit a notification. """

    layout = EditNotificationLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        request.message(_("Notification modified."), 'success')
        return redirect(layout.success_url)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'button_text': _("Save"),
        'cancel': layout.cancel_url,
    }


@WtfsApp.view(
    model=Notification,
    request_method='DELETE',
    permission=DeleteModel
)
def delete_notification(self, request):
    """ Delete a notification. """

    request.assert_valid_csrf_token()
    NotificationCollection(request.session).delete(self)
    request.message(_("Notification deleted."), 'success')
