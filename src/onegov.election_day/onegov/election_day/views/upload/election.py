""" The upload view. """
import transaction

from onegov.ballot import Election
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import FileImportError
from onegov.election_day.forms import UploadElectionForm
from onegov.election_day.layout import ManageElectionsLayout
from onegov.election_day.formats.election.onegov_ballot import (
    import_file as import_onegov_file
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

    result = {}

    # Remove wabsti and sesam for municipalities for the moment
    if request.app.principal.domain == 'municipality':
        form.file_format.choices = [
            choice for choice in form.file_format.choices
            if choice[0] != 'wabsti' and choice[0] != 'sesam'
        ]

    if form.submitted(request):
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, map_required=False):
            result = {
                'status': 'error',
                'errors': [
                    FileImportError(
                        _(
                            "The year ${year} is not yet supported",
                            mapping={'year': self.date.year}
                        )
                    )
                ]
            }
        else:
            entities = principal.entities[self.date.year]
            parties = len(form.parties.data)
            if form.file_format.data == 'internal':
                result = import_onegov_file(
                    entities,
                    self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype'],
                    form.parties.raw_data[0].file if parties else None,
                    form.parties.data['mimetype'] if parties else None
                )
            elif form.file_format.data == 'sesam':
                result = import_sesam_file(
                    entities,
                    self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype'],
                    form.parties.raw_data[0].file if parties else None,
                    form.parties.data['mimetype'] if parties else None
                )
                if self.type == 'majorz':
                    self.absolute_majority = form.majority.data
            elif form.file_format.data == 'wabsti':
                connections = len(form.connections.data)
                stats = len(form.statistics.data)
                elected = len(form.elected.data)
                result = import_wabsti_file(
                    entities,
                    self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype'],
                    form.connections.raw_data[0].file if connections else None,
                    form.connections.data['mimetype'] if connections else None,
                    form.elected.raw_data[0].file if elected else None,
                    form.elected.data['mimetype'] if elected else None,
                    form.statistics.raw_data[0].file if stats else None,
                    form.statistics.data['mimetype'] if stats else None,
                    form.parties.raw_data[0].file if parties else None,
                    form.parties.data['mimetype'] if parties else None
                )
                if self.type == 'majorz':
                    self.absolute_majority = form.majority.data
                if form.complete.data:
                    self.total_entities = self.counted_entities
            else:
                raise NotImplementedError("Unsupported import format")

            archive = ArchivedResultCollection(request.app.session())
            archive.update(self, request)

    form.apply_model(self)

    if result:
        status = result['status']
    else:
        status = 'open'

    if status == 'error':
        transaction.abort()

    if status == 'ok':
        request.app.pages_cache.invalidate()

    layout = ManageElectionsLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': layout.manage_model_link,
        'results': result,
        'status': status,
        'election': self
    }
