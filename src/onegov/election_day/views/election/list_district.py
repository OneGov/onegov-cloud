from onegov.ballot import Election
from onegov.ballot import List
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.utils import add_last_modified_header
from sqlalchemy import func


def list_options(request, election):
    if election.type == 'majorz':
        return []

    mandates = request.translate(_("Mandates"))
    return [
        (
            request.link(list_, name='by-district'),
            '{} {}'.format(
                list_.name,
                (
                    f'({list_.number_of_mandates} {mandates})'
                    if list_.number_of_mandates else ''
                )
            ).strip()
        )
        for list_ in election.lists.order_by(None).order_by(
            List.number_of_mandates.desc(),
            func.lower(List.name)
        )
    ]


@ElectionDayApp.json(
    model=List,
    name='by-district',
    permission=Public
)
def view_list_by_district(self, request):

    """" View the list by district as JSON. """

    return self.percentage_by_district


@ElectionDayApp.html(
    model=Election,
    name='list-by-district',
    template='election/heatmap.pt',
    permission=Public
)
def view_election_list_by_district(self, request):

    """" View the list as heatmap by district. """

    layout = ElectionLayout(self, request, 'list-by-district')

    options = list_options(request, self)
    data_url = options[0][0] if options else None

    return {
        'election': self,
        'layout': layout,
        'options': options,
        'map_type': 'districts',
        'data_url': data_url,
        'embed_source': request.link(self, name='list-by-district-chart')
    }


@ElectionDayApp.html(
    model=Election,
    name='list-by-district-chart',
    template='embed.pt',
    permission=Public
)
def view_election_list_by_district_chart(self, request):

    """" Embed the heatmap. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    options = list_options(request, self)
    data_url = options[0][0] if options else None

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'type': 'map',
        'scope': 'districts',
        'year': self.date.year,
        'thumbs': 'false',
        'color_scale': 'r',
        'label_left_hand': '0%',
        'label_right_hand': '100%',
        'data_url': data_url,
        'options': options
    }
