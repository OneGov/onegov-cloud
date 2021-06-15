from morepath import redirect
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.forms import TriggerNotificationsForm
from onegov.election_day.layouts import ManageLayout
from onegov.election_day.models import Principal


@ElectionDayApp.manage_form(
    model=Principal,
    name='trigger-notifications',
    form=TriggerNotificationsForm,
    template='manage/trigger_notifications.pt'
)
def view_trigger_notficiations(self, request, form):

    """ Trigger the notifications of the current election day. """

    layout = ManageLayout(self, request)
    session = request.session

    notifications = NotificationCollection(session)
    if form.submitted(request):
        notifications.trigger_summarized(
            request,
            form.election_models(session),
            form.vote_models(session),
            form.notifications.data
        )
        request.message(_("Notifications triggered."), 'success')
        return redirect(layout.manage_link)

    latest_date = form.latest_date(session)
    latest_date = layout.format_date(latest_date, 'date_long')

    warn = False
    last_notifications = {}
    for election in form.available_elections(session):
        last_notifications[election] = notifications.by_model(election, False)
        if notifications.by_model(election):
            warn = True
    for vote in form.available_votes(session):
        last_notifications[vote] = notifications.by_model(vote, False)
        if notifications.by_model(vote):
            warn = True

    callout = ''
    message = ''
    button_class = 'primary'
    if warn:
        callout = _(
            "There are no changes since the last time the notifications "
            "have been triggered!"
        )
        message = _(
            "Do you really want to retrigger the notfications?",
        )
        button_class = 'alert'

    return {
        'layout': layout,
        'form': form,
        'title': _("Trigger notifications"),
        'subtitle': _(
            "Elections and votes on ${date}",
            mapping={'date': latest_date}
        ),
        'cancel': layout.manage_link,
        'button_class': button_class,
        'callout': callout,
        'message': message,
        'last_notifications': last_notifications
    }
