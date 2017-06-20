""" The upload view. """
import transaction

from onegov.ballot import Election
from onegov.core.security import Private
from onegov.election_day import ElectionDayApp
from onegov.election_day.formats import import_party_results
from onegov.election_day.forms import UploadElectionPartyResultsForm
from onegov.election_day.layout import ManageElectionsLayout


@ElectionDayApp.form(model=Election, name='upload-party-results',
                     template='upload_election.pt', permission=Private,
                     form=UploadElectionPartyResultsForm)
def view_party_results_upload(self, request, form):

    errors = []

    status = 'open'
    if form.submitted(request):
        errors = import_party_results(
            self,
            form.parties.raw_data[0].file,
            form.parties.data['mimetype']
        )

        if errors:
            status = 'error'
            transaction.abort()
        else:
            status = 'success'
            request.app.pages_cache.invalidate()

    layout = ManageElectionsLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': layout.manage_model_link,
        'errors': errors,
        'status': status,
        'election': self
    }
