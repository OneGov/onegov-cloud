import morepath

from onegov.ballot import Ballot, Vote
from onegov.core.security import Public, Private
from onegov.election_day import _, ElectionDayApp
from onegov.election_day.forms import DeleteForm, VoteForm
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.models import Manage


@ElectionDayApp.html(model=Vote, template='vote.pt', permission=Public)
def view_vote(self, request):

    layout = DefaultLayout(self, request)
    request.include('ballot_map')

    return {
        'vote': self,
        'layout': layout,
    }


@ElectionDayApp.json(model=Ballot, permission=Public, name='by-municipality')
def view_ballot_by_municipality(self, request):
    return self.percentage_by_municipality()


@ElectionDayApp.form(model=Manage, name='new-vote', template='form.pt',
                     permission=Private, form=VoteForm)
def create_vote(self, request, form):

    if form.submitted(request):
        vote = Vote()
        form.update_model(vote)
        request.app.session().add(vote)
        return morepath.redirect(request.link(Manage(request.app.session())))

    return {
        'layout': DefaultLayout(self, request),
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
        'layout': DefaultLayout(self, request),
        'form': form,
        'title': self.title,
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
        'layout': DefaultLayout(self, request),
        'form': form,
        'title': _("Confirmation"),
        'button_text': _("Delete vote"),
        'button_class': 'alert',
        'cancel': request.link(Manage(request.app.session()))
    }
