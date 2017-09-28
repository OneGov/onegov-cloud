from datetime import datetime
from freezegun import freeze_time
from onegov.gazette.forms import NoticeForm
from onegov.gazette.forms import UserForm
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from sedate import standardize_date


class DummyApp(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal

    def session(self):
        return self._session


class DummyRequest(object):
    def __init__(self, session, principal=None, private=False):
        self.app = DummyApp(session, principal)
        self.private = private
        self.locale = 'de_CH'

    def is_private(self, model):
        return self.private

    def include(self, resource):
        pass

    def translate(self, text):
        return text.interpolate()


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_user_form(session):
    # Test apply / update
    users = UserCollection(session)
    user = users.add(
        username='a@a.ai', realname='User', role='editor', password='pwd'
    )

    groups = UserGroupCollection(session)
    group = groups.add(name='Group A')

    form = UserForm()

    form.apply_model(user)
    assert form.email.data == 'a@a.ai'
    assert form.email_old.data == 'a@a.ai'
    assert form.role.data == 'editor'
    assert form.name.data == 'User'
    assert form.group.data == ''

    user.group = group
    session.flush()

    form.apply_model(user)
    assert form.group.data == str(group.id)

    form.email.data = 'b@b.bi'
    form.role.data = 'publisher'
    form.name.data = 'Publisher'
    form.group.data = ''

    form.update_model(user)
    assert user.username == 'b@b.bi'
    assert user.role == 'publisher'
    assert user.realname == 'Publisher'
    assert user.group_id is None

    session.flush()
    session.refresh(user)
    assert user.group is None

    # Test validation
    form = UserForm()
    form.request = DummyRequest(session)
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
        form.request = DummyRequest(session)
        assert form.validate() == result

    form = UserForm(
        DummyPostData({
            'role': 'editor',
            'name': 'User',
            'email': 'b@b.bi',
            'group': ''
        })
    )
    form.request = DummyRequest(session)
    assert not form.validate()

    form = UserForm(
        DummyPostData({
            'role': 'editor',
            'name': 'User',
            'email': 'b@b.bi',
            'email_old': 'b@b.bi',
            'group': ''
        })
    )
    form.request = DummyRequest(session)
    assert form.validate()


def test_user_form_on_request(session):
    form = UserForm()
    form.request = DummyRequest(session)

    form.on_request()
    assert form.group.choices == [('', '- none -')]

    groups = UserGroupCollection(session)
    groups.add(name='Group A')
    groups.add(name='Group B')
    groups.add(name='Group C')

    form.on_request()
    assert sorted([choice[1] for choice in form.group.choices]) == [
        '- none -', 'Group A', 'Group B', 'Group C'
    ]


def test_notice_form(session, principal):
    # Test apply / update
    form = NoticeForm()
    form.request = DummyRequest(session, principal)

    notice = GazetteNotice(
        title='Title',
        text='A <b>text</b>.'
    )
    notice.organization_id = '200'
    notice.category_id = '13'
    notice.issues = [str(Issue(2017, 43))]

    form.apply_model(notice)
    assert form.title.data == 'Title'
    assert form.organization.data == '200'
    assert form.category.data == '13'
    assert form.text.data == 'A <b>text</b>.'
    assert form.issues.data == ['2017-43']

    form.title.data = 'Notice'
    form.organization.data = '300'
    form.category.data = '11'
    form.text.data = 'A <b>notice</b>.'
    form.issues.data = ['2017-44']

    form.update_model(notice)
    assert notice.title == 'Notice'
    assert notice.organization == 'Municipality'
    assert notice.category == 'Education'
    assert notice.text == 'A <b>notice</b>.'
    assert notice.issues == {'2017-44': None}
    assert notice.first_issue == standardize_date(datetime(2017, 11, 3), 'UTC')

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
    with freeze_time("2017-11-01 14:00"):
        form = NoticeForm()
        form.model = None
        form.request = DummyRequest(session, principal)
        form.on_request()
        assert form.organization.choices == [
            ('', 'Select one'),
            ('100', 'State Chancellery'),
            ('200', 'Civic Community'),
            ('300', 'Municipality'),
            ('400', 'Evangelical Reformed Parish'),
            ('500', 'Catholic Parish'),
            ('600', 'Corporation')
        ]
        assert form.issues.choices == [
            ('2017-45', 'No. 45, Freitag 10.11.2017'),
            ('2017-46', 'No. 46, Freitag 17.11.2017'),
            ('2017-47', 'No. 47, Freitag 24.11.2017'),
            ('2017-48', 'No. 48, Freitag 01.12.2017'),
            ('2017-49', 'No. 49, Freitag 08.12.2017'),
            ('2017-50', 'No. 50, Freitag 15.12.2017'),
            ('2017-51', 'No. 51, Freitag 22.12.2017'),
            ('2017-52', 'No. 52, Freitag 29.12.2017'),
            ('2018-1', 'No. 1, Freitag 05.01.2018'),
        ]
        assert form.category.choices == [
            ('11', 'Education'),
            ('12', 'Submissions'),
            ('13', 'Commercial Register'),
            ('14', 'Elections'),
        ]

        form = NoticeForm()
        form.model = None
        form.request = DummyRequest(session, principal, private=True)
        form.on_request()
        assert form.organization.choices == [
            ('', 'Select one'),
            ('100', 'State Chancellery'),
            ('200', 'Civic Community'),
            ('300', 'Municipality'),
            ('400', 'Evangelical Reformed Parish'),
            ('500', 'Catholic Parish'),
            ('600', 'Corporation')
        ]
        assert form.issues.choices == [
            ('2017-44', 'No. 44, Freitag 03.11.2017'),
            ('2017-45', 'No. 45, Freitag 10.11.2017'),
            ('2017-46', 'No. 46, Freitag 17.11.2017'),
            ('2017-47', 'No. 47, Freitag 24.11.2017'),
            ('2017-48', 'No. 48, Freitag 01.12.2017'),
            ('2017-49', 'No. 49, Freitag 08.12.2017'),
            ('2017-50', 'No. 50, Freitag 15.12.2017'),
            ('2017-51', 'No. 51, Freitag 22.12.2017'),
            ('2017-52', 'No. 52, Freitag 29.12.2017'),
            ('2018-1', 'No. 1, Freitag 05.01.2018'),
        ]
        assert form.category.choices == [
            ('11', 'Education'),
            ('12', 'Submissions'),
            ('13', 'Commercial Register'),
            ('14', 'Elections'),
        ]
        assert form.issues.render_kw['data-hot-issue'] == '2017-44'
