from morepath import redirect
from onegov.ballot import Vote
from onegov.ballot import VoteCollection
from onegov.core.utils import groupbylist
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.collections import NotificationCollection
from onegov.election_day.forms import TriggerNotificationForm
from onegov.election_day.forms import VoteForm
from onegov.election_day.layouts import ManageVotesLayout


@ElectionDayApp.manage_html(
    model=VoteCollection,
    template='manage/votes.pt',
)
def view_votes(self, request):
    """ View a list of all votes. """

    return {
        'layout': ManageVotesLayout(self, request),
        'title': _("Votes"),
        'groups': groupbylist(self.batch, key=lambda vote: vote.date),
        'new_vote': request.link(self, 'new-vote')
    }


@ElectionDayApp.manage_form(
    model=VoteCollection,
    name='new-vote',
    form=VoteForm
)
def create_vote(self, request, form):
    """ Create a new vote. """

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    form.set_domain(request.app.principal)

    if form.submitted(request):
        vote = Vote.get_polymorphic_class(form.vote_type.data, Vote)()
        form.update_model(vote)
        archive.add(vote, request)
        request.message(_("Vote added."), 'success')
        return redirect(layout.manage_model_link)

    return {
        'layout': layout,
        'form': form,
        'title': _("New vote"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Vote,
    name='edit',
    form=VoteForm
)
def edit_vote(self, request, form):
    """ Edit an existing vote. """

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    form.set_domain(request.app.principal)

    if form.submitted(request):
        form.update_model(self)
        archive.update(self, request)
        request.message(_("Vote modified."), 'success')
        return redirect(layout.manage_model_link)

    if not form.errors:
        form.apply_model(self)

    return {
        'layout': layout,
        'form': form,
        'title': self.title,
        'shortcode': self.shortcode,
        'subtitle': _("Edit vote"),
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Vote,
    name='clear'
)
def clear_vote(self, request, form):
    """ Clear the results of a vote. """

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.clear(self, request)
        request.message(_("Results deleted."), 'success')
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
    model=Vote,
    name='delete'
)
def delete_vote(self, request, form):
    """ Delete an existing vote. """

    layout = ManageVotesLayout(self, request)
    archive = ArchivedResultCollection(request.session)

    if form.submitted(request):
        archive.delete(self, request)
        request.message(_("Vote deleted."), 'success')
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
        'subtitle': _("Delete vote"),
        'button_text': _("Delete vote"),
        'button_class': 'alert',
        'cancel': layout.manage_model_link
    }


@ElectionDayApp.manage_form(
    model=Vote,
    name='trigger',
    form=TriggerNotificationForm
)
def trigger_vote(self, request, form):
    """ Trigger the notifications related to a vote. """

    session = request.session
    notifications = NotificationCollection(session)
    layout = ManageVotesLayout(self, request)

    if form.submitted(request):
        notifications.trigger(request, self, form.notifications.data)
        request.message(_("Notifications triggered."), 'success')
        return redirect(layout.manage_model_link)

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
