"""

For compound elections, the election creation view creates:

- All election belonging to the one election compound
- The election compound that registers all these election
- The

"""
import transaction

from onegov.election_day import _
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.formats.election.wabstic_proporz import \
    create_election_wabstic_proporz
from onegov.election_day.forms.upload.wabsti_proporz import \
    CreateWabstiProporzElectionForm
from onegov.election_day.models import Principal
from onegov.election_day.views.upload import set_locale, translate_errors
from onegov.election_day.views.upload.wabsti_exporter import \
    authenticated_source


@ElectionDayApp.json(
    model=Principal,
    name='create-wabsti-proporz',
    request_method='POST',
    permission=Public
)
def view_create_wabsti_proporz(self, request):
    set_locale(request)
    data_source = authenticated_source(request)

    # Get Additional params, if None then False/district
    create_compound = bool(request.params.get('create_compound'))
    after_pukelsheim = bool(request.params.get('after_pukelsheim'))
    domain = {
        'district': 'district',
        'region': 'region',
        'municipality': 'municipality'
    }.get(request.params.get('domain'), 'district')

    if data_source.items.first():
        return {
            'status': 'error',
            'errors': {
                'data_source': [request.translate(_(
                    'This source has already elections assigned to it'
                ))]
            }
        }
    form = request.get_form(
        CreateWabstiProporzElectionForm,
        model=self,
        csrf_support=False
    )
    if not form.validate():
        return {
            'status': 'error',
            'errors': form.errors
        }

    errors = create_election_wabstic_proporz(
        self,
        request,
        data_source,
        form.wp_wahl.raw_data[0].file,
        form.wp_wahl.data['mimetype'],
        create_compound=create_compound,
        after_pukelsheim=after_pukelsheim,
        domain=domain
    )
    translate_errors(errors, request)

    if any(errors):
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.flush()
        return {'status': 'success', 'errors': {}}
