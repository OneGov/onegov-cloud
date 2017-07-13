from onegov.gazette.collections import UserGroupCollection
from onegov.gazette.layout import Layout
from onegov.gazette.models import Issue
from onegov.user import User
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


def test_layout_links():
    layout = Layout(None, DummyRequest(None))
    assert layout.homepage_link == '/'
    assert layout.manage_link == '/'
    assert layout.manage_users_link == '/UserCollection/'
    assert layout.manage_user_groups_link == '/UserGroupCollection/'
    assert layout.manage_notices_link == '/GazetteNoticeCollection/'
    assert layout.manage_published_notices_link == '/GazetteNoticeCollection/'
    assert layout.dashboard_link == '/dashboard/'
    assert layout.archive_link == '/archive/'


def test_layout_menu():
    request = DummyRequest(None)
    layout = Layout(None, request)

    assert layout.menu == []

    request._is_personal = True
    assert layout.menu == [
        ('My Drafted and Submitted Official Notices', '/dashboard/', False),
        ('My Published Official Notices', '/archive/', False)
    ]

    request._is_private = True
    assert layout.menu == [
        ('Submitted Official Notices', '/GazetteNoticeCollection/', False),
        ('Published Official Notices', '/GazetteNoticeCollection/', False)
    ]

    request._is_secret = True
    assert layout.menu == [
        ('Users', '/UserCollection/', False),
        ('Groups', '/UserGroupCollection/', False)
    ]


def test_layout_format(gazette_app):
    request = DummyRequest(gazette_app.session(), gazette_app.principal)
    layout = Layout(None, request)

    # Category
    assert layout.format_category(None) == '?'
    assert layout.format_category('') == '?'
    assert layout.format_category('1') == '?'
    assert layout.format_category('14') == 'Kantonale Mitteilungen'

    # Issue
    with raises(ValueError):
        layout.format_issue(None)
    with raises(ValueError):
        layout.format_issue('')
    with raises(ValueError):
        layout.format_issue('2015/1')
    assert layout.format_issue('2015-1') == '?'
    assert layout.format_issue(Issue(2015, 1)) == '?'
    assert layout.format_issue(Issue(2017, 41)) == 'Nr. 41, 13.10.2017'
    assert layout.format_issue('2017-41') == 'Nr. 41, 13.10.2017'

    # Owner
    assert layout.format_owner(None) == ''
    assert layout.format_owner(User(realname='User')) == 'User'

    # Group
    assert layout.format_group(None) == ''
    assert layout.format_group(User()) == ''

    uid = str(UserGroupCollection(request.app.session()).add(name='Group').id)
    assert layout.format_group(User(data={'group': uid})) == 'Group'
