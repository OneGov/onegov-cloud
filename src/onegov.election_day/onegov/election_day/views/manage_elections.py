""" The manage views. """

import morepath

from onegov.ballot import Election, ElectionCollection
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import WebhookCollection
from onegov.election_day.forms import DeleteForm
from onegov.election_day.forms import ElectionForm
from onegov.election_day.forms import TriggerWebhookForm
from onegov.election_day.layout import ManageElectionsLayout


@ElectionDayApp.html(model=ElectionCollection, template='manage_elections.pt',
                     permission=Private)
def view_elections(self, request):

    return {
        'layout': ManageElectionsLayout(self, request),
        'title': _("Manage"),
        'elections': self.batch,
        'new_election': request.link(self, 'new-election'),
    }


@ElectionDayApp.form(model=ElectionCollection, name='new-election',
                     template='form.pt', permission=Private, form=ElectionForm)
def create_election(self, request, form):

    layout = ManageElectionsLayout(self, request)

    if form.submitted(request):
        election = Election()
        form.update_model(election)
        request.app.session().add(election)
        return morepath.redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Election"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.form(model=Election, name='edit', template='form.pt',
                     permission=Private, form=ElectionForm)
def edit_election(self, request, form):

    layout = ManageElectionsLayout(self, request)

    if form.submitted(request):
        form.update_model(self)
        return morepath.redirect(layout.manage_model_link)

    form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Edit"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.form(model=Election, name='delete', template='form.pt',
                     permission=Private, form=DeleteForm)
def delete_election(self, request, form):

    layout = ManageElectionsLayout(self, request)

    if form.submitted(request):
        request.app.session().delete(self)
        return morepath.redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${election}"?',
            mapping={
                'election': self.title
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


@ElectionDayApp.form(model=Election, name='trigger-webhooks',
                     template='form.pt', permission=Private,
                     form=TriggerWebhookForm)
def trigger_webhooks(self, request, form):

    session = request.app.session()
    webhooks = WebhookCollection(session)
    layout = ManageElectionsLayout(self, request)

    if form.submitted(request):
        for url in request.app.principal.webhooks:
            webhooks.add(url, self.last_result_change, election=self)
        # todo: trigger notification, add webhook entry
        return morepath.redirect(layout.manage_model_link)

    callout = None
    message = ''
    title = _("Trigger notifications")
    button_class = 'primary'

    for url in request.app.principal.webhooks:
        webhook = webhooks.by_election(self, url, self.last_result_change)
        if webhook is not None:
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
