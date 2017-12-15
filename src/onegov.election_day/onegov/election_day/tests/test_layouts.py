from datetime import date
from freezegun import freeze_time
from onegov.ballot import Ballot
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.ballot import ComplexVote
from onegov.ballot import ElectionCollection
from onegov.ballot import VoteCollection
from onegov.election_day.layouts import ElectionLayout
from onegov.election_day.layouts import DefaultLayout
from onegov.election_day.layouts import ManageDataSourceItemsLayout
from onegov.election_day.layouts import ManageDataSourcesLayout
from onegov.election_day.layouts import ManageElectionsLayout
from onegov.election_day.layouts import ManageSubscribersLayout
from onegov.election_day.layouts import ManageVotesLayout
from onegov.election_day.layouts import VoteLayout
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.tests import DummyRequest
from unittest.mock import Mock


def test_layout_principal():
    request = DummyRequest()
    model = Vote()
    layout = DefaultLayout(model, request)

    assert layout.principal == request.app.principal


def test_layout_links():
    layout_de = DefaultLayout(None, DummyRequest(locale='de'))
    layout_en = DefaultLayout(None, DummyRequest(locale='en'))
    layout_fr = DefaultLayout(None, DummyRequest(locale='fr'))
    layout_it = DefaultLayout(None, DummyRequest(locale='it'))
    layout_rm = DefaultLayout(None, DummyRequest(locale='rm'))

    assert layout_de.homepage_link == 'DummyPrincipal/archive'
    assert layout_en.homepage_link == 'DummyPrincipal/archive'

    assert layout_de.manage_link == 'VoteCollection/archive'
    assert layout_en.manage_link == 'VoteCollection/archive'

    assert layout_de.get_topojson_link('ag', 2015)
    assert layout_en.get_topojson_link('ag', 2015)

    assert layout_de.terms_link == 'https://opendata.swiss/de/terms-of-use'
    assert layout_en.terms_link == 'https://opendata.swiss/en/terms-of-use'
    assert layout_fr.terms_link == 'https://opendata.swiss/fr/terms-of-use'
    assert layout_it.terms_link == 'https://opendata.swiss/it/terms-of-use'
    assert layout_rm.terms_link == 'https://opendata.swiss/rm/terms-of-use'

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
        'format__de.md'
    )
    assert layout_en.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__en.md'
    )
    assert layout_fr.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__fr.md'
    )
    assert layout_it.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__it.md'
    )
    assert layout_rm.format_description_link == (
        'https://github.com/OneGov/onegov.election_day/blob/master/docs/'
        'format__rm.md'
    )

    assert layout_de.login_link == 'Auth/login'
    assert layout_de.logout_link is None

    layout_de = DefaultLayout(
        None, DummyRequest(locale='de', is_logged_in=True)
    )

    assert layout_de.login_link is None
    assert layout_de.logout_link == 'Auth/logout'


def test_elections_layout(session):
    layout = ElectionLayout(None, DummyRequest())

    assert layout.all_tabs == (
        'lists', 'candidates', 'connections', 'parties', 'statistics',
        'panachage', 'data'
    )

    assert layout.title() == ''
    assert layout.title('undefined') == ''
    assert layout.title('lists') == 'Lists'
    assert layout.title('candidates') == 'Candidates'
    assert layout.title('connections') == 'List connections'
    assert layout.title('parties') == 'Parties'
    assert layout.title('statistics') == 'Election statistics'
    assert layout.title('data') == 'Downloads'
    assert layout.title('panachage') == 'Panachage'

    layout = ElectionLayout(Election(type='majorz'), DummyRequest())
    assert layout.majorz
    assert not layout.proporz
    assert layout.main_view == 'Election/candidates'
    assert list(layout.menu) == []
    assert not layout.tacit

    layout = ElectionLayout(Election(type='proporz'), DummyRequest())
    assert not layout.majorz
    assert layout.proporz
    assert layout.main_view == 'Election/lists'
    assert list(layout.menu) == []
    assert not layout.tacit

    layout = ElectionLayout(
        Election(type='majorz', tacit=True), DummyRequest()
    )
    assert layout.tacit

    with freeze_time("2014-01-01 12:00"):
        election = Election(
            title="Election",
            domain='federation',
            type='proporz',
            date=date(2011, 1, 1),
        )
        session.add(election)
        session.flush()
        ts = (
            '4b9e99d2bd5e48d9a569e5f82175d1d2ed59105f8d82a12dc51b673ff12dc1f2'
            '.1388577600'
        )

        request = DummyRequest()
        request.app.filestorage = Mock()

        layout = ElectionLayout(election, request)
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.None.any.svg'.format(ts)
        assert layout.svg_link == 'Election/None-svg'
        assert layout.svg_name == 'election.svg'

        layout = ElectionLayout(election, request, 'lists')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.lists.any.svg'.format(ts)
        assert layout.svg_link == 'Election/lists-svg'
        assert layout.svg_name == 'election-lists.svg'

        layout = ElectionLayout(election, request, 'candidates')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.candidates.any.svg'.format(
            ts
        )
        assert layout.svg_link == 'Election/candidates-svg'
        assert layout.svg_name == 'election-candidates.svg'

        layout = ElectionLayout(election, request, 'connections')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.connections.any.svg'.format(
            ts
        )
        assert layout.svg_link == 'Election/connections-svg'
        assert layout.svg_name == 'election-list-connections.svg'

        layout = ElectionLayout(election, request, 'panachage')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.panachage.any.svg'.format(
            ts
        )
        assert layout.svg_link == 'Election/panachage-svg'
        assert layout.svg_name == 'election-panachage.svg'

        layout = ElectionLayout(election, request, 'parties')
        assert layout.pdf_path == 'pdf/election-{}.de.pdf'.format(ts)
        assert layout.svg_path == 'svg/election-{}.parties.any.svg'.format(ts)
        assert layout.svg_link == 'Election/parties-svg'
        assert layout.svg_name == 'election-parties.svg'


