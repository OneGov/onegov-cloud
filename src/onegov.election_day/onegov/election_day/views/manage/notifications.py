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
    template='form.pt',
    form=TriggerNotificationsForm
)
def view_trigger_notficiations(self, request, form):

    """ Trigger the notifications of the current election day. """

    layout = ManageLayout(self, request)
    session = request.session

    if form.submitted(request):
        notifications = NotificationCollection(session)
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

    return {
        'layout': layout,
        'form': form,
        'title': _("Trigger notifications"),
        'subtitle': _(
            "Elections and votes on ${date}",
            mapping={'date': latest_date}
        ),
        'cancel': layout.manage_link
    }
