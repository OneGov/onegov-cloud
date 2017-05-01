from morepath.request import Response
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import VotesLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_vote_summary
from onegov.election_day.utils import handle_headerless_params


@ElectionDayApp.html(model=Vote, template='vote/ballot.pt', permission=Public)
def view_vote_proposal(self, request):
    """" The main view. """

    request.include('ballot_map')

    handle_headerless_params(request)

    return {
        'vote': self,
        'layout': VotesLayout(self, request),
        'use_maps': request.app.principal.use_maps
    }


@ElectionDayApp.html(model=Vote, template='vote/ballot.pt', permission=Public,
                     name='counter-proposal')
def view_vote_counter_proposal(self, request):
    """" The main view. """

    request.include('ballot_map')

    handle_headerless_params(request)

    return {
        'vote': self,
        'layout': VotesLayout(self, request, 'counter-proposal'),
        'use_maps': request.app.principal.use_maps
    }


@ElectionDayApp.html(model=Vote, template='vote/ballot.pt', permission=Public,
                     name='tie-breaker')
def view_vote_tie_breaker(self, request):
    """" The main view. """

    request.include('ballot_map')

    handle_headerless_params(request)

    return {
        'vote': self,
        'layout': VotesLayout(self, request, 'tie-breaker'),
        'use_maps': request.app.principal.use_maps
    }


@ElectionDayApp.json(model=Vote, permission=Public, name='json')
def view_vote_json(self, request):
    """" The main view as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    media = {'maps': {}}
    if VotesLayout(self, request).pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    if request.app.principal.use_maps:
        for ballot in self.ballots:
            if VotesLayout(self, request, tab=ballot.type).svg_path:
                media['maps'][ballot.type] = request.link(ballot, 'svg')

    return {
        'completed': self.completed,
        'date': self.date.isoformat(),
        'domain': self.domain,
        'last_modified': self.last_result_change.isoformat(),
        'progress': {
            'counted': self.progress[0],
            'total': self.progress[1]
        },
        'related_link': (self.meta or {}).get('related_link', ''),
        'title': self.title_translations,
        'type': 'election',
        'resuts': {
            'answer': self.answer,
            'nays_percentage': self.nays_percentage,
            'yeas_percentage': self.yeas_percentage,
        },
        'ballots': [
            {
                'type': ballot.type,
                'progress': {
                    'counted': ballot.progress[0],
                    'total': ballot.progress[1],
                },
                'results': {
                    'total': {
                        'accepted': ballot.accepted,
                        'yeas': ballot.yeas,
                        'nays': ballot.nays,
                        'empty': ballot.empty,
                        'invalid': ballot.invalid,
                        'yeas_percentage': ballot.yeas_percentage,
                        'nays_percentage': ballot.nays_percentage,
                        'elegible_voters': ballot.elegible_voters,
                        'cast_ballots': ballot.cast_ballots,
                        'turnout': ballot.turnout,
                        'counted': ballot.counted,
                    },
                    'districts': [
                        {
                            'accepted': district.accepted,
                            'yeas': district.yeas,
                            'nays': district.nays,
                            'empty': district.empty,
                            'invalid': district.invalid,
                            'yeas_percentage': district.yeas_percentage,
                            'nays_percentage': district.nays_percentage,
                            'elegible_voters': district.elegible_voters,
                            'cast_ballots': district.cast_ballots,
                            'turnout': district.turnout,
                            'counted': district.counted,
                            'name': (
                                district.group if district.entity_id
                                else 'Expats'
                            ),
                            'id': district.entity_id,
                        } for district in ballot.results
                    ],
                },
            } for ballot in self.ballots
        ],
        'url': request.link(self),
        'embed': {
            ballot.type: request.link(ballot, 'map')
            for ballot in self.ballots if request.app.principal.use_maps

        },
        'media': media,
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
            'xlsx': request.link(self, 'data-xlsx'),
        }
    }


@ElectionDayApp.json(model=Vote, permission=Public, name='summary')
def view_vote_summary(self, request):
    """ View the summary of the vote as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return get_vote_summary(self, request)


@ElectionDayApp.view(model=Vote, name='pdf', permission=Public)
def view_vote_pdf(self, request):
    """ View the generated PDF. """

    layout = VotesLayout(self, request)

    if not layout.pdf_path:
        return Response(status='503 Service Unavailable')

    content = None
    with request.app.filestorage.open(layout.pdf_path, 'rb') as f:
        content = f.read()

    return Response(
        content,
        content_type='application/pdf',
        content_disposition='inline; filename={}.pdf'.format(
            normalize_for_url(self.title)
        )
    )
