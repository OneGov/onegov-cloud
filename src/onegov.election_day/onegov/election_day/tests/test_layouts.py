from onegov.ballot import Election, Vote
from onegov.election_day.layout import ElectionsLayout
from onegov.election_day.layout import Layout
from onegov.election_day.layout import ManageElectionsLayout
from onegov.election_day.layout import ManageLayout
from onegov.election_day.layout import ManageVotesLayout
from onegov.election_day.layout import VotesLayout
from onegov.election_day.tests import DummyRequest


def test_layout_principal():
    request = DummyRequest()
    model = Vote()
    layout = Layout(model, request)

    assert layout.principal == request.app.principal


def test_layout_links():
    layout_de = Layout(None, DummyRequest(locale='de'))
    layout_en = Layout(None, DummyRequest(locale='en'))
    layout_fr = Layout(None, DummyRequest(locale='fr'))
    layout_it = Layout(None, DummyRequest(locale='it'))
    layout_rm = Layout(None, DummyRequest(locale='rm'))

    assert layout_de.homepage_link == 'DummyPrincipal/archive'
    assert layout_en.homepage_link == 'DummyPrincipal/archive'

    assert layout_de.subscribe_link == 'DummyPrincipal/subscribe'
    assert layout_en.subscribe_link == 'DummyPrincipal/subscribe'

    assert layout_de.unsubscribe_link == 'DummyPrincipal/unsubscribe'
    assert layout_en.unsubscribe_link == 'DummyPrincipal/unsubscribe'

    assert layout_de.manage_link == 'VoteCollection/archive'
    assert layout_en.manage_link == 'VoteCollection/archive'

    assert layout_de.get_topojson_link('ag', 2015)
    assert layout_en.get_topojson_link('ag', 2015)

    assert layout_de.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_de.md'
    )
    assert layout_en.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_en.md'
    )
    assert layout_fr.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_fr.md'
    )
    assert layout_it.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_it.md'
    )
    assert layout_rm.opendata_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'open_data_rm.md'
    )

    assert layout_de.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format_de.md'
    )
    assert layout_en.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format_en.md'
    )
    assert layout_fr.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format_fr.md'
    )
    assert layout_it.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format_it.md'
    )
    assert layout_rm.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format_rm.md'
    )

    assert layout_de.login_link == 'Auth/login'
    assert layout_de.logout_link is None

    layout_de = Layout(None, DummyRequest(locale='de', is_logged_in=True))

    assert layout_de.login_link is None
    assert layout_de.logout_link == 'Auth/logout'


def test_elections_layout():
    layout = ElectionsLayout(None, DummyRequest())

    assert layout.all_tabs == (
        'lists', 'candidates', 'districts', 'connections', 'parties',
        'statistics', 'panachage', 'data'
    )

    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('lists') == 'Lists'
    assert layout.title('candidates') == 'Candidates'
    assert layout.title('districts') == 'Electoral Districts'
    assert layout.title('connections') == 'List connections'
    assert layout.title('parties') == 'Parties'
    assert layout.title('statistics') == 'Election statistics'
    assert layout.title('data') == 'Open Data'
    assert layout.title('panachage') == 'Panachage'

    layout = ElectionsLayout(Election(type='majorz'), DummyRequest())
    assert layout.majorz
    assert not layout.proporz
    assert layout.main_view == 'Election/candidates'
    assert not layout.has_results
    assert not layout.counted
    assert list(layout.menu) == []

    layout = ElectionsLayout(Election(type='proporz'), DummyRequest())
    assert not layout.majorz
    assert layout.proporz
    assert layout.main_view == 'Election/lists'
    assert not layout.has_results
    assert not layout.counted
    assert list(layout.menu) == []


def test_votes_layout():
    layout = VotesLayout(Vote(), DummyRequest())

    assert layout.title() == 'Proposal'
    assert layout.title('undefined') == ''
    assert layout.title('proposal') == 'Proposal'
    assert layout.title('counter-proposal') == 'Counter Proposal'
    assert layout.title('tie-breaker') == 'Tie-Breaker'
    assert layout.title('data') == 'Open Data'

    assert not layout.has_results
    assert not layout.counted
    assert list(layout.menu) == []


def test_manage_layout():
    layout = ManageLayout(Vote(), DummyRequest())

    assert layout.manage_model_link == 'Vote/None'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', '')
    ]

    layout = ManageLayout(Election(), DummyRequest())

    assert layout.manage_model_link == 'Election/None'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', '')
    ]

    layout = ManageVotesLayout(Vote(), DummyRequest())
    assert layout.manage_model_link == 'VoteCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', 'active'),
        ('Elections', 'ElectionCollection/archive', '')
    ]

    layout = ManageElectionsLayout(Election(), DummyRequest())
    assert layout.manage_model_link == 'ElectionCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', 'active')
    ]
