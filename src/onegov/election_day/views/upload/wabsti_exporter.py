from __future__ import annotations

import transaction

from base64 import b64decode
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_election_wabstic_majorz
from onegov.election_day.formats import import_election_wabstic_proporz
from onegov.election_day.formats import import_vote_wabstic
from onegov.election_day.forms import UploadWabstiMajorzElectionForm
from onegov.election_day.forms import UploadWabstiProporzElectionForm
from onegov.election_day.forms import UploadWabstiVoteForm
from onegov.election_day.models import DataSource
from onegov.election_day.models import Election
from onegov.election_day.models import Principal
from onegov.election_day.models import ProporzElection
from onegov.election_day.models import Vote
from onegov.election_day.views.upload import set_locale
from onegov.election_day.views.upload import translate_errors
from onegov.election_day.views.upload import unsupported_year_error
from webob.exc import HTTPForbidden


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.formats.imports.common import FileImportError
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.request import ElectionDayRequest


def authenticated_source(request: ElectionDayRequest) -> DataSource:
    try:
        token = b64decode(
            request.authorization[1]  # type:ignore
        ).decode('utf-8').split(':')[1]

        query = request.session.query(DataSource)
        query = query.filter(DataSource.token == token)
        return query.one()
    except Exception as exception:
        raise HTTPForbidden() from exception


@ElectionDayApp.json(
    model=Principal,
    name='upload-wabsti-vote',
    request_method='POST',
    permission=Public
)
def view_upload_wabsti_vote(
    self: Canton | Municipality,
    request: ElectionDayRequest
) -> RenderData:

    """ Upload vote results using the WabstiCExportert 2.2+.

    Example usage:
        curl http://localhost:8080/onegov_election_day/xx/upload-wabsti-vote
            --user :<token>
            --header "Accept-Language: de_CH"
            --form "sg_gemeinden=@SG_Gemeinden.csv"
            --form "sg_geschafte=@SG_Geschaefte.csv"

    """

    set_locale(request)

    data_source = authenticated_source(request)
    if (
        data_source.type != 'vote'
        or not all(item.vote for item in data_source.items)
    ):
        return {
            'status': 'error',
            'errors': {
                'data_source': [request.translate(_(
                    'The data source is not configured properly'
                ))]
            }
        }

    form = request.get_form(
        UploadWabstiVoteForm,
        model=self,
        csrf_support=False
    )
    if not form.validate():
        return {
            'status': 'error',
            'errors': form.errors
        }

    assert form.sg_geschaefte.data is not None
    assert form.sg_geschaefte.file is not None
    assert form.sg_gemeinden.data is not None
    assert form.sg_gemeinden.file is not None

    errors: dict[str, list[FileImportError]] = {}
    session = request.session
    archive = ArchivedResultCollection(session)
    for item in data_source.items:
        vote = item.item
        if not isinstance(vote, Vote):
            continue

        errors[vote.id] = []
        if not self.is_year_available(vote.date.year, False):
            errors[vote.id].append(unsupported_year_error(vote.date.year))
            continue

        assert item.number is not None
        assert item.district is not None

        errors[vote.id] = import_vote_wabstic(
            vote,
            self,
            item.number,
            item.district,
            form.sg_geschaefte.file,
            form.sg_geschaefte.data['mimetype'],
            form.sg_gemeinden.file,
            form.sg_gemeinden.data['mimetype']
        )
        if not errors[vote.id]:
            archive.update(vote, request)
            request.app.send_zulip(
                self.name,
                'New results available: [{}]({})'.format(
                    vote.title, request.link(vote)
                )
            )

    translate_errors(errors, request)

    if any(errors.values()):
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.flush()
        return {'status': 'success', 'errors': {}}


