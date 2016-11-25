from onegov.ballot import Ballot
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layout import DefaultLayout
from onegov.election_day.utils import add_last_modified_header


@ElectionDayApp.json(model=Ballot, permission=Public, name='by-entity')
def view_ballot_by_entity(self, request):
    return self.percentage_by_entity()


@ElectionDayApp.html(model=Ballot, template='embed.pt', permission=Public,
                     name='map')
def view_ballot_as_map(self, request):
    """" View the ballot as map. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.vote.last_result_change)

    request.include('ballot_map')
    request.include('frame_resizer')

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'data': {
            'map': request.link(self, name='by-entity')
        } if request.app.principal.use_maps else {}
    }
