from collections import defaultdict
from morepath import redirect
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.schemas import BallotEntityResultSchema
from onegov.election_day.schemas import BallotResultSchema
from onegov.election_day.schemas import BallotSchema
from onegov.election_day.schemas import BallotTotalResultSchema
from onegov.election_day.schemas import DataSchema
from onegov.election_day.schemas import ProgressSchema
from onegov.election_day.schemas import TitleSchema
from onegov.election_day.schemas import VoteResultsSchema
from onegov.election_day.schemas import VoteSchema
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_vote_summary

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import JSONObject
    from onegov.core.types import RenderData
    from onegov.election_day.request import ElectionDayRequest
    from webob.response import Response


@ElectionDayApp.view(
    model=Vote,
    request_method='HEAD',
    permission=Public
)
def view_vote_head(
    self: Vote,
    request: 'ElectionDayRequest'
) -> None:

    @request.after
    def add_headers(response: 'Response') -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)


@ElectionDayApp.html(
    model=Vote,
    permission=Public
)
def view_vote(
    self: Vote,
    request: 'ElectionDayRequest'
) -> 'Response':
    """" The main view. """

    return redirect(VoteLayout(self, request).main_view)


@ElectionDayApp.json(
    model=Vote,
    name='json',
    permission=Public
)
def view_vote_json(
    self: Vote,
    request: 'ElectionDayRequest'
) -> 'JSON_ro':
    """" The main view as JSON. """

    last_modified = self.last_modified
    assert last_modified is not None

    @request.after
    def add_headers(response: 'Response') -> None:
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    embed = defaultdict(list)
    media: 'JSONObject' = {}
    layout = VoteLayout(self, request)
    layout.last_modified = last_modified
    if layout.pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    if layout.show_map:
        media['maps'] = maps = {}
        for tab in (
            'entities',
            'proposal-entities',
            'counter-proposal-entities',
            'tie-breaker-entities',
            'districts',
            'proposal-districts',
            'counter-proposal-districts',
            'tie-breaker-districts'
        ):
            layout = VoteLayout(self, request, tab)
            layout.last_modified = last_modified
            if layout.visible:
                embed[tab].append(layout.map_link)
                if layout.svg_path:
                    maps[tab] = layout.svg_link

    embed['entities'].append(request.link(self, name='vote-header-widget'))

    for tab in layout.tabs_with_embedded_tables:
        layout = VoteLayout(self, request, tab)
        if layout.visible:
            embed[tab].append(layout.table_link())

    counted = self.counted
    return VoteSchema(
        completed=self.completed,
        date=self.date.isoformat(),
        domain=self.domain,
        last_modified=last_modified.isoformat(),
        progress=ProgressSchema(
            counted=self.progress[0],
            total=self.progress[1]
        ),
        related_link=self.related_link,
        title=TitleSchema(
            de_CH=self.title_translations.get('de_CH'),
            fr_CH=self.title_translations.get('fr_CH'),
            it_CH=self.title_translations.get('it_CH'),
            rm_CH=self.title_translations.get('rm_CH'),
        ),
        type='vote',
        results=VoteResultsSchema(
            answer=self.answer,
            nays_percentage=self.nays_percentage if counted else None,
            yeas_percentage=self.yeas_percentage if counted else None,
        ),
        ballots=[
            BallotSchema(
                type=ballot.type,
                title=TitleSchema(
                    de_CH=(ballot.title_translations or {}).get('de_CH'),
                    fr_CH=(ballot.title_translations or {}).get('fr_CH'),
                    it_CH=(ballot.title_translations or {}).get('it_CH'),
                    rm_CH=(ballot.title_translations or {}).get('rm_CH'),
                ),
                progress=ProgressSchema(
                    counted=ballot.progress[0],
                    total=ballot.progress[1],
                ),
                results=BallotResultSchema(
                    total=BallotTotalResultSchema(
                        accepted=ballot.accepted,
                        yeas=ballot.yeas,
                        nays=ballot.nays,
                        empty=ballot.empty,
                        invalid=ballot.invalid,
                        yeas_percentage=ballot.yeas_percentage,
                        nays_percentage=ballot.nays_percentage,
                        eligible_voters=ballot.eligible_voters,
                        cast_ballots=ballot.cast_ballots,
                        turnout=ballot.turnout,
                        counted=ballot.counted,
                    ),
                    entities=[
                        BallotEntityResultSchema(
                            accepted=entity.accepted,
                            yeas=entity.yeas,
                            nays=entity.nays,
                            empty=entity.empty,
                            invalid=entity.invalid,
                            yeas_percentage=entity.yeas_percentage,
                            nays_percentage=entity.nays_percentage,
                            eligible_voters=entity.eligible_voters,
                            cast_ballots=entity.cast_ballots,
                            turnout=entity.turnout,
                            counted=entity.counted,
                            name=(
                                entity.name if entity.entity_id else 'Expats'
                            ),
                            district=(
                                entity.district or ''
                                if entity.entity_id else ''
                            ),
                            id=entity.entity_id,
                        )
                        for entity in ballot.results
                    ]
                )
            ) for ballot in self.ballots
        ],
        url=request.link(self),
        embed=embed,
        media=media,
        data=DataSchema(
            json=request.link(self, 'data-json'),
            csv=request.link(self, 'data-csv'),
        )
    ).model_dump(by_alias=True)


@ElectionDayApp.json_schema(
    model=Vote,
    name='json-schema',
    permission=Public
)
def view_vote_json_schema(
    self: Vote,
    request: 'ElectionDayRequest'
) -> 'JSON_ro':
    """" The JSON schema of the main JSON view. """

    return VoteSchema.model_json_schema()


@ElectionDayApp.json(
    model=Vote,
    name='summary',
    permission=Public
)
def view_vote_summary(
    self: Vote,
    request: 'ElectionDayRequest'
) -> 'JSON_ro':
    """ View the summary of the vote as JSON. """

    @request.after
    def add_headers(response: 'Response') -> None:
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return get_vote_summary(self, request)


@ElectionDayApp.pdf_file(model=Vote, name='pdf')
def view_vote_pdf(
    self: Vote,
    request: 'ElectionDayRequest'
) -> 'RenderData':
    """ View the generated PDF. """

    layout = VoteLayout(self, request)
    return {
        'path': layout.pdf_path,
        'name': normalize_for_url(self.title or '')
    }


@ElectionDayApp.html(
    model=Vote,
    name='vote-header-widget',
    permission=Public,
    template='embed.pt'
)
def view_vote_header_as_widget(
    self: Vote,
    request: 'ElectionDayRequest'
) -> 'RenderData':
    """ A static link to the top bar showing the vote result as widget. """

    @request.after
    def add_last_modified(response: 'Response') -> None:
        add_last_modified_header(response, self.last_modified)

    return {
        'vote': self,
        'layout': VoteLayout(self, request),
        'type': 'vote-header',
        'scope': 'vote',
    }
