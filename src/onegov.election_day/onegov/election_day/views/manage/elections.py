""" The manage views. """

import morepath

from onegov.ballot import Election, ElectionCollection
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.forms import ElectionForm
from onegov.election_day.layout import ManageElectionsLayout


@ElectionDayApp.manage_html(
    model=ElectionCollection,
    template='manage/elections.pt'
)
def view_elections(self, request):

    """ View a list of all elections. """

    return {
        'layout': ManageElectionsLayout(self, request),
        'title': _("Elections"),
        'elections': self.batch,
        'new_election': request.link(self, 'new-election')
    }


@ElectionDayApp.manage_form(
    model=ElectionCollection,
    name='new-election',
    form=ElectionForm
)
def create_election(self, request, form):

    """ Create a new election. """

    layout = ManageElectionsLayout(self, request)
    archive = ArchivedResultCollection(request.app.session())

    form.set_domain(request.app.principal)

    if form.submitted(request):
        election = Election()
        form.update_model(election)
        archive.add(election, request)
        request.message(_("Election added."), 'success')
        return morepath.redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Election"),
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
    archive = ArchivedResultCollection(request.app.session())

    form.set_domain(request.app.principal)

    if form.submitted(request):
        form.update_model(self)
        archive.update(self, request)
        request.message(_("Election modified."), 'success')
        return morepath.redirect(layout.manage_model_link)

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
    name='clear'
)
def clear_election(self, request, form):

    """ Clear the results of an election. """

    layout = ManageElectionsLayout(self, request)
    archive = ArchivedResultCollection(request.app.session())

    if form.submitted(request):
        archive.clear(self, request)
        request.message(_("Results deleted."), 'success')
        return morepath.redirect(layout.manage_model_link)

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
    name='delete'
)
def delete_election(self, request, form):

    """ Delete an existing election. """

    layout = ManageElectionsLayout(self, request)
    archive = ArchivedResultCollection(request.app.session())

    if form.submitted(request):
        archive.delete(self, request)
        request.message(_("Election deleted."), 'success')
        return morepath.redirect(layout.manage_model_link)

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
    name='trigger'
)
def trigger_election(self, request, form):

    """ Trigger the notifications related to an election. """

    session = request.app.session()
    notifications = NotificationCollection(session)
    layout = ManageElectionsLayout(self, request)

    if form.submitted(request):
        notifications.trigger(request, self)
        request.message(_("Notifications triggered."), 'success')
        return morepath.redirect(layout.manage_model_link)

    callout = None
    message = ''
    title = _("Trigger notifications")
    button_class = 'primary'

    if notifications.by_election(self):
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
        'subtitle': title,
        'callout': callout,
        'button_text': title,
        'button_class': button_class,
        'cancel': layout.manage_model_link
    }
