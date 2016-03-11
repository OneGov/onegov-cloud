""" The upload view. """
import transaction

from onegov.ballot import Election
from onegov.core.security import Private
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.forms import UploadElectionForm
from onegov.election_day.layout import ManageLayout
from onegov.election_day.models import Manage
from onegov.election_day.utils import (
    FileImportError,
    import_sesam_file,
    import_wabsti_file
)


@ElectionDayApp.form(model=Election, name='upload',
                     template='upload_election.pt', permission=Private,
                     form=UploadElectionForm)
def view_upload(self, request, form):

    result = {}

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
            municipalities = principal.municipalities[self.date.year]
            if form.type.data == 'sesam':
                result = import_sesam_file(
                    municipalities,
                    self,
                    form.results.raw_data[0].file,
                    form.results.data['mimetype']
                )
            else:
                connections = len(form.connections.data)
                stats = len(form.statistics.data)
                elected = len(form.elected.data)
                result = import_wabsti_file(
                    municipalities,
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
                if form.complete.data:
                    self.total_municipalities = self.counted_municipalities

    form.apply_model(self)

    if result:
        status = result['status']
    else:
        status = 'open'

    if status == 'error':
        transaction.abort()

    return {
        'layout': ManageLayout(self, request),
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': request.link(Manage(request.app.session())),
        'results': result,
        'status': status,
        'election': self
    }
