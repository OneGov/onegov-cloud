from morepath.request import Response
from onegov.ballot import Election
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header


def get_parties_panachage(item, request=None):
    results = item.panachage_results.all()
    party_results = item.party_results.filter_by(year=item.date.year).all()
    if not results:
        return {}

    parties = sorted(
        set([result.source for result in results]) |
        set([result.target for result in results]) |
        set([result.name for result in party_results])
    )

    def left_node(party):
        return parties.index(party)

    def right_node(party):
        return parties.index(party) + len(parties)

    colors = dict(set((r.name, r.color) for r in party_results))
    intra_party_votes = dict(set((r.name, r.votes) for r in party_results))

    # Create the links
    links = []
    for result in results:
        if result.source == result.target:
            continue
        if result.target in intra_party_votes:
            intra_party_votes[result.target] -= result.votes
        links.append({
            'source': left_node(result.source),
            'target': right_node(result.target),
            'value': result.votes,
            'color': colors.get(result.source, '#999')
        })
    for party, votes in intra_party_votes.items():
        links.append({
            'source': left_node(party),
            'target': right_node(party),
            'value': votes,
            'color': colors.get(party, '#999')
        })

    # Create the nodes
    blank = request.translate(_("Blank list")) if request else '-'
    nodes = [
        {
            'name': name or blank,
            'id': count + 1,
            'color': colors.get(name, '#999')
        }
        for count, name in enumerate(2 * parties)
    ]

    return {
        'nodes': nodes,
        'links': links,
        'title': item.title
    }


@ElectionDayApp.json(
    model=Election,
    name='parties-panachage-data',
    permission=Public
)
def view_election_parties_panachage_data(self, request):

    """" View the panachage data as JSON. Used to for the panachage sankey
    chart.

    Returns for every list: The number of votes from other parties. The
    modified xplus remaining votes from the own list.
    """

    if self.type == 'majorz':
        return {}

    return get_parties_panachage(self, request)


@ElectionDayApp.html(
    model=Election,
    name='parties-panachage-chart',
    template='embed.pt',
    permission=Public
)
def view_election_parties_panachage_chart(self, request):

    """" View the panachage data as sankey chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'sankey': request.link(self, name='parties-panachage-data')
        }
    }


@ElectionDayApp.html(
    model=Election,
    name='parties-panachage',
    template='election/parties_panachage.pt',
    permission=Public
)
def view_election_parties_panachage(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'parties-panachage')

    return {
        'election': self,
        'layout': layout
    }


@ElectionDayApp.json(
    model=Election,
    name='parties-panachage-svg',
    permission=Public
)
def view_election_parties_panachage_svg(self, request):

    """ View the panachage as SVG. """

    layout = ElectionLayout(self, request, 'parties-panachage')
    if not layout.svg_path:
        return Response(status='503 Service Unavailable')

    content = None
    with request.app.filestorage.open(layout.svg_path, 'r') as f:
        content = f.read()

    return Response(
        content,
        content_type='application/svg; charset=utf-8',
        content_disposition='inline; filename={}'.format(layout.svg_name)
    )
