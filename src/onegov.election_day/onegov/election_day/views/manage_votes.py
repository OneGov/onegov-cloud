""" The manage views. """

import morepath

from onegov.ballot import Vote, VoteCollection
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import DeleteForm, VoteForm
from onegov.election_day.layout import ManageVotesLayout


@ElectionDayApp.html(model=VoteCollection, template='manage_votes.pt',
                     permission=Private)
def view_votes(self, request):

    return {
        'layout': ManageVotesLayout(self, request),
        'title': _("Manage"),
        'votes': self.batch,
        'new_vote': request.link(self, 'new-vote'),
    }


@ElectionDayApp.form(model=VoteCollection, name='new-vote', template='form.pt',
                     permission=Private, form=VoteForm)
def create_vote(self, request, form):

    layout = ManageVotesLayout(self, request)

    if form.submitted(request):
        vote = Vote()
        form.update_model(vote)
        request.app.session().add(vote)
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


@ElectionDayApp.form(model=Vote, name='delete', template='form.pt',
                     permission=Private, form=DeleteForm)
def delete_vote(self, request, form):

    layout = ManageVotesLayout(self, request)

    if form.submitted(request):
        request.app.session().delete(self)
        return morepath.redirect(layout.manage_model_link)

    return {
        'message': _(
            'Do you really want to delete "${vote}"?',
            mapping={
                'vote': self.title
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
