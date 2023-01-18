from onegov.ballot import ElectionCompound
from onegov.core.security import Public
from onegov.election_day import ElectionDayApp
from onegov.election_day.layouts import ElectionCompoundLayout
from onegov.election_day.utils import add_last_modified_header
from onegov.election_day.utils.parties import get_party_results
from onegov.election_day.utils.parties import get_party_results_seat_allocation
from onegov.election_day.utils.parties import get_party_results_vertical_data


@ElectionDayApp.json(
    model=ElectionCompound,
    name='seat-allocation-data',
    permission=Public
)
def view_election_compound_seat_allocation_data(self, request):

    """ Retuns the data used for the grouped bar diagram showing the seat
    allocation.

    """

    return get_party_results_vertical_data(self)


@ElectionDayApp.html(
    model=ElectionCompound,
    name='seat-allocation-chart',
    template='embed.pt',
    permission=Public
)
def view_election_compound_seat_allocation_chart(self, request):

    """" View the seat allocation as grouped bar chart. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    return {
        'model': self,
        'layout': ElectionCompoundLayout(self, request),
        'type': 'seat-allocation-chart',
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='seat-allocation',
    template='election_compound/seat_allocation.pt',
    permission=Public
)
def view_election_compound_seat_allocation(self, request):

    """" The main view. """

    layout = ElectionCompoundLayout(self, request, 'seat-allocation')

    party_years, parties = get_party_results(self)
    seat_allocations = get_party_results_seat_allocation(party_years, parties)

    return {
        'election_compound': self,
        'layout': layout,
        'seat_allocations': seat_allocations,
        'party_years': party_years,
    }


@ElectionDayApp.svg_file(model=ElectionCompound, name='seat-allocation-svg')
def view_election_compound_seat_allocation_svg(self, request):

    """ View the seat allocation as SVG. """

    layout = ElectionCompoundLayout(self, request, 'seat-allocation')
    return {
        'path': layout.svg_path,
        'name': layout.svg_name
    }


@ElectionDayApp.html(
    model=ElectionCompound,
    name='seat-allocation-table',
    template='embed.pt',
    permission=Public
)
def view_election_compound_seat_allocation_table(self, request):

    """" Displays the seat allocation as standalone table. """

    @request.after
    def add_last_modified(response):
        add_last_modified_header(response, self.last_modified)

    party_years, parties = get_party_results(self)
    seat_allocations = get_party_results_seat_allocation(party_years, parties)

    return {
        'election_compound': self,
        'layout': ElectionCompoundLayout(self, request, 'seat-allocation'),
        'type': 'election-compound-table',
        'scope': 'seat-allocation',
        'seat_allocations': seat_allocations,
        'party_years': party_years,
    }
