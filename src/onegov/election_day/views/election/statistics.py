from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import Election
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=Election,
    name='statistics',
    template='election/statistics.pt',
    permission=MaybePublic
)
def view_election_statistics(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    return {
        'election': self,
        'layout': ElectionLayout(self, request, 'statistics')
    }


@ElectionDayApp.html(
    model=Election,
    name='statistics-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_statistics_table(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" View for the standalone statistics table.  """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'election': self,
        'layout': ElectionLayout(self, request, 'statistics'),
        'type': 'election-table',
        'scope': 'statistics'
    }
