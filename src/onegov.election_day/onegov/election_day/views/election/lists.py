from onegov.ballot import Election, List
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout, ElectionsLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils import handle_headerless_params
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


@ElectionDayApp.json(model=Election, permission=Public, name='lists-data')
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


@ElectionDayApp.html(model=Election, permission=Public,
                     name='lists-chart', template='embed.pt')
def view_election_lists_chart(self, request):
    """" View the lists as bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_result_change)

    request.include('bar_chart')
    request.include('frame_resizer')

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'bar': request.link(self, name='lists-data')
        }
    }


@ElectionDayApp.html(model=Election, template='election/lists.pt',
                     name='lists', permission=Public)
def view_election_lists(self, request):
    """" The main view. """

    request.include('bar_chart')
    request.include('tablesorter')

    handle_headerless_params(request)

    return {
        'election': self,
        'layout': ElectionsLayout(self, request, 'lists'),
        'lists': get_list_results(self, object_session(self)),
    }
