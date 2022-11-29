from onegov.ballot import Superregion
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import SuperregionLayout
# todo: ?
# from onegov.election_day.utils import add_last_modified_header
# from onegov.election_day.utils.election_compound import get_districts_data


@ElectionDayApp.html(
    model=Superregion,
    name='districts',
    template='superregion/districts.pt',
    permission=Public
)
def view_superregion_districts(self, request):

    """" The districts view. """

    # todo: ?
    # map_type = 'districts'
    # if self.domain_elections == 'municipality':
    #     map_type = 'entities'

    return {
        'superregion': self,
        'layout': SuperregionLayout(self, request, 'districts'),
        # todo: ?
        # 'map_type': map_type,
        # 'data_url': request.link(self, name='by-district'),
        # 'embed_source': request.link(self, name='districts-map'),
    }


# todo: ?
# @ElectionDayApp.json(
#     model=Superregion,
#     name='by-district',
#     permission=Public
# )
# def view_superregion_by_district(self, request):
#
#     """" View the districts/regions/municipalities as JSON for the map. """
#
#     return get_districts_data(self, request.app.principal, request)


# todo: ?
# @ElectionDayApp.html(
#     model=Superregion,
#     name='districts-map',
#     template='embed.pt',
#     permission=Public
# )
# def view_election_list_by_district_chart(self, request):
#
#     """" Embed the heatmap. """
#
#     @request.after
#     def add_last_modified(response):
#         add_last_modified_header(response, self.last_modified)
#
#     scope = 'districts'
#     if self.domain_elections == 'municipality':
#         scope = 'entities'
#
#     return {
#         'model': self,
#         'layout': SuperregionLayout(self, request, 'districts'),
#         'type': 'map',
#         'scope': scope,
#         'year': self.date.year,
#         'thumbs': 'false',
#         'color_scale': 'b',
#         'label_left_hand': '',
#         'label_right_hand': '',
#         'hide_percentages': True,
#         'hide_legend': True,
#         'data_url': request.link(self, name='by-district'),
#     }

# todo: ?
# @ElectionDayApp.html(
#     model=Superregion,
#     name='districts-table',
#     template='embed.pt',
#     permission=Public
# )
# def view_superregion_districts_table(self, request):
#
#     """" Displays the districts as standalone table. """
#
#     @request.after
#     def add_last_modified(response):
#         add_last_modified_header(response, self.last_modified)
#
#     return {
#         'election_compound': self,
#         'layout': SuperregionLayout(self, request, 'districts'),
#         'type': 'election-compound-table',
#         'scope': 'districts'
#     }
