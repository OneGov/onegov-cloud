""" The upload view. """
from __future__ import annotations

import transaction

from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_election_compound_internal
from onegov.election_day.forms import UploadElectionCompoundForm
from onegov.election_day.layouts import ManageElectionCompoundsLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.views.upload import unsupported_year_error


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest


@ElectionDayApp.manage_form(
    model=ElectionCompound,
    name='upload',
    template='upload_election.pt',
    form=UploadElectionCompoundForm
)
def view_upload_election_compound(
    self: ElectionCompound,
    request: ElectionDayRequest,
    form: UploadElectionCompoundForm
) -> RenderData:
    """ Upload results of a election compound. """

    errors = []

    status = 'open'
    last_change = self.last_result_change
    if form.submitted(request):
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, map_required=False):
            errors = [unsupported_year_error(self.date.year)]
        else:
            if form.file_format.data == 'internal':
                assert form.results.data is not None
                assert form.results.file is not None
                errors = import_election_compound_internal(
                    self,
                    principal,
                    form.results.file,
                    form.results.data['mimetype']
                )
            else:
                raise NotImplementedError('Unsupported import format')

            archive = ArchivedResultCollection(request.session)
            archive.update(self, request)
            for election in self.elections:
                archive.update(election, request)

            if errors:
                status = 'error'
                transaction.abort()
            else:
                status = 'success'
                last_change = self.last_result_change
                request.app.pages_cache.flush()
                request.app.send_zulip(
                    request.app.principal.name,
                    'New results available: [{}]({})'.format(
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
        'election': self,
        'last_change': last_change
    }
