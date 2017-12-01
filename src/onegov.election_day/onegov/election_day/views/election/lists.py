from morepath.request import Response
from onegov.ballot import Election, List
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from sqlalchemy import desc
from sqlalchemy.orm import object_session


def get_list_results(election, session):

    """ Returns the aggregated list results as list. """

    result = session.query(
        List.name, List.votes, List.list_id, List.number_of_mandates
    )
    result = result.order_by(desc(List.votes))
    result = result.filter(List.election_id == election.id)

    return result


@ElectionDayApp.json(
    model=Election,
    name='lists-data',
    permission=Public
)
def view_election_lists_data(self, request):

    """" View the lists as JSON. Used to for the lists bar chart. """

    if self.type == 'majorz':
        return {
            'results': [],
            'majority': None,
            'title': self.title
        }

    return {
        'results': [{
            'text': item[0],
            'value': item[1],
            'value2': item[3],
            'class': 'active' if item[3] else 'inactive',
        } for item in get_list_results(self, object_session(self))],
        'majority': None,
        'title': self.title
    }


@ElectionDayApp.html(
    model=Election,
    name='lists-chart',
    template='embed.pt',
    permission=Public
)
def view_election_lists_chart(self, request):

    """" View the lists as bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'bar': request.link(self, name='lists-data')
        }
    }


@ElectionDayApp.html(
    model=Election,
    name='lists',
    template='election/lists.pt',
    permission=Public
)
def view_election_lists(self, request):

    """" The main view. """

    layout = ElectionLayout(self, request, 'lists')

    return {
        'election': self,
        'layout': layout,
        'lists': get_list_results(self, object_session(self)),
    }


@ElectionDayApp.json(
    model=Election,
    name='lists-svg',
    permission=Public
)
def view_election_lists_svg(self, request):

    """ View the lists as SVG. """

    layout = ElectionLayout(self, request, 'lists')
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
