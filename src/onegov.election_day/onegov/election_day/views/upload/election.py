""" The upload view. """
import transaction

from onegov.ballot import Election
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import FileImportError
from onegov.election_day.forms import UploadElectionForm
from onegov.election_day.forms import UploadElectionPartyResultsForm
from onegov.election_day.layout import ManageElectionsLayout
from onegov.election_day.formats.election import import_party_results_file
from onegov.election_day.formats.election.internal import (
    import_file as import_internal_file
)
from onegov.election_day.formats.election.wabsti import (
    import_file as import_wabsti_file
)
from onegov.election_day.formats.election.sesam import (
    import_file as import_sesam_file
)


@ElectionDayApp.form(model=Election, name='upload',
                     template='upload_election.pt', permission=Private,
                     form=UploadElectionForm)
def view_upload(self, request, form):

    errors = []

    # Remove wabsti and sesam for municipalities for the moment
    if request.app.principal.domain == 'municipality':
        form.file_format.choices = [
            choice for choice in form.file_format.choices
            if choice[0] != 'wabsti' and choice[0] != 'sesam'
        ]

    status = 'open'
    if form.submitted(request):
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, map_required=False):
            errors = [
                FileImportError(
                    _(
                        "The year ${year} is not yet supported",
                        mapping={'year': self.date.year}
                    )
                )
            ]
        else:
            entities = principal.entities[self.date.year]
            if form.file_format.data == 'internal':
                errors = import_internal_file(
                    entities,
                    self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype']
                )
            elif form.file_format.data == 'sesam':
                errors = import_sesam_file(
                    entities,
                    self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype']
                )
                if self.type == 'majorz':
                    self.absolute_majority = form.majority.data
            elif form.file_format.data == 'wabsti':
                connections = len(form.connections.data)
                stats = len(form.statistics.data)
                elected = len(form.elected.data)
                errors = import_wabsti_file(
                    entities,
                    self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype'],
                    form.connections.raw_data[0].file if connections else None,
                    form.connections.data['mimetype'] if connections else None,
                    form.elected.raw_data[0].file if elected else None,
                    form.elected.data['mimetype'] if elected else None,
                    form.statistics.raw_data[0].file if stats else None,
                    form.statistics.data['mimetype'] if stats else None
                )
                if self.type == 'majorz':
                    self.absolute_majority = form.majority.data
                if form.complete.data:
                    self.total_entities = self.counted_entities
            else:
                raise NotImplementedError("Unsupported import format")

            archive = ArchivedResultCollection(request.app.session())
            archive.update(self, request)

            if errors:
                status = 'error'
                transaction.abort()
            else:
                status = 'success'
                request.app.pages_cache.invalidate()
                request.app.send_hipchat(
                    request.app.principal.name,
                    'New results available: <a href="{}">{}</a>'.format(
                        request.link(self), self.title
                    )
                )

    form.apply_model(self)

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


@ElectionDayApp.form(model=Election, name='upload-party-results',
                     template='upload_election.pt', permission=Private,
                     form=UploadElectionPartyResultsForm)
def view_party_results_upload(self, request, form):

    errors = []

    status = 'open'
    if form.submitted(request):
        errors = import_party_results_file(
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
