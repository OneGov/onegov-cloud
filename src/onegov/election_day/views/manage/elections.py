from morepath import redirect
from onegov.ballot import Election
from onegov.ballot import ElectionCollection
from onegov.core.utils import groupbylist
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.forms import ChangeIdForm
from onegov.election_day.forms import ElectionForm
from onegov.election_day.forms import TriggerNotificationForm
from onegov.election_day.layouts import ManageElectionsLayout
from onegov.election_day.layouts import MailLayout


@ElectionDayApp.manage_html(
    model=ElectionCollection,
    template='manage/elections.pt'
)
def view_elections(self, request):
    """ View a list of all elections. """

    years = [
        (
            year if year else _('All'),
            year == self.year,
            request.link(self.for_year(year))
        )
        for year in [None] + self.get_years()
    ]

    return {
        'layout': ManageElectionsLayout(self, request),
        'title': _("Elections"),
        'groups': groupbylist(self.batch, key=lambda election: election.date),
        'new_election': request.link(self, 'new-election'),
        'redirect_filters': {_('Year'): years},
    }


@ElectionDayApp.manage_form(
    model=ElectionCollection,
    name='new-election',
    form=ElectionForm
)
def create_election(self, request, form):
    """ Create a new election. """

    layout = ManageElectionsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        election = Election()
        form.update_model(election)
        archive.add(election, request)
        request.message(_("Election added."), 'success')
        return redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New election"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Election,
    name='edit',
    form=ElectionForm
)
def edit_election(self, request, form):
    """ Edit an existing election. """

    layout = ManageElectionsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        form.update_model(self)
        archive.update(self, request)
        request.message(_("Election modified."), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Edit election"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Election,
    name='change-id',
    form=ChangeIdForm
)
def change_vote_id(self, request, form):
    layout = ManageElectionsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        old = request.link(self)
        form.update_model(self)
        archive.update(self, request, old=old)
        request.message(_("Election modified."), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Change ID"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Election,
    name='clear'
)
def clear_election(self, request, form):
    """ Clear the results of an election. """

    layout = ManageElectionsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.clear(self, request)
        request.message(_("Results deleted."), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to clear all results of "${item}"?',
            mapping={
                'item': self.title
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Clear results"),
        'button_text': _("Clear results"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Election,
    name='clear-media'
)
def clear_election_media(self, request, form):
    """ Deletes alls SVGs and PDFs of this election. """

    layout = ManageElectionsLayout(self, request)

    if form.submitted(request):
        count = layout.clear_media()
        request.message(
            _('${count} files deleted.', mapping={'count': count}),
            'success'
        )
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    return {
        'callout': _(
            'Deletes all SVGs and PDFs. They are regenerated in the '
            'background and are available again in a few minutes.'
        ),
        'message': _(
            'Do you really want to clear all media of "${item}"?',
            mapping={
                'item': self.title
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Clear media"),
        'button_text': _("Clear media"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Election,
    name='delete'
)
def delete_election(self, request, form):
    """ Delete an existing election. """

    layout = ManageElectionsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.delete(self, request)
        request.message(_("Election deleted."), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${item}"?',
            mapping={
                'item': self.title
            }
        ),
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Delete election"),
        'button_text': _("Delete election"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Election,
    name='trigger',
    form=TriggerNotificationForm,
    template='manage/trigger_notification.pt'
)
def trigger_election(self, request, form):
    """ Trigger the notifications related to an election. """

    session = request.session
    notifications = NotificationCollection(session)
    layout = ManageElectionsLayout(self, request)

    if form.submitted(request):
        notifications.trigger(request, self, form.notifications.data)
        request.message(_("Notifications triggered."), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    callout = None
    message = ''
    title = _("Trigger notifications")
    button_class = 'primary'
    subject = MailLayout(None, request).subject(self)

    if notifications.by_model(self):
        callout = _(
            "There are no changes since the last time the notifications "
            "have been triggered!"
        )
        message = _(
            "Do you really want to retrigger the notfications?",
        )
        button_class = 'alert'

    return {
        'message': message,
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subject': subject,
        'subtitle': title,
        'callout': callout,
        'button_text': title,
        'button_class': button_class,
        'cancel': layout.manage_model_link,
        'last_notifications': notifications.by_model(self, False)
    }
