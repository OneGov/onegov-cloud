from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.election_compound import get_superregions
from onegov.election_day.utils.election_compound import get_superregions_data


@ElectionDayApp.html(
    model=ElectionCompound,
    name='superregions',
    template='election_compound/superregions.pt',
    permission=Public
)
def view_election_compound_superregions(self, request):

    """" The superregions view. """

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'superregions'),
        'map_type': 'districts',
        'superregions': get_superregions(self, request.app.principal),
        'data_url': request.link(self, name='by-superregion'),
        'embed_source': request.link(self, name='superregions-map'),
    }


@ElectionDayApp.json(
    model=ElectionCompound,
    name='by-superregion',
    permission=Public
)
def view_election_compound_by_superregion(self, request):

    """" View the superregions/regions/municipalities as JSON for the map. """

    return get_superregions_data(self, request.app.principal)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='superregions-map',
    template='embed.pt',
    permission=Public
)
def view_election_list_by_superregion_chart(self, request):

    """" Embed the heatmap. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionCompoundLayout(self, request, 'superregions'),
        'type': 'map',
        'scope': 'districts',
        'year': self.date.year,
        'thumbs': 'false',
        'color_scale': 'b',
        'label_left_hand': '',
        'label_right_hand': '',
        'hide_percentages': True,
        'hide_legend': True,
        'data_url': request.link(self, name='by-superregion'),
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='superregions-table',
    template='embed.pt',
    permission=Public
)
def view_election_compound_superregions_table(self, request):

    """" Displays the superregions as standalone table. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'superregions'),
        'type': 'election-compound-table',
        'scope': 'superregions',
        'superregions': get_superregions(self, request.app.principal),
    }
