from datetime import datetime
from freezegun import freeze_time
from onegov.gazette.collections import UserGroupCollection
from onegov.gazette.forms import NoticeForm
from onegov.gazette.forms import UserForm
from onegov.gazette.forms import UserGroupForm
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.models import UserGroup
from onegov.user import User
from sedate import standardize_date


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

    def include(self, resource):
        pass


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_user_group_form():
    # Test apply / update
    form = UserGroupForm()
    group = UserGroup(name='Group X')

    form.apply_model(group)
    assert form.name.data == 'Group X'

    form.name.data = 'Group Y'
    form.update_model(group)
    assert group.name == 'Group Y'

    # Test validation
    form = UserGroupForm()
    assert not form.validate()

    form = UserGroupForm(DummyPostData({'name': 'Group'}))
    assert form.validate()


def test_user_form(session):
    # Test apply / update
    form = UserForm()
    user = User(username='a@a.ai', role='editor', realname='User')

    form.apply_model(user)
    assert form.email.data == 'a@a.ai'
    assert form.role.data == 'editor'
    assert form.name.data == 'User'
    assert form.group.data == ''

    user.data = {'group': 'Group'}
    form.apply_model(user)
    assert form.group.data == 'Group'

    form.email.data = 'b@b.bi'
    form.role.data = 'publisher'
    form.name.data = 'Publisher'
    form.group.data = 'Publishers'

    form.update_model(user)
    assert user.username == 'b@b.bi'
    assert user.role == 'publisher'
    assert user.realname == 'Publisher'
    assert user.data['group'] == 'Publishers'

    # Test validation
    form = UserForm()
    assert not form.validate()

    for role, result in (('admin', False), ('editor', True), ('member', True)):
        form = UserForm(
            DummyPostData({
                'role': role,
                'name': 'User',
                'email': 'x@y.za',
                'group': ''
            })
        )
        assert form.validate() == result

    # Test on request
    form = UserForm()
    form.request = DummyRequest(session)

    form.on_request()
    assert form.group.choices == [('', '')]

    groups = UserGroupCollection(session)
    groups.add(name='Group A')
    groups.add(name='Group B')
    groups.add(name='Group C')

    form.on_request()
    assert sorted([choice[1] for choice in form.group.choices]) == [
        '', 'Group A', 'Group B', 'Group C'
    ]


def test_notice_form(session, principal):
    # Test apply / update
    form = NoticeForm()
    form.request = DummyRequest(session, principal)

    notice = GazetteNotice(
        title='Title',
        text='A <b>text</b>.'
    )
    notice.organization_id = '210'
    notice.category_id = '13'
    notice.issues = [str(Issue(2017, 43))]

    form.apply_model(notice)
    assert form.title.data == 'Title'
    assert form.organization.data == '210'
    assert form.category.data == '13'
    assert form.text.data == 'A <b>text</b>.'
    assert form.issues.data == ['2017-43']

    form.title.data = 'Notice'
    form.organization.data = '310'
    form.category.data = '14'
    form.text.data = 'A <b>notice</b>.'
    form.issues.data = ['2017-44']

    form.update_model(notice)
    assert notice.title == 'Notice'
    assert notice.organization == 'Einwohnergemeinde Zug'
    assert notice.category == 'Kantonale Mitteilungen'
    assert notice.text == 'A <b>notice</b>.'
    assert notice.issues == {'2017-44': None}
    assert notice.issue_date == standardize_date(
        datetime(2017, 11, 3), 'Europe/Zurich'
    )

    # Test validation
    form = NoticeForm()
    form.request = DummyRequest(session, principal)
    assert not form.validate()

    form = NoticeForm()
    form.request = DummyRequest(session, principal)
    form.issues.choices = [('2017-5', '2017-5')]
    form.organization.choices = [('onegov', 'onegov')]
    form.category.choices = [('important', 'important')]
    form.process(
        DummyPostData({
            'title': 'Title',
            'organization': 'onegov',
            'category': 'important',
            'issues': ['2017-5'],
            'text': 'Text'
        })
    )
    assert form.validate()

    # Test on request
    form = NoticeForm()
    form.request = DummyRequest(session, principal)

    with freeze_time("2017-11-01 12:00"):
        form.on_request()
        assert form.organization.choices == [
            ('100', 'Staatskanzlei Kanton Zug'),
            ('210', 'Bürgergemeinde Zug'),
            ('310', 'Einwohnergemeinde Zug'),
            ('400', 'Evangelisch-reformierte Kirchgemeinde des Kantons Zug'),
            ('501', 'Katholische Kirchgemeinde Baar'),
            ('509', 'Katholische Kirchgemeinde Zug'),
            ('609', 'Korporation Zug')
        ]
        assert form.issues.choices == [
            ('2017-44', 'Nr. 44, Freitag 03.11.2017'),
            ('2017-45', 'Nr. 45, Freitag 10.11.2017'),
            ('2017-46', 'Nr. 46, Freitag 17.11.2017'),
            ('2017-47', 'Nr. 47, Freitag 24.11.2017'),
            ('2017-48', 'Nr. 48, Freitag 01.12.2017')
        ]
        assert form.category.choices == [
            ('12', 'Weiterbildung'),
            ('13', 'Submissionen'),
            ('14', 'Kantonale Mitteilungen'),
            ('16', 'Bürgergemeinden'),
            ('17', 'Kath. Kirchgemeinden'),
            ('18', 'Ev.-ref. Kirchgemeinde'),
            ('19', 'Korporationen'),
            ('20', 'Handelsregister'),
        ]
