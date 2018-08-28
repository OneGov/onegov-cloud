from morepath.request import Response
from onegov.core.security import Private
from onegov.core.security import Public
from onegov.swissvotes import _
from onegov.swissvotes import SwissvotesApp
from onegov.swissvotes.collections import SwissVoteCollection
from onegov.swissvotes.forms import SearchForm
from onegov.swissvotes.forms import UpdateDatasetForm
from onegov.swissvotes.layouts import UpdateVotesLayout
from onegov.swissvotes.layouts import VotesLayout


@SwissvotesApp.form(
    model=SwissVoteCollection,
    permission=Public,
    form=SearchForm,
    template='votes.pt'
)
def view_votes(self, request, form):
    if not form.errors:
        form.apply_model(self)

    return {
        'layout': VotesLayout(self, request),
        'form': form
    }


@SwissvotesApp.form(
    model=SwissVoteCollection,
    permission=Private,
    form=UpdateDatasetForm,
    template='form.pt',
    name='update'
)
def update_votes(self, request, form):
    layout = UpdateVotesLayout(self, request)

    if form.submitted(request):
        self.update(form.dataset.data)
        request.message(_("Dataset updated"), 'success')
        return request.redirect(layout.votes_link)

    return {
        'layout': layout,
        'form': form,
        'cancel': request.link(self)
    }


@SwissvotesApp.view(
    model=SwissVoteCollection,
    permission=Public,
    name='csv'
)
def export_votes(self, request):
    response = Response(
        content_type='text/csv',
        content_disposition='inline; filename=dataset.csv'
    )
    self.export(response.body_file)
    return response
