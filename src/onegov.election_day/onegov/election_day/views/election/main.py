import morepath

from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import ElectionsLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_election_summary
from onegov.election_day.views.election import get_candidates_results
from onegov.election_day.views.election import get_connection_results
from onegov.election_day.views.election.lists import get_list_results
from sqlalchemy.orm import object_session


@ElectionDayApp.html(model=Election, permission=Public)
def view_election(self, request):
    """" The main view. """

    return morepath.redirect(ElectionsLayout(self, request).main_view)


@ElectionDayApp.json(model=Election, permission=Public, name='json')
def view_election_json(self, request):
    """" The main view as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    data = {
        'date': self.date.isoformat(),
        'domain': self.domain,
        'last_modified': self.last_result_change.isoformat(),
        'mandates': {
            'allocated': self.allocated_mandates or 0,
            'total': self.number_of_mandates or 0,
        },
        'progress': {
            'counted': self.counted_entities or 0,
            'total': self.total_entities or 0,
        },
        'related_link': (self.meta or {}).get('related_link', ''),
        'title': self.title_translations,
        'type': 'election',
        'statistics': {
            'total': {
                'elegible_voters': self.elegible_voters,
                'received_ballots': self.received_ballots,
                'accounted_ballots': self.accounted_ballots,
                'blank_ballots': self.blank_ballots,
                'invalid_ballots': self.invalid_ballots,
                'accounted_votes': self.accounted_votes,
                'turnout': self.turnout,
            },
            'districts': [
                {
                    'elegible_voters': district.elegible_voters,
                    'received_ballots': district.received_ballots,
                    'accounted_ballots': district.accounted_ballots,
                    'blank_ballots': district.blank_ballots,
                    'invalid_ballots': district.invalid_ballots,
                    'accounted_votes': district.accounted_votes,
                    'turnout': district.turnout,
                    'name': district.group,
                    'id': district.entity_id,
                } for district in self.results
            ],
        },
        'election_type': self.type,
        'url': request.link(self),
        'embed': [
            request.link(self, 'lists-chart'),
            request.link(self, 'connections-chart'),
            request.link(self, 'panachage-chart'),
        ] if self.type == 'proporz' else [
            request.link(self, 'candidates-chart'),
        ]
    }

    session = object_session(self)

    if self.type == 'majorz':
        data['absolute_majority'] = self.absolute_majority
        data['candidates'] = [
            {
                'family_name': candidate[0],
                'first_name': candidate[1],
                'elected': candidate[2],
                'votes': candidate[3],
            } for candidate in get_candidates_results(self, session)
        ]

    if self.type == 'proporz':
        data['candidates'] = [
            {
                'family_name': candidate[0],
                'first_name': candidate[1],
                'elected': candidate[2],
                'votes': candidate[3],
                'list_name': candidate[4],
                'list_list_id': candidate[5]
            } for candidate in get_candidates_results(self, session)
        ]

        data['lists'] = [
            {
                'name': item[0],
                'votes': item[1],
                'id': item[2],
            } for item in get_list_results(self, session)
        ]

        data['list_connections'] = [
            {
                'id': connection[0],
                'votes': connection[1],
                'lists': [
                    {
                        'name': item[0],
                        'votes': item[1],
                        'id': item[2],
                    } for item in connection[2]
                ],
                'subconnections': [
                    {
                        'id': subconnection[0],
                        'votes': subconnection[1],
                        'lists': [
                            {
                                'name': item[0],
                                'votes': item[1],
                                'id': item[2],
                            } for item in subconnection[2]
                        ],
                    } for subconnection in connection[3]
                ],
            } for connection in get_connection_results(self, session)
        ]

    return data


@ElectionDayApp.json(model=Election, permission=Public, name='summary')
def view_election_summary(self, request):
    """ View the summary of the election as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    return get_election_summary(self, request)
