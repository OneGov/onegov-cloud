from morepath import redirect
from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import get_election_compound_summary
from onegov.election_day.utils.election_compound import get_elected_candidates
from onegov.election_day.utils.parties import get_party_results


@ElectionDayApp.html(
    model=ElectionCompound,
    permission=Public
)
def view_election_compound(self, request):

    """" The main view. """

    return redirect(ElectionCompoundLayout(self, request).main_view)


@ElectionDayApp.json(
    model=ElectionCompound,
    name='json',
    permission=Public
)
def view_election_compound_json(self, request):
    """" The main view as JSON. """

    last_modified = self.last_modified

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, last_modified)

    embed = {'districts-map': request.link(self, 'districts-map')}
    media = {'charts': {}}
    layout = ElectionCompoundLayout(self, request)
    layout.last_modified = last_modified
    if layout.pdf_path:
        media['pdf'] = request.link(self, 'pdf')
    for tab in ('party-strengths', 'parties-panachage'):
        layout = ElectionCompoundLayout(self, request, tab=tab)
        layout.last_modified = last_modified
        if layout.visible:
            embed[tab] = request.link(self, '{}-chart'.format(tab))
        if layout.svg_path:
            media['charts'][tab] = request.link(self, '{}-svg'.format(tab))

    elected_candidates = get_elected_candidates(self, request.app.session())
    districts = {
        election.id: {
            'name': election.domain_segment,
            'mandates': {
                'allocated': election.allocated_mandates or 0,
                'total': election.number_of_mandates or 0,
            },
            'progress': {
                'counted': election.progress[0] or 0,
                'total': election.progress[1] or 0
            },
        }
        for election in self.elections
    }

    years, parties = get_party_results(self)

    return {
        'completed': self.completed,
        'date': self.date.isoformat(),
        'last_modified': last_modified.isoformat(),
        'mandates': {
            'allocated': self.allocated_mandates or 0,
            'total': self.number_of_mandates or 0,
        },
        'progress': {
            'counted': self.progress[0] or 0,
            'total': self.progress[1] or 0
        },
        'districts': list(districts.values()),
        'elections': [
            request.link(election) for election in self.elections
        ],
        'elected_candidates': [
            {
                'first_name': candidate.first_name,
                'family_name': candidate.family_name,
                'party': candidate.party,
                'list': candidate.list,
                'district': districts[candidate.election_id]['name']
            } for candidate in elected_candidates
        ],
        'parties': parties,
        'related_link': self.related_link,
        'title': self.title_translations,
        'type': 'election_compound',
        'url': request.link(self),
        'embed': embed,
        'media': media,
        'data': {
            'json': request.link(self, 'data-json'),
            'csv': request.link(self, 'data-csv'),
        }
    }


@ElectionDayApp.json(
    model=ElectionCompound,
    name='summary',
    permission=Public
)
def view_election_compound_summary(self, request):

    """ View the summary of the election compound as JSON. """

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(response, self.last_modified)

    return get_election_compound_summary(self, request)


@ElectionDayApp.pdf_file(model=ElectionCompound, name='pdf')
def view_election_compound_pdf(self, request):

    """ View the generated PDF. """

    layout = ElectionCompoundLayout(self, request)
    return {
        'path': layout.pdf_path,
        'name': normalize_for_url(self.title)
    }
