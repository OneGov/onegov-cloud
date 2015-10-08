""" The manage views. """

import morepath

from onegov.ballot import Vote
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import DeleteForm, VoteForm
from onegov.election_day.layout import ManageLayout
from onegov.election_day.models import Manage


@ElectionDayApp.html(model=Manage, template='manage.pt', permission=Private)
def view_manage(self, request):
    """ Shows the manage interface. """

    return {
        'layout': ManageLayout(self, request),
        'title': _("Manage"),
        'votes': self.votes,
        'new_vote': request.link(self, 'new-vote')
    }


@ElectionDayApp.form(model=Manage, name='new-vote', template='form.pt',
                     permission=Private, form=VoteForm)
def create_vote(self, request, form):

    if form.submitted(request):
        vote = Vote()
        form.update_model(vote)
        request.app.session().add(vote)
        return morepath.redirect(request.link(Manage(request.app.session())))

    return {
        'layout': ManageLayout(self, request),
        'form': form,
        'title': _("New Vote"),
        'cancel': request.link(Manage(request.app.session()))
    }


@ElectionDayApp.form(model=Vote, name='edit', template='form.pt',
                     permission=Private, form=VoteForm)
def edit_vote(self, request, form):

    if form.submitted(request):
        form.update_model(self)
        return morepath.redirect(request.link(Manage(request.app.session())))

    form.apply_model(self)

    return {
        'layout': ManageLayout(self, request),
        'form': form,
        'title': self.title,
        'subtitle': _("Edit"),
        'cancel': request.link(Manage(request.app.session()))
    }


@ElectionDayApp.form(model=Vote, name='delete', template='form.pt',
                     permission=Private, form=DeleteForm)
def delete_vote(self, request, form):

    if form.submitted(request):
        request.app.session().delete(self)
        return morepath.redirect(request.link(Manage(request.app.session())))

    return {
        'message': _(
            'Do you really want to delete "${vote}"?',
            mapping={
                'vote': self.title
            }
        ),
        'layout': ManageLayout(self, request),
        'form': form,
        'title': self.title,
        'subtitle': _("Delete vote"),
        'button_text': _("Delete vote"),
        'button_class': 'alert',
        'cancel': request.link(Manage(request.app.session()))
    }
