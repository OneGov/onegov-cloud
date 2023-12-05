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
from onegov.election_day.formats.imports.election.wabstic_proporz import (
    create_election_wabstic_proporz)
from onegov.election_day.forms.upload.wabsti_proporz import (
    CreateWabstiProporzElectionForm)
from onegov.election_day.models import Principal
from onegov.election_day.views.upload import set_locale, translate_errors
from onegov.election_day.views.upload.wabsti_exporter import (
    authenticated_source)


from typing import cast
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.types import DomainOfInfluence
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest


@ElectionDayApp.json(
    model=Principal,
    name='create-wabsti-proporz',
    request_method='POST',
    permission=Public
)
def view_create_wabsti_proporz(
    self: Principal,
    request: 'ElectionDayRequest'
) -> 'RenderData':

    set_locale(request)
    data_source = authenticated_source(request)

    # Get Additional params, if None then False/district
    create_compound = bool(request.params.get('create_compound'))
    pukelsheim = bool(request.params.get('pukelsheim'))
    domain_ = request.params.get('domain')
    domain: 'DomainOfInfluence'
    if domain_ in ('district', 'region', 'municipality'):
        domain = cast('DomainOfInfluence', domain_)
    else:
        domain = 'district'

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

    assert form.wp_wahl.data is not None
    assert form.wp_wahl.file is not None
    errors = create_election_wabstic_proporz(
        # TODO: Figure out if we want to use a discriminated union
        #       everywhere instead of using Principal, so the type
        #       checker can narrow based on type
        self,  # type:ignore[arg-type]
        request,
        data_source,
        form.wp_wahl.file,
        form.wp_wahl.data['mimetype'],
        create_compound=create_compound,
        pukelsheim=pukelsheim,
        domain=domain
    )
    translate_errors(errors, request)

    if any(errors):
        transaction.abort()
        return {'status': 'error', 'errors': errors}
    else:
        request.app.pages_cache.flush()
        return {'status': 'success', 'errors': {}}
