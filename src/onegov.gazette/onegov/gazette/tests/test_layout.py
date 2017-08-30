from onegov.gazette.layout import Layout
from onegov.gazette.models import Issue
from pytest import raises


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


def test_layout_links():
    layout = Layout(None, DummyRequest(None))
    assert layout.homepage_link == '/'
    assert layout.manage_link == '/'
    assert layout.manage_users_link == '/UserCollection/'
    assert layout.manage_user_groups_link == '/UserGroupCollection/'
    assert layout.manage_notices_link == '/GazetteNoticeCollection/'
    assert layout.manage_statistics_link == \
        '/GazetteNoticeCollection/statistics/'
    assert layout.dashboard_link == '/dashboard/'


def test_layout_menu():
    request = DummyRequest(None)
    layout = Layout(None, request)

    assert layout.menu == []

    request._is_personal = True
    assert layout.menu == [
        ('My Drafted and Submitted Official Notices', '/dashboard/', False),
        ('My Accepted Official Notices', '/GazetteNoticeCollection/', False)
    ]

    request._is_private = True
    assert layout.menu == [
        ('Official Notices', '/GazetteNoticeCollection/', False),
        ('Statistics', '/GazetteNoticeCollection/statistics/', False)
    ]

    request._is_secret = True
    assert layout.menu == [
        ('Users', '/UserCollection/', False),
        ('Groups', '/UserGroupCollection/', False),
        ('Official Notices', '/GazetteNoticeCollection/', False),
        ('Statistics', '/GazetteNoticeCollection/statistics/', False)
    ]


def test_layout_format(session, principal):
    request = DummyRequest(session, principal)
    layout = Layout(None, request)

    # Issue
    with raises(ValueError):
        layout.format_issue(None)
    with raises(ValueError):
        layout.format_issue('')
    with raises(ValueError):
        layout.format_issue('2015/1')

    assert layout.format_issue('2015-1') == '?'
    assert layout.format_issue(Issue(2015, 1)) == '?'
    assert layout.format_issue(Issue(2017, 41)) == 'No. 41, 13.10.2017'
    assert layout.format_issue('2017-41') == 'No. 41, 13.10.2017'
    assert layout.format_issue('2017-41', date_format='date_with_weekday') == \
        'No. 41, Freitag 13.10.2017'

    # Deadline
    with raises(ValueError):
        layout.format_deadline(None)
    with raises(ValueError):
        layout.format_deadline('')
    with raises(ValueError):
        layout.format_deadline('2015/1')
    assert layout.format_deadline('2015-1') == '?'
    assert layout.format_deadline(Issue(2015, 1)) == '?'
    assert layout.format_deadline(Issue(2017, 41)) == \
        'Mittwoch 11.10.2017 12:00'
    assert layout.format_deadline('2017-41') == 'Mittwoch 11.10.2017 12:00'
    assert layout.format_deadline('2017-41', date_format='time') == '12:00'
