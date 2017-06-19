import transaction

from base64 import b64decode
from onegov.ballot.models import Election
from onegov.ballot.models import Vote
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_election_internal
from onegov.election_day.formats import import_party_results
from onegov.election_day.formats import import_vote_internal
from onegov.election_day.forms import UploadRestForm
from onegov.election_day.models import Principal
from onegov.election_day.models import UploadToken
from onegov.election_day.views.upload import set_locale
from onegov.election_day.views.upload import translate_errors
from onegov.election_day.views.upload import unsupported_year_error
from webob.exc import HTTPUnauthorized


def authenticate(request):
    try:
        token = b64decode(
            request.authorization[1]
        ).decode('utf-8').split(':')[1]

        request.app.session().query(UploadToken).filter_by(token=token).one()
    except:
        raise HTTPUnauthorized()


@ElectionDayApp.json(model=Principal, name='upload',
                     permission=Public, request_method='POST')
def view_upload_test(self, request):
    """ Upload election or vote results via REST using the internal format.

    Example usage:
        curl http://localhost:8080/onegov_election_day/xx/upload
            --user :<token>
            --header "Accept-Language: de_CH"
            --form "type=vote"
            --form "identifier=vote-against-something"
            --form "results=@results.csv"

    """
    set_locale(request)
    authenticate(request)

    status_code = None

    @request.after
    def set_status_code(response):
        if status_code:
            response.status_code = status_code

    errors = {}

    form = request.get_form(UploadRestForm, model=self, csrf_support=False)
    if not form.validate():
        status_code = 400
        return {
            'status': 'error',
            'errors': {
                key: [{'message': v} for v in value]
                for key, value in form.errors.items()
            }
        }

    # Check the ID
    session = request.app.session()
    item = session.query(
        Vote if form.type.data == 'vote' else Election
    ).filter_by(id=form.id.data).first()
    if not item:
        errors.setdefault('id', []).append(_("Invalid id"))

    # Check the type
    if item and form.type.data == 'parties':
        if item.type != 'proporz':
            errors.setdefault('id', []).append(
                _("Use an election based on proportional representation")
            )

    # Check if the year is supported
    if item:
        if not self.is_year_available(item.date.year, False):
            errors.setdefault('id', []).append(
                unsupported_year_error(item.date.year)
            )

    if not errors:
        entities = self.entities.get(item.date.year, {})
        file = form.results.raw_data[0].file
        mimetype = form.results.data['mimetype']

        err = []
        if form.type.data == 'vote':
            err = import_vote_internal(item, entities, file, mimetype)
        if form.type.data == 'election':
            err = import_election_internal(item, entities, file, mimetype)
        if form.type.data == 'parties':
            err = import_party_results(item, file, mimetype)
        if err:
            errors.setdefault('results', []).extend(err)

        if not errors:
            archive = ArchivedResultCollection(session)
            archive.update(item, request)
            request.app.send_hipchat(
                self.name,
                'New results available: <a href="{}">{}</a>'.format(
                    request.link(item), item.title
                )
            )

    translate_errors(errors, request)

    if errors:
        status_code = 400
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.invalidate()
        return {'status': 'success', 'errors': {}}
