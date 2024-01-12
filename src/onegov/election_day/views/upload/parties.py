""" The upload view. """
import transaction

from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_party_results_internal
from onegov.election_day.forms import UploadPartyResultsForm
from onegov.election_day.layouts import ManageElectionCompoundsLayout
from onegov.election_day.layouts import ManageElectionsLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest


@ElectionDayApp.manage_form(
    model=Election,  # FIXME: Shouldn't this be ProporzElection?
    name='upload-party-results',
    template='upload_election.pt',
    form=UploadPartyResultsForm
)
def view_upload_election_party_results(
    self: Election,
    request: 'ElectionDayRequest',
    form: UploadPartyResultsForm
) -> 'RenderData':
    """ Uploads party results. """

    errors = []

    status = 'open'
    last_change = self.last_result_change
    if form.submitted(request):
        assert form.parties.data is not None
        assert form.parties.file is not None
        errors = import_party_results_internal(
            self,  # type:ignore[arg-type]
            request.app.principal,
            form.parties.file,
            form.parties.data['mimetype'],
            request.app.locales,
            # FIXME: Should we assert that a default_locale is set?
            request.app.default_locale  # type:ignore[arg-type]
        )

        archive = ArchivedResultCollection(request.session)
        archive.update(self, request)

        if errors:
            status = 'error'
            transaction.abort()
        else:
            status = 'success'
            last_change = self.last_result_change
            request.app.pages_cache.flush()
            request.app.send_zulip(
                # FIXME: Should we assert that the principal name is set?
                request.app.principal.name,  # type:ignore[arg-type]
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
        'election': self,
        'last_change': last_change
    }


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='upload-party-results',
    template='upload_election.pt',
    form=UploadPartyResultsForm
)
def view_upload_election_compound_party_results(
    self: ElectionCompound,
    request: 'ElectionDayRequest',
    form: UploadPartyResultsForm
) -> 'RenderData':
    """ Uploads party results. """

    errors = []

    status = 'open'
    last_change = self.last_result_change
    if form.submitted(request):
        assert form.parties.data is not None
        assert form.parties.file is not None
        errors = import_party_results_internal(
            self,
            request.app.principal,
            form.parties.file,
            form.parties.data['mimetype'],
            request.app.locales,
            # FIXME: should we assert that default_locale is set?
            request.app.default_locale  # type:ignore[arg-type]
        )

        archive = ArchivedResultCollection(request.session)
        archive.update(self, request)

        if errors:
            status = 'error'
            transaction.abort()
        else:
            status = 'success'
            last_change = self.last_result_change
            request.app.pages_cache.flush()
            request.app.send_zulip(
                # FIXME: Should we assert that the principal name is set?
                request.app.principal.name,  # type:ignore[arg-type]
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
        'election': self,
        'last_change': last_change
    }
