from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.core.utils import groupbylist
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout


def districts_data(principal, compound):
    entities = principal.entities.get(compound.date.year, {})
    if compound.domain_elections in ('region', 'district'):
        lookup = sorted([
            (value.get(compound.domain_elections), key)
            for key, value in entities.items()
        ])
        lookup = groupbylist(lookup, lambda x: x[0])
        lookup = {
            key: {
                'id': key,
                'entities': [v[1] for v in value]
            } for key, value in lookup
        }
    if compound.domain_elections == 'municipality':
        lookup = {
            value['name']: {
                'id': key,
                'entities': []
            } for key, value in entities.items()
        }
    if not lookup:
        return {}

    return {
        lookup[election.domain_segment]['id']: {
            'entities': lookup[election.domain_segment]['entities'],
            'votes': 0,
            'percentage': 100.0,
            'counted': election.counted
        }
        for election in compound.elections
        if election.domain_segment in lookup
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='districts',
    template='election_compound/districts.pt',
    permission=Public
)
def view_election_compound_districts(self, request):

    """" The districts view. """

    map_type = 'districts'
    if self.domain_elections == 'municipality':
        map_type = 'entities'

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'districts'),
        'map_type': map_type,
        'data_url': request.link(self, name='by-district'),
        'embed_source': request.link(self, name='districts-map'),
    }


@ElectionDayApp.json(
    model=ElectionCompound,
    name='by-district',
    permission=Public
)
def view_election_compound_by_district(self, request):

    """" View the districts/regions/municipalities as JSON for the map. """

    return districts_data(request.app.principal, self)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='districts-map',
    template='embed.pt',
    permission=Public
)
def view_election_list_by_district_chart(self, request):

    """" Embed the heatmap. """

    scope = 'districts'
    if self.domain_elections == 'municipality':
        scope = 'entities'

    return {
        'model': self,
        'layout': ElectionCompoundLayout(self, request, 'districts'),
        'type': 'map',
        'scope': scope,
        'year': self.date.year,
        'thumbs': 'false',
        'color_scale': 'b',
        'label_left_hand': '',
        'label_right_hand': '',
        'hide_percentages': True,
        'hide_legend': True,
        'data_url': request.link(self, name='by-district'),
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='districts-table',
    template='embed.pt',
    permission=Public
)
def view_election_compound_districts_table(self, request):

    """" Displays the districts as standalone table. """

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'districts'),
        'type': 'election-compound-table',
        'scope': 'districts'
    }