def test_votes_layout(session):
    layout = VoteLayout(Vote(), DummyRequest())

    assert layout.title() == 'Proposal'
    assert layout.title('undefined') == ''
    assert layout.title('proposal') == 'Proposal'
    assert layout.title('counter-proposal') == 'Counter Proposal'
    assert layout.title('tie-breaker') == 'Tie-Breaker'
    assert layout.title('data') == 'Downloads'

    assert list(layout.menu) == []

    with freeze_time("2014-01-01 12:00"):
        vote = ComplexVote(
            title="Vote",
            domain='federation',
            date=date(2011, 1, 1),
        )
        proposal = Ballot(type="proposal")
        vote.ballots.append(proposal)
        counter = Ballot(type="counter-proposal")
        vote.ballots.append(counter)
        tie = Ballot(type="tie-breaker")
        vote.ballots.append(tie)
        session.add(vote)
        session.flush()

        ts = '1388577600'
        vh = 'ab274474a6aa82c100dddca63977facb556f66f489fb558c044a456f9ba919ce'

        request = DummyRequest()
        request.app.filestorage = Mock()

        layout = VoteLayout(vote, request)
        assert layout.pdf_path == 'pdf/vote-{}.{}.de.pdf'.format(vh, ts)
        assert layout.svg_path == 'svg/ballot-{}.{}.map.de.svg'.format(
            proposal.id, ts
        )
        assert layout.svg_link == 'Ballot/svg'
        assert layout.svg_name == 'vote-proposal.svg'

        layout = VoteLayout(vote, request, 'counter-proposal')
        assert layout.pdf_path == 'pdf/vote-{}.{}.de.pdf'.format(vh, ts)
        assert layout.svg_path == 'svg/ballot-{}.{}.map.de.svg'.format(
            counter.id, ts
        )
        assert layout.svg_link == 'Ballot/svg'
        assert layout.svg_name == 'vote-counter-proposal.svg'

        layout = VoteLayout(vote, request, 'tie-breaker')
        assert layout.pdf_path == 'pdf/vote-{}.{}.de.pdf'.format(vh, ts)
        assert layout.svg_path == 'svg/ballot-{}.{}.map.de.svg'.format(
            tie.id, ts
        )
        assert layout.svg_link == 'Ballot/svg'
        assert layout.svg_name == 'vote-tie-breaker.svg'


def test_manage_layout(session):
    # Votes
    layout = ManageVotesLayout(
        VoteCollection(session),
        DummyRequest()
    )
    assert layout.manage_model_link == 'VoteCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', 'active'),
        ('Elections', 'ElectionCollection/archive', '')
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Votes', 'VoteCollection/archive', '')
    ]

    # ... with full menu
    layout = ManageVotesLayout(
        VoteCollection(session),
        DummyRequest()
    )
    layout.principal.sms_notification = 'http://example.com'
    layout.principal.email_notification = True
    layout.principal.wabsti_import = True
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', 'active'),
        ('Elections', 'ElectionCollection/archive', ''),
        ('Data sources', 'DataSourceCollection/archive', ''),
        ('SMS subscribers', 'SmsSubscriberCollection/archive', ''),
        ('Email subscribers', 'EmailSubscriberCollection/archive', ''),
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Votes', 'VoteCollection/archive', '')
    ]

    # Elections
    layout = ManageElectionsLayout(
        ElectionCollection(session),
        DummyRequest()
    )
    assert layout.manage_model_link == 'ElectionCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', 'active')
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Elections', 'ElectionCollection/archive', '')
    ]

    # Data sources
    layout = ManageDataSourcesLayout(
        DataSourceCollection(session),
        DummyRequest()
    )
    layout.principal.wabsti_import = True
    assert layout.manage_model_link == 'DataSourceCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', ''),
        ('Data sources', 'DataSourceCollection/archive', 'active'),
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Data sources', 'DataSourceCollection/archive', '')
    ]

    # Data source items
    layout = ManageDataSourceItemsLayout(
        DataSourceItemCollection(session, 'source'),
        DummyRequest()
    )
    layout.principal.wabsti_import = True
    assert layout.manage_model_link == 'DataSourceItemCollection/source'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', ''),
        ('Data sources', 'DataSourceCollection/archive', 'active'),
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Data sources', 'DataSourceCollection/archive', ''),
        ('Mappings', 'DataSourceItemCollection/source', '')
    ]

    # Email subscribers
    layout = ManageSubscribersLayout(
        EmailSubscriberCollection(session),
        DummyRequest()
    )
    layout.principal.email_notification = True
    assert layout.manage_model_link == 'EmailSubscriberCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', ''),
        ('Email subscribers', 'EmailSubscriberCollection/archive', 'active')
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Email subscribers', 'EmailSubscriberCollection/archive', '')
    ]

    # SMS subscribers
    layout = ManageSubscribersLayout(
        SmsSubscriberCollection(session),
        DummyRequest()
    )
    layout.principal.sms_notification = 'http://example.com'
    assert layout.manage_model_link == 'SmsSubscriberCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', ''),
        ('SMS subscribers', 'SmsSubscriberCollection/archive', 'active')
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('SMS subscribers', 'SmsSubscriberCollection/archive', '')
    ]
