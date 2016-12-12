from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import VotesLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_vote_summary
from onegov.election_day.utils import handle_headerless_params


@ElectionDayApp.html(model=Vote, template='vote.pt', permission=Public)
def view_vote_proposal(self, request):
    """" The main view. """

    request.include('ballot_map')
    request.include('tablesorter')

    handle_headerless_params(request)

    return {
        'vote': self,
        'layout': VotesLayout(self, request),
        'use_maps': request.app.principal.use_maps
    }


@ElectionDayApp.html(model=Vote, template='vote.pt', permission=Public,
                     name='counter-proposal')
def view_vote_counter_proposal(self, request):
    """" The main view. """

    request.include('ballot_map')
    request.include('tablesorter')

    handle_headerless_params(request)

    return {
        'vote': self,
        'layout': VotesLayout(self, request, 'counter-proposal'),
        'use_maps': request.app.principal.use_maps
    }


@ElectionDayApp.html(model=Vote, template='vote.pt', permission=Public,
                     name='tie-breaker')
def view_vote_tie_breaker(self, request):
    """" The main view. """

    request.include('ballot_map')
    request.include('tablesorter')

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

    return {
        'date': self.date.isoformat(),
        'domain': self.domain,
        'last_modified': self.last_result_change.isoformat(),
        'progress': {
            'counted': (self.progress[0] or 0) / (self.ballots.count() or 1),
            'total': (self.progress[1] or 0) / (self.ballots.count() or 1)
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
                            'name': district.group,
                            'id': district.entity_id,
                        } for district in ballot.results
                    ],
                },
            } for ballot in self.ballots
        ],
        'url': request.link(self),
        'embed': [
            request.link(ballot, 'map') for ballot in self.ballots
        ]
    }


@ElectionDayApp.json(model=Vote, permission=Public, name='summary')
def view_vote_summary(self, request):
    """ View the summary of the vote as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return get_vote_summary(self, request)
