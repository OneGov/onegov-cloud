""" The manage views. """

import morepath

from onegov.ballot import Vote, VoteCollection
from onegov.core.security import Private
from onegov.core.utils import groupbylist
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.forms import DeleteForm
from onegov.election_day.forms import TriggerNotificationForm
from onegov.election_day.forms import VoteForm
from onegov.election_day.layout import ManageVotesLayout


@ElectionDayApp.html(model=VoteCollection, template='manage/votes.pt',
                     permission=Private)
def view_votes(self, request):

    return {
        'layout': ManageVotesLayout(self, request),
        'title': _("Manage"),
        'groups': groupbylist(self.batch, key=lambda vote: vote.date),
        'new_vote': request.link(self, 'new-vote')
    }


@ElectionDayApp.form(model=VoteCollection, name='new-vote', template='form.pt',
                     permission=Private, form=VoteForm)
def create_vote(self, request, form):

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.app.session())

    form.set_domain(request.app.principal)

    if form.submitted(request):
        vote = Vote()
        form.update_model(vote)
        archive.add(vote, request)
        return morepath.redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New Vote"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.form(model=Vote, name='edit', template='form.pt',
                     permission=Private, form=VoteForm)
def edit_vote(self, request, form):

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.app.session())

    form.set_domain(request.app.principal)

    if form.submitted(request):
        form.update_model(self)
        archive.update(self, request)
        return morepath.redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Edit"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.form(model=Vote, name='delete', template='form.pt',
                     permission=Private, form=DeleteForm)
def delete_vote(self, request, form):

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.app.session())

    if form.submitted(request):
        archive.delete(self, request)
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
        'subtitle': _("Delete vote"),
        'button_text': _("Delete vote"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.form(model=Vote, name='trigger', template='form.pt',
                     permission=Private, form=TriggerNotificationForm)
def trigger_notifications(self, request, form):

    session = request.app.session()
    notifications = NotificationCollection(session)
    layout = ManageVotesLayout(self, request)

    if form.submitted(request):
        notifications.trigger(request, self)
        return morepath.redirect(layout.manage_model_link)

    callout = None
    message = ''
    title = _("Trigger notifications")
    button_class = 'primary'

    if notifications.by_vote(self):
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
