from datetime import date
from datetime import datetime
from freezegun import freeze_time
from onegov.gazette.layout import Layout
from onegov.gazette.models import Issue
from onegov.gazette.models import GazetteNotice
from pytest import raises
from sedate import standardize_date


class DummyPrincipal(object):
    def __init__(self, publishing=True):
        self.publishing = publishing


class DummyApp(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal

    def session(self):
        return self._session


class DummyRequest(object):
    def __init__(self, session, principal=None):
        self.app = DummyApp(session, principal)
        self.locale = 'de_CH'
        self.session = session
        self._is_secret = False
        self._is_private = False
        self._is_personal = False

    def is_secret(self, model):
        return self._is_secret

    def is_private(self, model):
        return self._is_private

    def is_personal(self, model):
        return self._is_personal

    def include(self, resource):
        pass

    def link(self, target, name=''):
        return '/{}/{}/'.format(
            target.__class__.__name__ if target else '', name
        ).replace('///', '/',).replace('//', '/',)

    def translate(self, text):
        return text.interpolate()

    def new_csrf_token(self):
        return 'XXX'


def test_layout_links():
    layout = Layout(None, DummyRequest(None))
    assert layout.homepage_link == '/'
    assert layout.manage_users_link == '/UserCollection/'
    assert layout.manage_groups_link == '/UserGroupCollection/'
    assert layout.manage_organizations_link == '/OrganizationCollection/'
    assert layout.manage_categories_link == '/CategoryCollection/'
    assert layout.manage_issues_link == '/IssueCollection/'
    assert layout.manage_notices_link == '/GazetteNoticeCollection/'
    assert layout.dashboard_link == '/dashboard/'
    assert layout.dashboard_or_notices_link == '/dashboard/'


def test_sortable_url_template():
    layout = Layout(None, DummyRequest(None))
    assert layout.sortable_url_template == '/OrganizationMove/?csrf-token=XXX'


def test_layout_menu():
    request = DummyRequest(None, DummyPrincipal())
    layout = Layout(None, request)

    assert layout.menu == []

    request._is_personal = True
    assert layout.menu == [
        ('Dashboard', '/DummyPrincipal/dashboard/', False, []),
        ('Published Official Notices', '/GazetteNoticeCollection/', False, [])
    ]

    request._is_private = True
    assert layout.menu == [
        ('Official Notices', '/GazetteNoticeCollection/', False, []),
        ('Manage', None, False, [
            ('Issues', '/IssueCollection/', False, []),
            ('Organizations', '/OrganizationCollection/', False, []),
            ('Categories', '/CategoryCollection/', False, []),
            ('Groups', '/UserGroupCollection/', False, []),
            ('Users', '/UserCollection/', False, []),
        ]),
        ('Statistics', '/GazetteNoticeCollection/statistics/', False, []),
    ]

    request._is_secret = True
    assert layout.menu == [
        ('Official Notices', '/GazetteNoticeCollection/', False, []),
        ('Manage', None, False, [
            ('Issues', '/IssueCollection/', False, []),
            ('Organizations', '/OrganizationCollection/', False, []),
            ('Categories', '/CategoryCollection/', False, []),
            ('Groups', '/UserGroupCollection/', False, []),
            ('Users', '/UserCollection/', False, []),
        ]),
        ('Statistics', '/GazetteNoticeCollection/statistics/', False, []),
    ]


def test_current_issue(session, issues):
    with freeze_time("2017-10-10 11:00"):
        layout = Layout(None, DummyRequest(session))
        assert layout.current_issue.name == '2017-41'


def test_layout_format(session, principal):
    request = DummyRequest(session, principal)
    layout = Layout(None, request)

    # Date
    assert layout.principal.time_zone == 'Europe/Zurich'
    assert layout.format_date(date(2019, 1, 2), 'date') == '02.01.2019'
    assert layout.format_date(datetime(2019, 1, 2, 12), 'date') == '02.01.2019'
    assert layout.format_date(datetime(2019, 1, 2, 12), 'date_long') == \
        '2. Januar 2019'
    assert layout.format_date(datetime(2019, 1, 2, 12), 'datetime') == \
        '02.01.2019 12:00'
    assert layout.format_date(
        standardize_date(datetime(2019, 1, 2, 12, 0), 'UTC'), 'date'
    ) == '02.01.2019'
    assert layout.format_date(
        standardize_date(datetime(2019, 1, 2, 12, 0), 'UTC'), 'datetime'
    ) == '02.01.2019 13:00'

    # Issue
    with raises(AssertionError):
        layout.format_issue(None)
    with raises(AssertionError):
        layout.format_issue('')

    assert layout.format_issue(Issue()) == 'No. , '

    assert layout.format_issue(
        Issue(number=1, date=date(2017, 1, 2))
    ) == 'No. 1, 02.01.2017'
    assert layout.format_issue(
        Issue(number=1, date=date(2017, 1, 2)),
        date_format='date_with_weekday'
    ) == 'No. 1, Montag 02.01.2017'
    assert layout.format_issue(
        Issue(name='2017-1', number=1, date=date(2017, 1, 2)),
        notice=GazetteNotice()
    ) == 'No. 1, 02.01.2017'
    assert layout.format_issue(
        Issue(name='2017-1', number=1, date=date(2017, 1, 2)),
        notice=GazetteNotice(issues=['2017-1'])
    ) == 'No. 1, 02.01.2017'
    assert layout.format_issue(
        Issue(name='2017-1', number=1, date=date(2017, 1, 2)),
        notice=GazetteNotice(_issues={'2017-1': 10})
    ) == 'No. 1, 02.01.2017 / 10'

    # Text
    assert layout.format_text(None) == ''
    assert layout.format_text('abc') == 'abc'
    assert layout.format_text('a\nb\r\nc') == 'a<br>b<br>c'
