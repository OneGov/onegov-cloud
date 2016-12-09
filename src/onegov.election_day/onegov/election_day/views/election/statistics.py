from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import ElectionsLayout
from onegov.election_day.utils import handle_headerless_params
from onegov.election_day.views.election import get_missing_entities
from sqlalchemy.orm import object_session


@ElectionDayApp.html(model=Election, template='election/statistics.pt',
                     name='statistics', permission=Public)
def view_election_statistics(self, request):
    """" The main view. """

    request.include('tablesorter')

    handle_headerless_params(request)

    return {
        'election': self,
        'layout': ElectionsLayout(self, request, 'statistics'),
        'missing_entities': get_missing_entities(
            self, request, object_session(self)
        ),
    }
