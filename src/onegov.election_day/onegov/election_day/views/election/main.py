from morepath import redirect
from morepath.request import Response
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
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

    return redirect(ElectionsLayout(self, request).main_view)


@ElectionDayApp.json(model=Election, permission=Public, name='json')
def view_election_json(self, request):
    """" The main view as JSON. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    media = {'charts': {}}
    if ElectionsLayout(self, request).pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    for tab in ('candidates', 'lists', 'connections', 'panachage', 'parties'):
        if ElectionsLayout(self, request, tab=tab).svg_path:
            media['charts'][tab] = request.link(self, '{}-svg'.format(tab))

    embed = {'candidates': request.link(self, 'candidates-chart')}
    for item in ('lists', 'connections', 'panachage', 'parties'):
        if ElectionsLayout(self, request).visible(item):
            embed[item] = request.link(self, '{}-chart'.format(item))

    data = {
        'completed': self.completed,
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
                    'name': district.group if district.entity_id else 'Expats',
                    'id': district.entity_id,
                } for district in self.results
            ],
        },
        'election_type': self.type,
        'url': request.link(self),
        'embed': embed,
        'media': media,
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
            'xlsx': request.link(self, 'data-xlsx'),
        }
    }

    session = object_session(self)

    if self.type == 'majorz':
        data['absolute_majority'] = self.absolute_majority
        data['candidates'] = [
            {
                'family_name': candidate[0],
                'first_name': candidate[1],
                'elected': candidate[2],
                'party': candidate[3],
                'votes': candidate[4],
            } for candidate in get_candidates_results(self, session)
        ]

    if self.type == 'proporz':
        data['candidates'] = [
            {
                'family_name': candidate[0],
                'first_name': candidate[1],
                'elected': candidate[2],
                'party': candidate[3],
                'votes': candidate[4],
                'list_name': candidate[5],
                'list_list_id': candidate[6]
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


@ElectionDayApp.view(model=Election, name='pdf', permission=Public)
def view_election_pdf(self, request):
    """ View the generated PDF. """

    layout = ElectionsLayout(self, request)

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
