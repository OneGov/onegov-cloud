from __future__ import annotations

from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.formats import export_vote_internal
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.models import Vote
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=Vote,
    name='data',
    template='vote/data.pt',
    permission=MaybePublic
)
def view_vote_data(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    layout = VoteLayout(self, request, 'data')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.json_file(
    model=Vote,
    name='data-json',
    permission=MaybePublic
)
def view_vote_data_as_json(
    self: Vote,
    request: ElectionDayRequest
) -> JSON_ro:
    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'data': export_vote_internal(self, sorted(request.app.locales)),
        'name': normalize_for_url(self.title[:60]) if self.title else ''
    }


@ElectionDayApp.csv_file(
    model=Vote,
    name='data-csv',
    permission=MaybePublic
)
def view_vote_data_as_csv(
    self: Vote,
    request: ElectionDayRequest
) -> RenderData:
    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'data': export_vote_internal(self, sorted(request.app.locales)),
        'name': normalize_for_url(self.title[:60]) if self.title else ''
    }
