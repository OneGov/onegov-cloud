""" The upload view. """
from __future__ import annotations

import morepath
import transaction

from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_election_internal_majorz
from onegov.election_day.formats import import_election_internal_proporz
from onegov.election_day.formats import import_election_wabstic_majorz
from onegov.election_day.formats import import_election_wabstic_proporz
from onegov.election_day.forms import UploadMajorzElectionForm
from onegov.election_day.forms import UploadProporzElectionForm
from onegov.election_day.layouts import ManageElectionsLayout
from onegov.election_day.models import Election
from onegov.election_day.models import ProporzElection
from onegov.election_day.views.upload import unsupported_year_error


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.models import DataSourceItem
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.manage_html(
    model=Election,
    name='upload'
)
def view_upload_election(
    self: Election,
    request: ElectionDayRequest
) -> Response:
    """ Upload results of an election.

    Redirects to the majorz or proporz upload view.

    """

    if self.type == 'majorz':
        return morepath.redirect(request.link(self, 'upload-majorz'))
    return morepath.redirect(request.link(self, 'upload-proporz'))


@ElectionDayApp.manage_form(
    model=Election,
    name='upload-majorz',
    template='upload_election.pt',
    form=UploadMajorzElectionForm,
)
def view_upload_majorz_election(
    self: Election,
    request: ElectionDayRequest,
    form: UploadMajorzElectionForm
) -> RenderData:
    """ Upload results of a majorz election. """

    assert self.type == 'majorz'

    errors = []

    form.adjust(request.app.principal, self)

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
                errors = import_election_internal_majorz(
                    self,
                    principal,
                    form.results.file,
                    form.results.data['mimetype']
                )
            elif form.file_format.data == 'wabsti_c':
                source: DataSourceItem
                for source in self.data_sources:
                    assert source.district is not None
                    assert source.number is not None
                    assert form.wm_wahl.data is not None
                    assert form.wm_wahl.file is not None
                    assert form.wmstatic_gemeinden.data is not None
                    assert form.wmstatic_gemeinden.file is not None
                    assert form.wm_gemeinden.data is not None
                    assert form.wm_gemeinden.file is not None
                    assert form.wm_kandidaten.data is not None
                    assert form.wm_kandidaten.file is not None
                    assert form.wm_kandidatengde.data is not None
                    assert form.wm_kandidatengde.file is not None
                    errors.extend(
                        import_election_wabstic_majorz(
                            self,
                            principal,
                            source.number,
                            source.district,
                            form.wm_wahl.file,
                            form.wm_wahl.data['mimetype'],
                            form.wmstatic_gemeinden.file,
                            form.wmstatic_gemeinden.data['mimetype'],
                            form.wm_gemeinden.file,
                            form.wm_gemeinden.data['mimetype'],
                            form.wm_kandidaten.file,
                            form.wm_kandidaten.data['mimetype'],
                            form.wm_kandidatengde.file,
                            form.wm_kandidatengde.data['mimetype']
                        )
                    )
            else:
                raise NotImplementedError('Unsupported import format')

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
                    request.app.principal.name,
                    'New results available: '
                    f'[{self.title}]({request.link(self)})'
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
    model=ProporzElection,
    name='upload-proporz',
    template='upload_election.pt',
    form=UploadProporzElectionForm
)
def view_upload_proporz_election(
    self: ProporzElection,
    request: ElectionDayRequest,
    form: UploadProporzElectionForm
) -> RenderData:
    """ Upload results of a proproz election. """

    assert self.type == 'proporz'

    errors = []

    form.adjust(request.app.principal, self)

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
                errors = import_election_internal_proporz(
                    self,
                    principal,
                    form.results.file,
                    form.results.data['mimetype']
                )
            elif form.file_format.data == 'wabsti_c':
                source: DataSourceItem
                for source in self.data_sources:
                    assert source.number is not None
                    assert form.wp_wahl.data is not None
                    assert form.wp_wahl.file is not None
                    assert form.wpstatic_gemeinden.data is not None
                    assert form.wpstatic_gemeinden.file is not None
                    assert form.wp_gemeinden.data is not None
                    assert form.wp_gemeinden.file is not None
                    assert form.wp_listen.data is not None
                    assert form.wp_listen.file is not None
                    assert form.wp_listengde.data is not None
                    assert form.wp_listengde.file is not None
                    assert form.wpstatic_kandidaten.data is not None
                    assert form.wpstatic_kandidaten.file is not None
                    assert form.wp_kandidaten.data is not None
                    assert form.wp_kandidaten.file is not None
                    assert form.wp_kandidatengde.data is not None
                    assert form.wp_kandidatengde.file is not None
                    errors.extend(
                        import_election_wabstic_proporz(
                            self,
                            principal,
                            source.number,
                            source.district,
                            form.wp_wahl.file,
                            form.wp_wahl.data['mimetype'],
                            form.wpstatic_gemeinden.file,
                            form.wpstatic_gemeinden.data['mimetype'],
                            form.wp_gemeinden.file,
                            form.wp_gemeinden.data['mimetype'],
                            form.wp_listen.file,
                            form.wp_listen.data['mimetype'],
                            form.wp_listengde.file,
                            form.wp_listengde.data['mimetype'],
                            form.wpstatic_kandidaten.file,
                            form.wpstatic_kandidaten.data['mimetype'],
                            form.wp_kandidaten.file,
                            form.wp_kandidaten.data['mimetype'],
                            form.wp_kandidatengde.file,
                            form.wp_kandidatengde.data['mimetype'],
                        )
                    )
            else:
                raise NotImplementedError('Unsupported import format')

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
                    request.app.principal.name,
                    'New results available: '
                    f'[{self.title}]({request.link(self)})'
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
