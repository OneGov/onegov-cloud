""" The upload view. """
import transaction

from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_party_results
from onegov.election_day.forms import UploadPartyResultsForm
from onegov.election_day.layouts import ManageElectionCompoundsLayout
from onegov.election_day.layouts import ManageElectionsLayout


@ElectionDayApp.manage_form(
    model=Election,
    name='upload-party-results',
    template='upload_election.pt',
    form=UploadPartyResultsForm
)
def view_upload_election_party_results(self, request, form):

    """ Uploads party results. """

    errors = []

    status = 'open'
    if form.submitted(request):
        errors = import_party_results(
            self,
            form.parties.raw_data[0].file,
            form.parties.data['mimetype']
        )

        archive = ArchivedResultCollection(request.session)
        archive.update(self, request)

        if errors:
            status = 'error'
            transaction.abort()
        else:
            status = 'success'
            request.app.pages_cache.invalidate()
            request.app.send_zulip(
                request.app.principal.name,
                'New party results available: [{}]({})'.format(
                    self.title, request.link(self)
                )
            )

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


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='upload-party-results',
    template='upload_election.pt',
    form=UploadPartyResultsForm
)
def view_upload_election_compound_party_results(self, request, form):

    """ Uploads party results. """

    errors = []

    status = 'open'
    if form.submitted(request):
        errors = import_party_results(
            self,
            form.parties.raw_data[0].file,
            form.parties.data['mimetype']
        )

        archive = ArchivedResultCollection(request.session)
        archive.update(self, request)

        if errors:
            status = 'error'
            transaction.abort()
        else:
            status = 'success'
            request.app.pages_cache.invalidate()
            request.app.send_zulip(
                request.app.principal.name,
                'New party results available: [{}]({})'.format(
                    self.title, request.link(self)
                )
            )

    layout = ManageElectionCompoundsLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': layout.manage_model_link,
        'errors': errors,
        'status': status,
        'show_trigger': False,
        'election': self
    }
