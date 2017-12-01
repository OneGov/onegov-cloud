from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.views.election import get_missing_entities
from sqlalchemy.orm import object_session


@ElectionDayApp.html(
    model=Election,
    name='statistics',
    template='election/statistics.pt',
    permission=Public
)
def view_election_statistics(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'statistics')

    return {
        'election': self,
        'layout': layout,
        'missing_entities': get_missing_entities(
            self, request, object_session(self)
        ),
    }
