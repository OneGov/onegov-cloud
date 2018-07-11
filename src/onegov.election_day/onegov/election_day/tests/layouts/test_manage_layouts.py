from onegov.ballot import ElectionCollection
from onegov.ballot import ElectionCompoundCollection
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
        ('Votes', 'VoteCollection/archive', True, []),
        ('Elections', 'ElectionCollection/archive', False, []),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            False,
            []
        )
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
        ('Votes', 'VoteCollection/archive', True, []),
        ('Elections', 'ElectionCollection/archive', False, []),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            False,
            []
        ),
        ('Data sources', 'DataSourceCollection/archive', False, []),
        ('Subscribers', '', False, [
            ('SMS subscribers', 'SmsSubscriberCollection/archive', False, []),
            (
                'Email subscribers',
                'EmailSubscriberCollection/archive',
                False,
                []
            )
        ])
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
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', 'ElectionCollection/archive', True, []),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            False,
            []
        )
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Elections', 'ElectionCollection/archive', '')
    ]

    # Election compounds
    layout = ManageElectionCompoundsLayout(
        ElectionCompoundCollection(session),
        DummyRequest()
    )
    assert layout.manage_model_link == 'ElectionCompoundCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', 'ElectionCollection/archive', False, []),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            True,
            []
        )
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Compounds of elections', 'ElectionCompoundCollection/archive', '')
    ]

    # Data sources
    layout = ManageDataSourcesLayout(
        DataSourceCollection(session),
        DummyRequest()
    )
    layout.principal.wabsti_import = True
    assert layout.manage_model_link == 'DataSourceCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', 'ElectionCollection/archive', False, []),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            False,
            []
        ),
        ('Data sources', 'DataSourceCollection/archive', True, []),
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
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', 'ElectionCollection/archive', False, []),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            False,
            []
        ),
        ('Data sources', 'DataSourceCollection/archive', True, []),
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
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', 'ElectionCollection/archive', False, []),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            False,
            []
        ),
        ('Email subscribers', 'EmailSubscriberCollection/archive', True, [])
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
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', 'ElectionCollection/archive', False, []),
        (
            'Compounds of elections',
            'ElectionCompoundCollection/archive',
            False,
            []
        ),
        ('SMS subscribers', 'SmsSubscriberCollection/archive', True, [])
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('SMS subscribers', 'SmsSubscriberCollection/archive', '')
    ]
