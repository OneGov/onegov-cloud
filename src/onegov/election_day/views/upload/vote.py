""" The upload view. """
from __future__ import annotations

import transaction

from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_vote_internal
from onegov.election_day.formats import import_vote_wabstic
from onegov.election_day.forms import UploadVoteForm
from onegov.election_day.layouts import ManageVotesLayout
from onegov.election_day.models import Vote
from onegov.election_day.views.upload import unsupported_year_error


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.models import DataSourceItem
    from onegov.election_day.request import ElectionDayRequest


@ElectionDayApp.manage_form(
    model=Vote,
    name='upload',
    template='upload_vote.pt',
    form=UploadVoteForm
)
def view_upload(
    self: Vote,
    request: ElectionDayRequest,
    form: UploadVoteForm
) -> RenderData:
    """ Uploads votes results. """

    errors = []

    form.adjust(request.app.principal, self)

    status = 'open'
    map_available = True
    last_change = self.last_result_change
    if form.submitted(request):
        session = request.session
        principal = request.app.principal
        if not principal.is_year_available(self.date.year, False):
            errors = [unsupported_year_error(self.date.year)]
        else:
            map_available = principal.is_year_available(
                self.date.year, principal.use_maps
            )
            if form.file_format.data == 'internal':
                assert form.proposal.data is not None
                assert form.proposal.file is not None
                errors = import_vote_internal(
                    self,
                    principal,
                    form.proposal.file,
                    form.proposal.data['mimetype']
                )
            elif form.file_format.data == 'wabsti_c':
                assert form.sg_geschaefte.data is not None
                assert form.sg_geschaefte.file is not None
                assert form.sg_gemeinden.data is not None
                assert form.sg_gemeinden.file is not None
                source: DataSourceItem
                for source in self.data_sources:
                    assert source.number is not None
                    assert source.district is not None
                    errors.extend(
                        import_vote_wabstic(
                            self,
                            principal,
                            source.number,
                            source.district,
                            form.sg_geschaefte.file,
                            form.sg_geschaefte.data['mimetype'],
                            form.sg_gemeinden.file,
                            form.sg_gemeinden.data['mimetype']
                        )
                    )
            else:
                raise NotImplementedError('Unsupported import format')
            archive = ArchivedResultCollection(session)
            archive.update(self, request)

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

    layout = ManageVotesLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'shortcode': self.shortcode,
        'form': form,
        'cancel': layout.manage_model_link,
        'errors': errors,
        'status': status,
        'vote': self,
        'map_available': map_available,
        'last_change': last_change
    }
