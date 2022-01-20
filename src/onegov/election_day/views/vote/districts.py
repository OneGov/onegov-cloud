from morepath import redirect
from onegov.ballot import Ballot
from onegov.ballot import Vote
from onegov.core.security import Public
from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.vote import get_ballot_data_by_district
from webob.exc import HTTPNotFound


@ElectionDayApp.html(
    model=Vote,
    name='districts',
    template='vote/districts.pt',
    permission=Public
)
def view_vote_districts(self, request):

    """" The main view (proposal). """

    layout = VoteLayout(self, request, 'districts')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-districts',
    template='vote/districts.pt',
    permission=Public
)
def view_vote_districts_proposal(self, request):

    """" The main view (proposal). """

    layout = VoteLayout(self, request, 'proposal-districts')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-districts',
    template='vote/districts.pt',
    permission=Public
)
def view_vote_districts_counter_proposal(self, request):

    """" The main view (counter-proposal). """

    layout = VoteLayout(self, request, 'counter-proposal-districts')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-districts',
    template='vote/districts.pt',
    permission=Public
)
def view_vote_districts_tie_breaker(self, request):

    """" The main view (tie-breaker). """

    layout = VoteLayout(self, request, 'tie-breaker-districts')

    return {
        'vote': self,
        'layout': layout
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-by-districts-map',
    permission=Public
)
def view_vote_districts_map_proposal(self, request):

    """ A static link to the map of the proposal. """

    ballot = getattr(self, 'proposal', None)
    if ballot:
        return redirect(request.link(ballot, name='districts-map'))

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-by-districts-map',
    permission=Public
)
def view_vote_districts_map_counter_proposal(self, request):

    """ A static link to the map of the counter proposal. """

    ballot = getattr(self, 'counter_proposal', None)
    if ballot:
        return redirect(request.link(ballot, name='districts-map'))

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-by-districts-map',
    permission=Public
)
def view_vote_districts_map_tie_breaker(self, request):

    """ A static link to the map of the tie breaker. """

    ballot = getattr(self, 'tie_breaker', None)
    if ballot:
        return redirect(request.link(ballot, name='districts-map'))

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Ballot,
    name='districts-table',
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
        'layout': VoteLayout(self.vote, request, f'{self.type}-districts'),
        'type': 'ballot-table',
        'year': self.vote.date.year,
        'scope': 'districts',
    }


@ElectionDayApp.html(
    model=Vote,
    name='proposal-by-districts-table',
    permission=Public
)
def view_vote_districts_table_proposal(self, request):

    """ A static link to the table by districts of the proposal. """

    ballot = getattr(self, 'proposal', None)
    if ballot:
        return redirect(request.link(ballot, name='districts-table'))

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='counter-proposal-by-districts-table',
    permission=Public
)
def view_vote_districts_table_counter_proposal(self, request):

    """ A static link to the table by districts of the counter proposal. """

    ballot = getattr(self, 'counter_proposal', None)
    if ballot:
        return redirect(request.link(ballot, name='districts-table'))

    raise HTTPNotFound()


@ElectionDayApp.html(
    model=Vote,
    name='tie-breaker-by-districts-table',
    permission=Public
)
def view_vote_districts_table_tie_breaker(self, request):

    """ A static link to the table of the tie breaker by districts. """

    ballot = getattr(self, 'tie_breaker', None)
    if ballot:
        return redirect(request.link(ballot, name='districts-table'))

    raise HTTPNotFound()


@ElectionDayApp.json(
    model=Ballot,
    name='by-district',
    permission=Public
)
def view_ballot_by_district(self, request):

    """ Returns the data for the ballot map. """

    return get_ballot_data_by_district(self)


@ElectionDayApp.html(
    model=Ballot,
    name='districts-map',
    template='embed.pt',
    permission=Public
)
def view_ballot_districts_as_map(self, request):

    """" View the results of the districts of ballot as map. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.vote.last_modified)

    return {
        'model': self,
        'layout': DefaultLayout(self, request),
        'type': 'map',
        'scope': 'districts',
        'year': self.vote.date.year,
        'thumbs': 'true',
        'color_scale': 'rb',
        'label_left_hand': _("Nay"),
        'label_right_hand': _("Yay"),
        'data_url': request.link(self, name='by-district'),
    }


@ElectionDayApp.svg_file(model=Ballot, name='districts-map-svg')
def view_ballot_districts_svg(self, request):

    """" Download the results of the districts of ballot as a SVG. """

    layout = VoteLayout(
        self.vote, request, tab='{}-districts'.format(self.type)
    )
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }
