from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import ElectionsLayout
from onegov.election_day.utils import handle_headerless_params
from onegov.election_day.views.election import get_missing_entities
from onegov.election_day.views.election import get_candidate_electoral_results
from sqlalchemy.orm import object_session


@ElectionDayApp.html(model=Election, template='election/districts.pt',
                     name='districts', permission=Public)
def view_election_districts(self, request):
    """" The main view. """

    request.include('tablesorter')

    handle_headerless_params(request)

    session = object_session(self)

    return {
        'election': self,
        'layout': ElectionsLayout(self, request, 'districts'),
        'electoral': get_candidate_electoral_results(self, session),
        'missing_entities': get_missing_entities(self, request, session),
        'number_of_candidates': self.candidates.count()
    }