@ElectionDayApp.json(
    model=Principal,
    name='upload-wabsti-majorz',
    request_method='POST',
    permission=Public
)
def view_upload_wabsti_majorz(
    self: Canton | Municipality,
    request: ElectionDayRequest
) -> RenderData:
    """ Upload election results using the WabstiCExportert 2.2+.

    Example usage:
        curl http://localhost:8080/onegov_election_day/xx/upload-wabsti-majorz
            --user :<token>
            --header "Accept-Language: de_CH"
            --form "wm_gemeinden=@WM_Gemeinden.csv"
            --form "wm_kandidaten=@WM_Kandidaten.csv"
            --form "wm_kandidatengde=@WM_KandidatenGde.csv"
            --form "wm_wahl=@WM_Wahl.csv"
            --form "wmstatic_gemeinden=@WMStatic_Gemeinden.csv"

    """
    set_locale(request)

    data_source = authenticated_source(request)
    if (
        data_source.type != 'majorz'
        or not all(item.election for item in data_source.items)
    ):
        return {
            'status': 'error',
            'errors': {
                'data_source': [request.translate(_(
                    'The data source is not configured properly'
                ))]
            }
        }

    form = request.get_form(
        UploadWabstiMajorzElectionForm,
        model=self,
        i18n_support=True,
        csrf_support=False
    )
    if not form.validate():
        return {
            'status': 'error',
            'errors': form.errors
        }

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

    errors: dict[str, list[FileImportError]] = {}
    session = request.session
    archive = ArchivedResultCollection(session)
    for item in data_source.items:
        election = item.item
        if not isinstance(election, Election):
            continue

        errors[election.id] = []
        if not self.is_year_available(election.date.year, False):
            errors[election.id].append(
                unsupported_year_error(election.date.year)
            )
            continue

        assert item.number is not None
        assert item.district is not None

        errors[election.id] = import_election_wabstic_majorz(
            election,
            self,
            item.number,
            item.district,
            form.wm_wahl.file,
            form.wm_wahl.data['mimetype'],
            form.wmstatic_gemeinden.file,
            form.wmstatic_gemeinden.data['mimetype'],
            form.wm_gemeinden.file,
            form.wm_gemeinden.data['mimetype'],
            form.wm_kandidaten.file,
            form.wm_kandidaten.data['mimetype'],
            form.wm_kandidatengde.file,
            form.wm_kandidatengde.data['mimetype'],
        )
        if not errors[election.id]:
            archive.update(election, request)
            request.app.send_zulip(
                self.name,
                'New results available: [{}]({})'.format(
                    election.title, request.link(election)
                )
            )

    translate_errors(errors, request)

    if any(errors.values()):
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.flush()
        return {'status': 'success', 'errors': {}}


@ElectionDayApp.json(
    model=Principal,
    name='upload-wabsti-proporz',
    request_method='POST',
    permission=Public
)
def view_upload_wabsti_proporz(
    self: Canton | Municipality,
    request: ElectionDayRequest
) -> RenderData:
    """ Upload election results using the WabstiCExportert 2.2+.

    Example usage:
        curl http://localhost:8080/onegov_election_day/xx/upload-wabsti-proporz
            --user :<token>
            --header "Accept-Language: de_CH"
            --form "wp_gemeinden=@WP_Gemeinden.csv"
            --form "wp_kandidaten=@WP_Kandidaten.csv"
            --form "wp_kandidatengde=@WP_KandidatenGde.csv"
            --form "wp_listen=@WP_Listen.csv"
            --form "wp_listengde=@WP_ListenGde.csv"
            --form "wp_wahl=@WP_Wahl.csv"
            --form "wpstatic_gemeinden=@WPStatic_Gemeinden.csv"
            --form "wpstatic_kandidaten=@WPStatic_Kandidaten.csv"

    """
    set_locale(request)

    data_source = authenticated_source(request)
    if (
        data_source.type != 'proporz'
        or not all(item.election for item in data_source.items)
    ):
        return {
            'status': 'error',
            'errors': {
                'data_source': [request.translate(_(
                    'The data source is not configured properly'
                ))]
            }
        }

    form = request.get_form(
        UploadWabstiProporzElectionForm,
        model=self,
        csrf_support=False
    )
    if not form.validate():
        return {
            'status': 'error',
            'errors': form.errors
        }

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

    errors: dict[str, list[FileImportError]] = {}
    session = request.session
    archive = ArchivedResultCollection(session)
    for item in data_source.items:
        election = item.item
        if not isinstance(election, ProporzElection):
            continue

        errors[election.id] = []
        if not self.is_year_available(election.date.year, False):
            errors[election.id].append(
                unsupported_year_error(election.date.year)
            )
            continue

        assert item.number is not None

        errors[election.id] = import_election_wabstic_proporz(
            election,
            self,
            item.number,
            item.district,
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
        if not errors[election.id]:
            archive.update(election, request)
            request.app.send_zulip(
                self.name,
                'New results available: [{}]({})'.format(
                    election.title, request.link(election)
                )
            )

    translate_errors(errors, request)

    if any(errors.values()):
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.flush()
        return {'status': 'success', 'errors': {}}
