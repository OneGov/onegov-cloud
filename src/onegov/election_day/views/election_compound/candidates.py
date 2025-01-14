from __future__ import annotations

from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.models import ElectionCompound
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election_compound import get_elected_candidates


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


def get_districts(
    model: ElectionCompound,
    layout: ElectionCompoundLayout
) -> dict[str, tuple[str, str, str]]:

    return {
        election.id: (
            election.domain_segment,
            layout.request.link(election),
            election.domain_supersegment,
        )
        for election in layout.model.elections
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='candidates',
    template='election_compound/candidates.pt',
    permission=MaybePublic
)
def view_election_compound_candidates(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    session = request.app.session()
    layout = ElectionCompoundLayout(self, request, 'candidates')

    return {
        'election_compound': self,
        'elected_candidates': get_elected_candidates(self, session).all(),
        'districts': get_districts(self, layout),
        'layout': layout
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='candidates-table',
    template='embed.pt',
    permission=MaybePublic
)
def view_election_statistics_table(
    self: ElectionCompound,
    request: ElectionDayRequest
) -> RenderData:
    """" View for the standalone statistics table.  """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    session = request.app.session()
    layout = ElectionCompoundLayout(self, request, 'candidates')

    return {
        'election_compound': self,
        'elected_candidates': get_elected_candidates(self, session).all(),
        'districts': get_districts(self, layout),
        'layout': layout,
        'type': 'election-compound-table',
        'scope': 'candidates'
    }
