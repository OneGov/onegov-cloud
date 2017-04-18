import transaction

from base64 import b64decode
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.forms import UploadWabstiVoteForm
from onegov.election_day.forms import UploadWabstiMajorzElectionForm
from onegov.election_day.formats.vote.wabsti import \
    import_exporter_files as import_vote
from onegov.election_day.formats.election.wabsti.majorz import \
    import_exporter_files as import_majorz
from onegov.election_day.models import Principal
from onegov.election_day.models import DataSource
from webob.exc import HTTPForbidden


def authenticated_source(request):
    try:
        token = b64decode(
            request.authorization[1]
        ).decode('utf-8').split(':')[1]

        query = request.app.session().query(DataSource)
        query = query.filter(DataSource.token == token)
        return query.one()
    except:
        raise HTTPForbidden()


def interpolate_errors(errors):
    for key, values in errors.items():
        errors[key] = [{
            'message': value.error.interpolate(),
            'filename': value.filename,
            'line': value.line
        } for value in values]


@ElectionDayApp.json(model=Principal, name='upload-wabsti-vote',
                     permission=Public, request_method='POST')
def view_upload_wabsti_vote(self, request):
    """ Upload vote results using the WabstiCExportert 2.1.

    Example usage:
        curl
            --user :<token>
            --form "sg_gemeinden=@SG_Gemeinden.csv"
            http://localhost:8080/onegov_election_day/sg/upload-wabsti-vote
    """

    data_source = authenticated_source(request)

    if data_source.type != 'vote':
        return {
            'status': 'error',
            'errors': {
                'data_source': 'The data source is note configured properly'
            }
        }

    form = request.get_form(
        UploadWabstiVoteForm,
        model=self,
        i18n_support=False,
        csrf_support=False
    )
    if not form.validate():
        return {
            'status': 'error',
            'errors': form.errors
        }

    errors = {}
    session = request.app.session()
    archive = ArchivedResultCollection(session)
    for item in data_source.items:
        vote = item.item
        errors[vote.id] = []
        if not self.is_year_available(vote.date.year, self.use_maps):
            errors[vote.id].append({
                'message': 'The year is not yet supported'
            })
            continue

        entities = self.entities.get(vote.date.year, {})
        errors[vote.id] = import_vote(
            vote, item.district, item.number, entities,
            form.sg_gemeinden.raw_data[0].file,
            form.sg_gemeinden.data['mimetype']
        )
        if not errors[vote.id]:
            archive.update(vote, request)
            request.app.send_hipchat(
                self.name,
                'New results available: <a href="{}">{}</a>'.format(
                    request.link(vote), vote.title
                )
            )

    interpolate_errors(errors)

    if any(errors.values()):
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.invalidate()
        return {'status': 'success', 'errors': {}}


@ElectionDayApp.json(model=Principal, name='upload-wabsti-majorz',
                     permission=Public, request_method='POST')
def view_upload_wabsti_majorz(self, request):
    """ Upload election results using the WabstiCExportert 2.1.

    Example usage:
        curl
            --user :<token>
            --form "wmstatic_gemeinden=@WMStatic_Gemeinden.csv"
            --form "wm_gemeinden=@WM_Gemeinden.csv"
            --form "wm_kandidaten=@WM_Kandidaten.csv"
            --form "wm_kandidatengde=@WM_KandidatenGde.csv"
            http://localhost:8080/onegov_election_day/sg/upload-wabsti-majorz
    """

    data_source = authenticated_source(request)

    if data_source.type != 'majorz':
        return {
            'status': 'error',
            'errors': {
                'data_source': 'The data source is note configured properly'
            }
        }

    form = request.get_form(
        UploadWabstiMajorzElectionForm,
        model=self,
        i18n_support=False,
        csrf_support=False
    )
    if not form.validate():
        return {
            'status': 'error',
            'errors': form.errors
        }

    errors = {}
    session = request.app.session()
    archive = ArchivedResultCollection(session)
    for item in data_source.items:
        election = item.item

        errors[election.id] = []
        if not self.is_year_available(election.date.year, self.use_maps):
            errors[election.id].append({
                'message': 'The year is not yet supported'
            })
            continue

        entities = self.entities.get(election.date.year, {})
        errors[election.id] = import_majorz(
            election, item.district, item.number, entities,
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
            request.app.send_hipchat(
                self.name,
                'New results available: <a href="{}">{}</a>'.format(
                    request.link(election), election.title
                )
            )

    interpolate_errors(errors)

    if any(errors.values()):
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.invalidate()
        return {'status': 'success', 'errors': {}}
