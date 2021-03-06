from morepath import redirect
from morepath.request import Response
from onegov.ballot import Ballot
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.ballot import get_ballot_data_by_entity


@ElectionDayApp.html(
    model=Vote,
    name='entities',
    template='vote/entities.pt',
    permission=Public
)
def view_vote_entities(self, request):

    """" The main view (proposal). """

    layout = VoteLayout(self, request, 'entities')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-entities',
    template='vote/entities.pt',
    permission=Public
)
def view_vote_entities_proposal(self, request):

    """" The main view (proposal). """

    layout = VoteLayout(self, request, 'proposal-entities')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-entities',
    template='vote/entities.pt',
    permission=Public
)
def view_vote_entities_counter_proposal(self, request):

    """" The main view (counter-proposal). """

    layout = VoteLayout(self, request, 'counter-proposal-entities')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-entities',
    template='vote/entities.pt',
    permission=Public
)
def view_vote_entities_tie_breaker(self, request):

    """" The main view (tie-breaker). """

    layout = VoteLayout(self, request, 'tie-breaker-entities')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-by-entities-map',
    permission=Public
)
def view_vote_entities_map_proposal(self, request):

    """ A static link to the map of the proposal. """

    return redirect(request.link(self.proposal, name='entities-map'))


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-by-entities-map',
    permission=Public
)
def view_vote_entities_map_counter_proposal(self, request):

    """ A static link to the map of the counter proposal. """

    return redirect(request.link(self.counter_proposal, name='entities-map'))


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-by-entities-map',
    permission=Public
)
def view_vote_entities_map_tie_breaker(self, request):

    """ A static link to the map of the tie breaker. """

    return redirect(request.link(self.tie_breaker, name='entities-map'))


@ElectionDayApp.json(
    model=Ballot,
    name='by-entity',
    permission=Public
)
def view_ballot_by_entity(self, request):

    """ Returns the data for the ballot map. """

    return get_ballot_data_by_entity(self)


@ElectionDayApp.html(
    model=Ballot,
    name='entities-map',
    template='embed.pt',
    permission=Public
)
def view_ballot_entities_as_map(self, request):

    """" View the results of the entities of ballot as map. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.vote.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'type': 'map',
        'scope': 'entities',
        'year': self.vote.date.year,
        'thumbs': 'true',
        'color_scale': 'rb',
        'label_left_hand': _("Nay"),
        'label_right_hand': _("Yay"),
        'data_url': request.link(self, name='by-entity'),
    }


@ElectionDayApp.html(
    model=Ballot,
    name='entities-table',
    template='embed.pt',
    permission=Public
)
def view_ballot_as_table(self, request):

    """" View the results of the entities of ballot as table. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.vote.last_modified)

    return {
        'ballot': self,
        'layout': DefaultLayout(self, request),
        'type': 'ballot-table',
        'year': self.vote.date.year,
        'scope': 'entities',
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-by-entities-table',
    permission=Public
)
def view_vote_entities_table_proposal(self, request):

    """ A static link to the table by entities of the proposal. """

    return redirect(request.link(self.proposal, name='entities-table'))


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-by-entities-table',
    permission=Public
)
def view_vote_entities_table_counter_proposal(self, request):

    """ A static link to the table by entities of the counter proposal. """

    return redirect(request.link(self.counter_proposal, name='entities-table'))


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-by-entities-table',
    permission=Public
)
def view_vote_entities_table_tie_breaker(self, request):

    """ A static link to the table of the tie breaker. """

    return redirect(request.link(self.tie_breaker, name='entities-table'))


@ElectionDayApp.json(
    model=Ballot,
    name='entities-map-svg',
    permission=Public
)
def view_ballot_entities_svg(self, request):

    """ Download the results of the entities of ballot as a SVG. """

    layout = VoteLayout(
        self.vote, request, tab='{}-entities'.format(self.type)
    )
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
