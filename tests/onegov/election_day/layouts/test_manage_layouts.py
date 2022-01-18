from datetime import date
from freezegun import freeze_time
from onegov.ballot import Election
from onegov.ballot import ElectionCollection
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundCollection
from onegov.ballot import Vote
from onegov.ballot import VoteCollection
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import ScreenCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.layouts import ManageDataSourceItemsLayout
from onegov.election_day.layouts import ManageDataSourcesLayout
from onegov.election_day.layouts import ManageElectionCompoundsLayout
from onegov.election_day.layouts import ManageElectionsLayout
from onegov.election_day.layouts import ManageScreensLayout
from onegov.election_day.layouts import ManageSubscribersLayout
from onegov.election_day.layouts import ManageUploadTokensLayout
from onegov.election_day.layouts import ManageVotesLayout
from tests.onegov.election_day.common import DummyRequest


def test_manage_layouts(session):
    # Votes
    layout = ManageVotesLayout(
        VoteCollection(session),
        DummyRequest()
    )
    assert layout.manage_model_link == 'VoteCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', True, []),
        ('Elections', '', False, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', False, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
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
        ('Elections', '', False, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', False, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
            ('Wabsti data sources', 'DataSourceCollection/archive', False, []),
        ]),
        ('Subscribers', '', False, [
            ('SMS subscribers', 'SmsSubscriberCollection/archive', False, []),
            (
                'Email subscribers',
                'EmailSubscriberCollection/archive',
                False,
                []
            ),
            (
                'Trigger notifications',
                'DummyPrincipal/trigger-notifications',
                False,
                []
            )
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
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
        ('Elections', '', True, [
            ('Elections', 'ElectionCollection/archive', True, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', False, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
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
        ('Elections', '', True, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                True,
                []
            )
        ]),
        ('Import configuration', '', False, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Compounds of elections', 'ElectionCompoundCollection/archive', '')
    ]

    # Upload tokens
    layout = ManageUploadTokensLayout(
        UploadTokenCollection(session),
        DummyRequest()
    )
    assert layout.manage_model_link == 'UploadTokenCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', '', False, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', True, [
            ('Upload tokens', 'UploadTokenCollection/archive', True, []),
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Upload tokens', 'UploadTokenCollection/archive', '')
    ]

    # Wabsti data sources
    layout = ManageDataSourcesLayout(
        DataSourceCollection(session),
        DummyRequest()
    )
    layout.principal.wabsti_import = True
    assert layout.manage_model_link == 'DataSourceCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', '', False, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', True, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
            ('Wabsti data sources', 'DataSourceCollection/archive', True, []),
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Wabsti data sources', 'DataSourceCollection/archive', '')
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
        ('Elections', '', False, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', True, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
            ('Wabsti data sources', 'DataSourceCollection/archive', True, []),
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Wabsti data sources', 'DataSourceCollection/archive', ''),
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
        ('Elections', '', False, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', False, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
        ]),
        ('Subscribers', '', True, [
            (
                'Email subscribers',
                'EmailSubscriberCollection/archive',
                True,
                []
            ),
            (
                'Trigger notifications',
                'DummyPrincipal/trigger-notifications',
                False,
                []
            )
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
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
        ('Elections', '', False, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', False, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
        ]),
        ('Subscribers', '', True, [
            ('SMS subscribers', 'SmsSubscriberCollection/archive', True, []),
            (
                'Trigger notifications',
                'DummyPrincipal/trigger-notifications',
                False,
                []
            )
        ]),
        ('Screens', 'ScreenCollection/archive', False, [])
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('SMS subscribers', 'SmsSubscriberCollection/archive', '')
    ]

    # Screens
    layout = ManageScreensLayout(
        ScreenCollection(session),
        DummyRequest()
    )
    assert layout.manage_model_link == 'ScreenCollection/archive'
    assert layout.menu == [
        ('Votes', 'VoteCollection/archive', False, []),
        ('Elections', '', False, [
            ('Elections', 'ElectionCollection/archive', False, []),
            (
                'Compounds of elections',
                'ElectionCompoundCollection/archive',
                False,
                []
            )
        ]),
        ('Import configuration', '', False, [
            ('Upload tokens', 'UploadTokenCollection/archive', False, []),
        ]),
        ('Screens', 'ScreenCollection/archive', True, [])
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Screens', 'ScreenCollection/archive', '')
    ]

    # Admin
    layout = ManageScreensLayout(None, DummyRequest(is_secret=True))
    assert layout.menu[-1] == (
        'Administration',
        '',
        False,
        [
            (
                'Update archived results',
                'DummyPrincipal/update-results',
                False,
                []
            ),
            (
                'Clear cache',
                'DummyPrincipal/clear-cache',
                False,
                []
            )
        ]
    )


def test_manage_layouts_clear_media(election_day_app_zg):
    session = election_day_app_zg.session()
    request = DummyRequest(app=election_day_app_zg, session=session)
    filestorage = election_day_app_zg.filestorage
    filestorage.makedir('svg')
    filestorage.makedir('pdf')

    with freeze_time('2016-08-31'):
        date_ = date(2010, 1, 1)
        domain = 'canton'
        session.add(Election(title='item', domain=domain, date=date_))
        session.add(ElectionCompound(title='item', domain=domain, date=date_))
        session.add(Vote(title='item', domain=domain, date=date_))
        session.flush()

    hash = '4a33eacd5fa65f2b2e2871cd131286b53c415b131666d71173bb6e3fe59361b3'
    timestamp = 1472601600
    for path in (
        f'pdf/election-{hash}.{timestamp}.de_CH.pdf',
        f'svg/election-{hash}.{timestamp}.lists.any.svg',
        f'svg/election-{hash}.{timestamp}.parties-panachage.any.svg',
        f'svg/election-{hash}.{timestamp-5}.parties-panachage.any.svg',
        f'pdf/elections-{hash}.{timestamp}.de_CH.pdf',
        f'svg/elections-{hash}.{timestamp}.mandate-allocation.any.svg',
        f'svg/elections-{hash}.{timestamp-5}.mandate-allocation.any.svg',
        f'pdf/vote-{hash}.{timestamp}.rm_CH.pdf',
        f'svg/vote-{hash}.{timestamp}.proposal-entities.any.svg',
        f'svg/vote-{hash}.{timestamp-5}.proposal-entities.any.svg',
    ):
        filestorage.touch(path)

    model = session.query(Election).one()
    layout = ManageElectionsLayout(model, request)
    assert layout.clear_media() == 3

    model = session.query(ElectionCompound).one()
    layout = ManageElectionCompoundsLayout(model, request)
    assert layout.clear_media() == 2

    model = session.query(Vote).one()
    layout = ManageVotesLayout(model, request)
    assert layout.clear_media() == 2
