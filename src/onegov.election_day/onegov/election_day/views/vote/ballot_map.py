from morepath.request import Response
from onegov.ballot import Ballot
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.json(
    model=Ballot,
    name='by-entity',
    permission=Public
)
def view_ballot_by_entity(self, request):

    """ Returns the data for the ballot map. """

    return self.percentage_by_entity()


@ElectionDayApp.html(
    model=Ballot,
    name='map',
    template='embed.pt',
    permission=Public
)
def view_ballot_as_map(self, request):

    """" View the ballot as map. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.vote.last_modified)

    show_map = request.app.principal.is_year_available(self.vote.date.year)
    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'map': request.link(self, name='by-entity')
        } if show_map else {}
    }


@ElectionDayApp.json(
    model=Ballot,
    name='svg',
    permission=Public
)
def view_ballot_svg(self, request):

    """ View the ballot as SVG. """

    layout = VoteLayout(self.vote, request, tab=self.type)
    if not layout.svg_path:
        return Response(status='503 Service Unavailable')

    content = None
    with request.app.filestorage.open(layout.svg_path, 'r') as f:
        content = f.read()

    return Response(
        content,
        content_type=('application/svg; charset=utf-8'),
        content_disposition='inline; filename={}'.format(layout.svg_name)
    )
