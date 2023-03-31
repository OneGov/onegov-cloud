from morepath import redirect
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundCollection
from onegov.core.utils import groupbylist
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.forms import ChangeIdForm
from onegov.election_day.forms import ElectionCompoundForm
from onegov.election_day.forms import TriggerNotificationForm
from onegov.election_day.layouts import ManageElectionCompoundsLayout
from onegov.election_day.layouts import MailLayout


@ElectionDayApp.manage_html(
    model=ElectionCompoundCollection,
    template='manage/election_compounds.pt'
)
def view_election_compounds(self, request):
    """ View a list of all election compoundss. """

    years = [
        (
            year if year else _('All'),
            year == self.year,
            request.link(self.for_year(year))
        )
        for year in [None] + self.get_years()
    ]

    return {
        'layout': ManageElectionCompoundsLayout(self, request),
        'title': _("Compounds of elections"),
        'groups': groupbylist(self.batch, key=lambda items: items.date),
        'new_election_compound': request.link(self, 'new-election-compound'),
        'redirect_filters': {_('Year'): years},
    }


@ElectionDayApp.manage_form(
    model=ElectionCompoundCollection,
    name='new-election-compound',
    form=ElectionCompoundForm
)
def create_election_compound(self, request, form):
    """ Create a new election compound. """

    layout = ManageElectionCompoundsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        election_compound = ElectionCompound()
        form.update_model(election_compound)
        archive.add(election_compound, request)
        request.message(_("Compound added."), 'success')
        return redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New compound"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='edit',
    form=ElectionCompoundForm
)
def edit_election_compound(self, request, form):
    """ Edit an existing election compound. """

    layout = ManageElectionCompoundsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        form.update_model(self)
        archive.update(self, request)
        request.message(_("Compound modified."), 'success')
        request.app.pages_cache.flush()
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Edit compound"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='change-id',
    form=ChangeIdForm
)
def change_election_compound_id(self, request, form):
    layout = ManageElectionCompoundsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        old = request.link(self)
        form.update_model(self)
        archive.update(self, request, old=old)
        request.message(_("Compound modified."), 'success')
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
    model=ElectionCompound,
    name='clear'
)
def clear_election_compound(self, request, form):
    """ Clear the results of an election ompound. """

    layout = ManageElectionCompoundsLayout(self, request)
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
    model=ElectionCompound,
    name='clear-media'
)
def clear_election_compound_media(self, request, form):
    """ Deletes alls SVGs and PDFs of this election compound. """

    layout = ManageElectionCompoundsLayout(self, request)

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
    model=ElectionCompound,
    name='delete'
)
def delete_election_compound(self, request, form):
    """ Delete an existing election compound. """

    layout = ManageElectionCompoundsLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.delete(self, request)
        request.message(_("Compound deleted."), 'success')
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
        'subtitle': _("Delete compound"),
        'button_text': _("Delete compound"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='trigger',
    form=TriggerNotificationForm,
    template='manage/trigger_notification.pt'
)
def trigger_election(self, request, form):
    """ Trigger the notifications related to an election. """

    session = request.session
    notifications = NotificationCollection(session)
    layout = ManageElectionCompoundsLayout(self, request)

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
