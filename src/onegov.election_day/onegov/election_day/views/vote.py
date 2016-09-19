from morepath.request import Response
from onegov.ballot import Ballot, Vote
from onegov.core.csv import convert_list_of_dicts_to_csv
from onegov.core.csv import convert_list_of_dicts_to_xlsx
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_vote_summary


@ElectionDayApp.html(model=Vote, template='vote.pt', permission=Public)
def view_vote(self, request):
    """" The main view. """

    request.include('ballot_map')

    return {
        'vote': self,
        'layout': DefaultLayout(self, request),
        'counted': self.counted,
        'use_maps': request.app.principal.use_maps
    }


@ElectionDayApp.json(model=Ballot, permission=Public, name='by-entity')
def view_ballot_by_entity(self, request):
    return self.percentage_by_entity()


@ElectionDayApp.html(model=Ballot, template='embed.pt', permission=Public,
                     name='map')
def view_ballot_as_map(self, request):
    """" View the ballot as map. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.vote.last_result_change)

    request.include('ballot_map')

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'map': request.link(self, name='by-entity')
        } if request.app.principal.use_maps else {}
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
            'counted': (self.progress[0] or 0) / (len(self.ballots) or 1),
            'total': (self.progress[1] or 0) / (len(self.ballots) or 1)
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
            if request.app.principal.use_maps
        ]
    }


@ElectionDayApp.json(model=Vote, permission=Public, name='summary')
def view_vote_summary(self, request):
    """ View the summary of the vote as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return get_vote_summary(self, request)


@ElectionDayApp.json(model=Vote, name='data-json', permission=Public)
def view_vote_data_as_json(self, request):
    """ View the raw data as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return self.export()


@ElectionDayApp.view(model=Vote, name='data-csv', permission=Public)
def view_vote_data_as_csv(self, request):
    """ View the raw data as CSV. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return convert_list_of_dicts_to_csv(self.export())


@ElectionDayApp.view(model=Vote, name='data-xlsx', permission=Public)
def view_vote_data_as_xlsx(self, request):
    """ View the raw data as XLSX. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return Response(
        convert_list_of_dicts_to_xlsx(self.export()),
        content_type=(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ),
        content_disposition='inline; filename={}.xlsx'.format(
            normalize_for_url(self.title)
        )
    )
