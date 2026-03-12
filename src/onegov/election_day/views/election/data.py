from __future__ import annotations

from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.formats import export_election_internal
from onegov.election_day.formats import export_parties_internal
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.models import Election
from onegov.election_day.security import MaybePublic
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election import get_connection_results_api
from webob.exc import HTTPNotFound


from typing import cast
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.election_day.models import ProporzElection
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.html(
    model=Election,
    name='data',
    template='election/data.pt',
    permission=MaybePublic
)
def view_election_data(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """" The main view. """

    layout = ElectionLayout(self, request, 'data')

    return {
        'election': self,
        'layout': layout
    }


@ElectionDayApp.json_file(
    model=Election,
    name='data-json',
    permission=MaybePublic
)
def view_election_data_as_json(
    self: Election,
    request: ElectionDayRequest
) -> JSON_ro:
    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'data': export_election_internal(self, sorted(request.app.locales)),
        'name': normalize_for_url(self.title[:60]) if self.title else ''
    }


@ElectionDayApp.csv_file(
    model=Election,
    name='data-csv',
    permission=MaybePublic
)
def view_election_data_as_csv(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:
    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'data': export_election_internal(self, sorted(request.app.locales)),
        'name': normalize_for_url(self.title[:60]) if self.title else ''
    }


@ElectionDayApp.json_file(
    model=Election,
    name='data-parties-json',
    permission=MaybePublic
)
def view_election_parties_data_as_json(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:

    """ View the raw parties data as JSON. """

    if not self.type == 'proporz':
        raise HTTPNotFound()

    self = cast('ProporzElection', self)

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    assert request.app.default_locale

    return {
        'data': export_parties_internal(
            self,
            locales=sorted(request.app.locales),
            default_locale=request.app.default_locale,
            json_serializable=True
        ),
        'name': normalize_for_url(
            '{}-{}'.format(
                normalize_for_url(self.title[:50]) if self.title else '',
                request.translate(_('Parties')).lower()
            )
        )
    }


@ElectionDayApp.csv_file(
    model=Election,
    name='data-parties-csv',
    permission=MaybePublic
)
def view_election_parties_data_as_csv(
    self: Election,
    request: ElectionDayRequest
) -> RenderData:

    """ View the raw parties data as CSV. """

    if not self.type == 'proporz':
        raise HTTPNotFound()

    self = cast('ProporzElection', self)

    @request.after
    def add_last_modified(response: Response) -> None:
        add_last_modified_header(response, self.last_modified)

    assert request.app.default_locale

    return {
        'data': export_parties_internal(
            self,
            locales=sorted(request.app.locales),
            default_locale=request.app.default_locale,
        ),
        'name': normalize_for_url(
            '{}-{}'.format(
                normalize_for_url(self.title[:50]) if self.title else '',
                request.translate(_('Parties')).lower()
            )
        )
    }


@ElectionDayApp.json(
    model=Election,
    name='data-list-connections',
    permission=MaybePublic
)
def view_election_aggregated_connections_data(
    self: Election,
    request: ElectionDayRequest
) -> JSON_ro:

    """" View the list connections as JSON. """

    return get_connection_results_api(self, request.session)
