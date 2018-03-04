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
from onegov.election_day.models import Principal
from onegov.election_day.views.upload import set_locale
from onegov.election_day.views.upload import translate_errors
from onegov.election_day.views.upload import unsupported_year_error
from webob.exc import HTTPForbidden


def authenticated_source(request):
    try:
        token = b64decode(
            request.authorization[1]
        ).decode('utf-8').split(':')[1]

        query = request.session.query(DataSource)
        query = query.filter(DataSource.token == token)
        return query.one()
    except Exception:
        raise HTTPForbidden()


@ElectionDayApp.json(
    model=Principal,
    name='upload-wabsti-vote',
    request_method='POST',
    permission=Public
)
def view_upload_wabsti_vote(self, request):

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
        data_source.type != 'vote' or
        not all((item.vote for item in data_source.items))
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

    errors = {}
    session = request.session
    archive = ArchivedResultCollection(session)
    for item in data_source.items:
        vote = item.item
        if not vote:
            continue

        errors[vote.id] = []
        if not self.is_year_available(vote.date.year, False):
            errors[vote.id].append(unsupported_year_error(vote.date.year))
            continue

        errors[vote.id] = import_vote_wabstic(
            vote, self, item.number, item.district,
            form.sg_geschaefte.raw_data[0].file,
            form.sg_geschaefte.data['mimetype'],
            form.sg_gemeinden.raw_data[0].file,
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
        request.app.pages_cache.invalidate()
        return {'status': 'success', 'errors': {}}


@ElectionDayApp.json(
    model=Principal,
    name='upload-wabsti-majorz',
    request_method='POST',
    permission=Public
)
def view_upload_wabsti_majorz(self, request):
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
        data_source.type != 'majorz' or
        not all((item.election for item in data_source.items))
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

    errors = {}
    session = request.session
    archive = ArchivedResultCollection(session)
    for item in data_source.items:
        election = item.item
        if not election:
            continue

        errors[election.id] = []
        if not self.is_year_available(election.date.year, False):
            errors[election.id].append(
                unsupported_year_error(election.date.year)
            )
            continue

        errors[election.id] = import_election_wabstic_majorz(
            election, self, item.number, item.district,
            form.wm_wahl.raw_data[0].file,
            form.wm_wahl.data['mimetype'],
            form.wmstatic_gemeinden.raw_data[0].file,
            form.wmstatic_gemeinden.data['mimetype'],
            form.wm_gemeinden.raw_data[0].file,
            form.wm_gemeinden.data['mimetype'],
            form.wm_kandidaten.raw_data[0].file,
            form.wm_kandidaten.data['mimetype'],
            form.wm_kandidatengde.raw_data[0].file,
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
        request.app.pages_cache.invalidate()
        return {'status': 'success', 'errors': {}}


@ElectionDayApp.json(
    model=Principal,
    name='upload-wabsti-proporz',
    request_method='POST',
    permission=Public
)
def view_upload_wabsti_proporz(self, request):
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
        data_source.type != 'proporz' or
        not all((item.election for item in data_source.items))
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

    errors = {}
    session = request.session
    archive = ArchivedResultCollection(session)
    for item in data_source.items:
        election = item.item
        if not election:
            continue

        errors[election.id] = []
        if not self.is_year_available(election.date.year, False):
            errors[election.id].append(
                unsupported_year_error(election.date.year)
            )
            continue

        errors[election.id] = import_election_wabstic_proporz(
            election, self, item.number, item.district,
            form.wp_wahl.raw_data[0].file,
            form.wp_wahl.data['mimetype'],
            form.wpstatic_gemeinden.raw_data[0].file,
            form.wpstatic_gemeinden.data['mimetype'],
            form.wp_gemeinden.raw_data[0].file,
            form.wp_gemeinden.data['mimetype'],
            form.wp_listen.raw_data[0].file,
            form.wp_listen.data['mimetype'],
            form.wp_listengde.raw_data[0].file,
            form.wp_listengde.data['mimetype'],
            form.wpstatic_kandidaten.raw_data[0].file,
            form.wpstatic_kandidaten.data['mimetype'],
            form.wp_kandidaten.raw_data[0].file,
            form.wp_kandidaten.data['mimetype'],
            form.wp_kandidatengde.raw_data[0].file,
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
        request.app.pages_cache.invalidate()
        return {'status': 'success', 'errors': {}}
