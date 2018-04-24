from onegov.ballot import ElectionCollection
from onegov.ballot import VoteCollection
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.layouts import ManageDataSourceItemsLayout
from onegov.election_day.layouts import ManageDataSourcesLayout
from onegov.election_day.layouts import ManageElectionCompoundsLayout
from onegov.election_day.layouts import ManageElectionsLayout
from onegov.election_day.layouts import ManageSubscribersLayout
from onegov.election_day.layouts import ManageVotesLayout
from onegov.election_day.tests.common import DummyRequest


def test_manage_layouts(session):
    # Votes
    layout = ManageVotesLayout(
        VoteCollection(session),
        DummyRequest()
    )
    assert layout.manage_model_link == 'VoteCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', 'active'),
        ('Elections', 'ElectionCollection/archive', ''),
        ('Compounds of elections', 'ElectionCompoundCollection/archive', '')
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
        ('Compounds of elections', 'ElectionCompoundCollection/archive', ''),
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
        ('Elections', 'ElectionCollection/archive', 'active'),
        ('Compounds of elections', 'ElectionCompoundCollection/archive', '')
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Elections', 'ElectionCollection/archive', '')
    ]

    # Election compounds
    layout = ManageElectionCompoundsLayout(
        ElectionCollection(session),
        DummyRequest()
    )
    assert layout.manage_model_link == 'ElectionCompoundCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', ''),
        ('Elections', 'ElectionCollection/archive', ''),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            'active'
        )
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Compounds of elections', 'ElectionCollection/archive', '')
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
        ('Compounds of elections', 'ElectionCompoundCollection/archive', ''),
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
        ('Compounds of elections', 'ElectionCompoundCollection/archive', ''),
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
        ('Compounds of elections', 'ElectionCompoundCollection/archive', ''),
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
        ('Compounds of elections', 'ElectionCompoundCollection/archive', ''),
        ('SMS subscribers', 'SmsSubscriberCollection/archive', 'active')
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('SMS subscribers', 'SmsSubscriberCollection/archive', '')
    ]
