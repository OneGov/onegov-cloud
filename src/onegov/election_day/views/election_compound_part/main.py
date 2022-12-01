from morepath import redirect
from onegov.ballot import ElectionCompoundPart
from onegov.core.security import Public
# todo: ?
# from onegov.core.utils import normalize_for_url
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundPartLayout
from onegov.election_day.utils import add_cors_header
from onegov.election_day.utils import add_last_modified_header
# todo: ?
# from onegov.election_day.utils import get_election_compound_summary
# from onegov.election_day.utils.election_compound import \
#     get_candidate_statistics
# from onegov.election_day.utils.election_compound import \
#     get_elected_candidates
# from onegov.election_day.utils.election_compound import get_superregions
# from onegov.election_day.utils.parties import get_party_results


@ElectionDayApp.view(
    model=ElectionCompoundPart,
    request_method='HEAD',
    permission=Public
)
def view_superregion_head(self, request):

    @request.after
    def add_headers(response):
        add_cors_header(response)
        add_last_modified_header(
            response, self.election_compound.last_modified
        )


@ElectionDayApp.html(
    model=ElectionCompoundPart,
    permission=Public
)
def view_superregion(self, request):

    """" The main view. """

    return redirect(ElectionCompoundPartLayout(self, request).main_view)

# todo: ?
# @ElectionDayApp.json(
#     model=ElectionCompoundPart,
#     name='json',
#     permission=Public
# )
# def view_superregion_json(self, request):
#     """" The main view as JSON. """
#
#     last_modified = self.last_modified
#
#     @request.after
#     def add_headers(response):
#         add_cors_header(response)
#         add_last_modified_header(response, last_modified)
#
#     session = request.app.session()
#     embed = {'districts-map': request.link(self, 'districts-map')}
#     media = {'charts': {}}
#     layout = ElectionCompoundPartLayout(self, request)
#     layout.last_modified = last_modified
#     if layout.pdf_path:
#         media['pdf'] = request.link(self, 'pdf')
#     for tab in ('party-strengths', 'parties-panachage'):
#         layout = ElectionCompoundPartLayout(self, request, tab=tab)
#         layout.last_modified = last_modified
#         if layout.visible:
#             embed[tab] = request.link(self, '{}-chart'.format(tab))
#         if layout.svg_path:
#             media['charts'][tab] = request.link(self, '{}-svg'.format(tab))
#
#     elected_candidates = get_elected_candidates(self, session).all()
#     candidate_statistics = get_candidate_statistics(self, elected_candidates)
#     districts = {
#         election.id: {
#             'name': election.domain_segment,
#             'mandates': {
#                 'allocated': election.allocated_mandates or 0,
#                 'total': election.number_of_mandates or 0,
#             },
#             'progress': {
#                 'counted': election.progress[0] or 0,
#                 'total': election.progress[1] or 0
#             },
#         }
#         for election in self.elections
#     }
#     superregions = get_superregions(self, request.app.principal)
#
#     years, parties = get_party_results(self, json_serializable=True)
#
#     return {
#         'completed': self.completed,
#         'date': self.date.isoformat(),
#         'last_modified': last_modified.isoformat(),
#         'mandates': {
#             'allocated': self.allocated_mandates or 0,
#             'total': self.number_of_mandates or 0,
#         },
#         'progress': {
#             'counted': self.progress[0] or 0,
#             'total': self.progress[1] or 0
#         },
#         'districts': list(districts.values()),
#         'superregions': superregions,
#         'elections': [
#             request.link(election) for election in self.elections
#         ],
#         'elected_candidates': [
#             {
#                 'first_name': candidate.first_name,
#                 'family_name': candidate.family_name,
#                 'party': candidate.party,
#                 'list': candidate.list,
#                 'district': districts[candidate.election_id]['name']
#             } for candidate in elected_candidates
#         ],
#         'candidate_statistics': candidate_statistics,
#         'parties': parties,
#         'related_link': self.related_link,
#         'title': self.title_translations,
#         'type': 'election_compound',
#         'url': request.link(self),
#         'embed': embed,
#         'media': media,
#         'data': {
#             'json': request.link(self, 'data-json'),
#             'csv': request.link(self, 'data-csv'),
#         }
#     }

# todo: ?
# @ElectionDayApp.json(
#     model=ElectionCompoundPart,
#     name='summary',
#     permission=Public
# )
# def view_superregion_summary(self, request):
#
#     """ View the summary of the election compound as JSON. """
#
#     @request.after
#     def add_headers(response):
#         add_cors_header(response)
#         add_last_modified_header(response, self.last_modified)
#
#     return get_election_compound_summary(self, request)
