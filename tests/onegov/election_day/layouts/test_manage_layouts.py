from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.election_day.collections import DataSourceCollection
from onegov.election_day.collections import DataSourceItemCollection
from onegov.election_day.collections import ElectionCollection
from onegov.election_day.collections import ElectionCompoundCollection
from onegov.election_day.collections import EmailSubscriberCollection
from onegov.election_day.collections import ScreenCollection
from onegov.election_day.collections import SmsSubscriberCollection
from onegov.election_day.collections import UploadTokenCollection
from onegov.election_day.collections import VoteCollection
from onegov.election_day.layouts import ManageDataSourceItemsLayout
from onegov.election_day.layouts import ManageDataSourcesLayout
from onegov.election_day.layouts import ManageElectionCompoundsLayout
from onegov.election_day.layouts import ManageElectionsLayout
from onegov.election_day.layouts import ManageScreensLayout
from onegov.election_day.layouts import ManageSubscribersLayout
from onegov.election_day.layouts import ManageUploadTokensLayout
from onegov.election_day.layouts import ManageVotesLayout
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import Vote
from tests.onegov.election_day.common import DummyRequest


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.layouts import DefaultLayout
    from onegov.election_day.types import DomainOfInfluence
    from sqlalchemy.orm import Session
    from ..conftest import TestApp


def test_manage_layouts(session: Session) -> None:
    layout: DefaultLayout
    # Votes
    layout = ManageVotesLayout(
        VoteCollection(session),
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', False, [
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

    # ... with full menu
    layout = ManageVotesLayout(
        VoteCollection(session),
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', False, [
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
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', False, [
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
        ('Elections', 'ElectionCollection/archive', '')
    ]

    # Election compounds
    layout = ManageElectionCompoundsLayout(
        ElectionCompoundCollection(session),
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', False, [
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
        ('Compounds of elections', 'ElectionCompoundCollection/archive', '')
    ]

    # Upload tokens
    layout = ManageUploadTokensLayout(
        UploadTokenCollection(session),
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', False, [
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
        ('Upload tokens', 'UploadTokenCollection/archive', '')
    ]

    # Wabsti data sources
    layout = ManageDataSourcesLayout(
        DataSourceCollection(session),
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', False, [
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
        ('Wabsti data sources', 'DataSourceCollection/archive', '')
    ]

    # Data source items
    layout = ManageDataSourceItemsLayout(
        DataSourceItemCollection(session, 'source'),  # type: ignore[arg-type]
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', False, [
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
        ('Wabsti data sources', 'DataSourceCollection/archive', ''),
        ('Mappings', 'DataSourceItemCollection/source', '')
    ]

    # Email subscribers
    layout = ManageSubscribersLayout(
        EmailSubscriberCollection(session),
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', True, [
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
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', True, [
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
        DummyRequest()  # type: ignore[arg-type]
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
        ('Notifications', '', False, [
            (
                'Trigger notifications',
                'DummyPrincipal/trigger-notifications',
                False,
                []
            )
        ]),
        ('Screens', 'ScreenCollection/archive', True, [])
    ]
    assert layout.breadcrumbs == [
        ('Manage', 'VoteCollection/archive', 'unavailable'),
        ('Screens', 'ScreenCollection/archive', '')
    ]

    # Admin
    layout = ManageScreensLayout(None, DummyRequest(is_secret=True))  # type: ignore[arg-type]
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


def test_manage_layouts_clear_media(election_day_app_zg: TestApp) -> None:
    session = election_day_app_zg.session()
    request: Any = DummyRequest(app=election_day_app_zg, session=session)
    filestorage = election_day_app_zg.filestorage
    assert filestorage is not None
    filestorage.makedir('svg')
    filestorage.makedir('pdf')

    with freeze_time('2016-08-31'):
        date_ = date(2010, 1, 1)
        domain: DomainOfInfluence = 'canton'
        session.add(Election(title='item', domain=domain, date=date_))
        session.add(ElectionCompound(title='item', domain=domain, date=date_))
        session.add(Vote(title='item', domain=domain, date=date_))
        session.flush()

    hash = '4a33eacd5fa65f2b2e2871cd131286b53c415b131666d71173bb6e3fe59361b3'
    timestamp = 1472601600
    for path in (
        f'pdf/election-{hash}.{timestamp}.de_CH.pdf',
        f'svg/election-{hash}.{timestamp}.lists.de_CH.svg',
        f'svg/election-{hash}.{timestamp}.parties-panachage.de_CH.svg',
        f'svg/election-{hash}.{timestamp - 5}.parties-panachage.de_CH.svg',
        f'pdf/elections-{hash}.{timestamp}.de_CH.pdf',
        f'pdf/vote-{hash}.{timestamp}.rm_CH.pdf',
        f'svg/vote-{hash}.{timestamp}.proposal-entities.de_CH.svg',
        f'svg/vote-{hash}.{timestamp - 5}.proposal-entities.de_CH.svg',
    ):
        filestorage.touch(path)

    model: Election | ElectionCompound | Vote
    layout: DefaultLayout
    model = session.query(Election).one()
    layout = ManageElectionsLayout(model, request)
    assert layout.clear_media() == 3

    model = session.query(ElectionCompound).one()
    layout = ManageElectionCompoundsLayout(model, request)
    assert layout.clear_media() == 1

    model = session.query(Vote).one()
    layout = ManageVotesLayout(model, request)
    assert layout.clear_media() == 2
