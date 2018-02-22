from datetime import date
from datetime import datetime
from freezegun import freeze_time
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.forms import CategoryForm
from onegov.gazette.forms import IssueForm
from onegov.gazette.forms import NoticeForm
from onegov.gazette.forms import OrganizationForm
from onegov.gazette.forms import UnrestrictedNoticeForm
from onegov.gazette.forms import UserForm
from onegov.gazette.models import GazetteNotice
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from sedate import standardize_date


class DummyPrincipal(object):
    def __init__(self, time_zone='Europe/Zurich'):
        self.time_zone = time_zone


class DummyApp(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal

    def session(self):
        return self._session


class DummyRequest(object):
    def __init__(self, session, principal=None, private=False):
        self.app = DummyApp(session, principal)
        self.session = session
        self.private = private
        self.locale = 'de_CH'
        self.time_zone = 'Europe/Zurich'

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


def test_category_form(session):
    request = DummyRequest(session)

    # Test apply / update
    # ... unused
    categories = CategoryCollection(session)
    category = categories.add_root(name='1', title='ABC', active=True)

    form = CategoryForm()
    form.request = request
    form.apply_model(category)
    assert form.title.data == 'ABC'
    assert form.active.data is True
    assert form.name.data == '1'

    form.title.data = 'DEF'
    form.active.data = False
    form.name.data = '3'
    form.update_model(category)
    assert category.title == 'DEF'
    assert category.active is False
    assert category.name == '3'

    # ... used
    category = categories.add_root(name='2', title='XYZ', active=True)
    GazetteNoticeCollection(session).add('title', 'text', '', '2', None, [])

    form.apply_model(category)
    assert form.name.render_kw == {'readonly': True}

    # Test validation
    # ... empty values
    form = CategoryForm()
    form.request = request
    assert not form.validate()

    # ... new model
    form = CategoryForm(DummyPostData({'title': 'title', 'name': '2'}))
    form.request = request
    assert not form.validate()
    assert 'This value already exists.' in form.errors['name']

    form = CategoryForm(DummyPostData({'title': 'title', 'name': '5'}))
    form.request = request
    assert form.validate()

    # ... existing model
    form = CategoryForm(DummyPostData({'title': 'title', 'name': '3'}))
    form.model = categories.query().filter_by(name='2').one()
    form.request = request
    assert not form.validate()
    assert 'This value already exists.' in form.errors['name']
    assert 'This value is in use.' in form.errors['name']

    form = CategoryForm(DummyPostData({'title': 'title', 'name': '5'}))
    form.model = categories.query().filter_by(name='3').one()
    form.request = request
    assert form.validate()


def test_organization_form(session):
    request = DummyRequest(session)

    # Test on request
    organizations = OrganizationCollection(session)
    parent = organizations.add_root(title='parent', active=True, order=1)
    child = organizations.add(parent=parent, title='child', active=True)
    other = organizations.add_root(title='other', active=True, order=2)
    other.external_name = 'xxx'

    form = OrganizationForm()
    form.request = request
    form.on_request()
    assert form.parent.choices == [
        ('', '- none -'),
        ('1', 'parent'),
        ('3', 'other')
    ]

    # Test apply / update
    # ... unused
    form.apply_model(parent)
    assert form.title.data == 'parent'
    assert form.active.data is True
    assert form.parent.data == ''
    assert form.name.data == '1'
    assert form.external_name.data is None

    form.apply_model(child)
    assert form.title.data == 'child'
    assert form.active.data is True
    assert form.parent.data == '1'
    assert form.name.data == '2'
    assert form.external_name.data is None

    form.apply_model(other)
    assert form.title.data == 'other'
    assert form.active.data is True
    assert form.parent.data == ''
    assert form.name.data == '3'
    assert form.external_name.data == 'xxx'

    form.title.data = 'DEF'
    form.active.data = False
    form.parent.data = '1'
    form.external_name.data = 'yyy'
    form.update_model(other)
    session.flush()
    session.expire(other)
    assert other.title == 'DEF'
    assert other.active is False
    assert other.parent == parent
    assert other.siblings.filter_by(id='3')
    assert other.name == '3'
    assert form.external_name.data == 'yyy'

    form.name.data = '4'
    form.update_model(other)
    assert other.name == '4'

    # ... used
    GazetteNoticeCollection(session).add('title', 'text', '4', '', None, [])

    form.apply_model(other)
    assert form.name.render_kw == {'readonly': True}

    # Test validation
    # ... empty values
    form = OrganizationForm()
    form.request = request
    assert not form.validate()

    # ... new model
    form = OrganizationForm(
        DummyPostData({'title': 'title', 'parent': '', 'name': '2'})
    )
    form.request = request
    assert not form.validate()
    assert 'This value already exists.' in form.errors['name']

    form = OrganizationForm(
        DummyPostData({'title': 'title', 'parent': '', 'name': '5'})
    )
    form.request = request
    assert form.validate()

    # ... existing model
    form = OrganizationForm(
        DummyPostData({'title': 'title', 'parent': '', 'name': '2'})
    )
    form.model = organizations.query().filter_by(name='4').one()
    form.request = request
    assert not form.validate()
    assert 'This value already exists.' in form.errors['name']
    assert 'This value is in use.' in form.errors['name']

    form = OrganizationForm(
        DummyPostData({'title': 'title', 'parent': '', 'name': '5'})
    )
    form.model = organizations.query().filter_by(name='1').one()
    form.request = request
    assert form.validate()


def test_issue_form(session):
    request = DummyRequest(session, DummyPrincipal())

    # Test apply / update
    # ... unused
    issues = IssueCollection(session)
    issue = issues.add(
        name='2018-1', number=1, date=date(2018, 1, 5),
        deadline=standardize_date(datetime(2018, 1, 4, 12, 0), 'UTC')
    )

    form = IssueForm()
    form.request = request
    form.on_request()

    form.apply_model(issue)
    assert form.number.data == 1
    assert form.name.data == '2018-1'
    assert form.date_.data == date(2018, 1, 5)
    assert form.deadline.data == datetime(2018, 1, 4, 13, 0)

    form.number.data = 2
    form.date_.data = date(2019, 1, 5)
    form.deadline.data = datetime(2019, 1, 4, 13, 0)
    form.update_model(issue)
    assert issue.number == 2
    assert issue.name == '2019-2'
    assert issue.date == date(2019, 1, 5)
    assert issue.deadline == standardize_date(
        datetime(2019, 1, 4, 12, 0), 'UTC'
    )

    # used
    issue = issues.add(
        name='2019-3', number=3, date=date(2019, 2, 5),
        deadline=standardize_date(datetime(2019, 2, 4, 12, 0), 'UTC')
    )
    notices = GazetteNoticeCollection(session)
    notices.add('title', 'text', '', '', None, ['2019-3'])

    form.apply_model(issue)
    assert form.number.render_kw == {'readonly': True}

    # Test validation
    # ... empty values
    form = IssueForm()
    form.request = request
    assert not form.validate()

    # ... new model
    form = IssueForm(
        DummyPostData({
            'number': '3', 'date_': '2019-03-05',
            'deadline': '2019-03-04T12:00'
        })
    )
    form.request = request
    assert not form.validate()
    assert 'This value already exists.' in form.errors['name']

    form = IssueForm(
        DummyPostData({
            'number': '5', 'date_': '2019-03-05',
            'deadline': '2019-03-04T12:00'
        })
    )
    form.request = request
    assert form.validate()

    form = IssueForm(
        DummyPostData({
            'number': '3', 'date_': '2018-03-05',
            'deadline': '2019-03-04T12:00'
        })
    )
    form.request = request
    assert form.validate()

    # ... existing model
    form = IssueForm(
        DummyPostData({
            'number': '2', 'date_': '2019-03-05',
            'deadline': '2019-03-04T12:00'
        })
    )
    form.model = issues.query().filter_by(number='3').one()
    form.request = request
    assert not form.validate()
    assert 'This value already exists.' in form.errors['name']
    assert 'This value is in use.' in form.errors['name']

    form = IssueForm(
        DummyPostData({
            'number': '5', 'date_': '2019-03-05',
            'deadline': '2019-03-04T12:00'
        })
    )
    form.model = issues.query().filter_by(number='2').one()
    form.request = request
    assert form.validate()

    # Datetimepicker forma
    form = IssueForm(
        DummyPostData({
            'number': '1', 'date_': '2020-01-01',
            'deadline': '2011-01-01 12:00'
        })
    )
    form.request = request
    assert form.validate()


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
    assert form.username.data == 'a@a.ai'
    assert form.role.data == 'editor'
    assert form.name.data == 'User'
    assert form.group.data == ''

    user.group = group
    session.flush()

    form.apply_model(user)
    assert form.group.data == str(group.id)

    form.username.data = 'b@b.bi'
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

    # ... admins can not be created
    for role, result in (('admin', False), ('editor', True), ('member', True)):
        form = UserForm(
            DummyPostData({
                'role': role,
                'name': 'User',
                'username': 'x@y.za',
                'group': ''
            })
        )
        form.request = DummyRequest(session)
        assert form.validate() == result

    # ... existing email
    form = UserForm(
        DummyPostData({
            'role': 'editor',
            'name': 'User',
            'username': 'b@b.bi',
            'group': ''
        })
    )
    form.request = DummyRequest(session)
    assert not form.validate()
    assert 'This value already exists.' in form.errors['username']

    form.model = user
    form.validate()


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


def test_notice_form(session, categories, organizations, issues):
    # Test apply / update
    form = NoticeForm()
    form.request = DummyRequest(session)

    notice = GazetteNotice(
        title='Title',
        text='A <b>text</b>.',
        author_place='Govikon',
        author_name='State Chancellerist',
        author_date=standardize_date(datetime(2018, 1, 1), 'UTC'),
    )
    notice.organization_id = '200'
    notice.category_id = '13'
    notice.issues = ['2017-43']

    notice.author_date is None
    notice.author_name is None

    form.apply_model(notice)
    assert form.title.data == 'Title'
    assert form.organization.data == '200'
    assert form.category.data == '13'
    assert form.print_only.data is False
    assert form.at_cost.data == 'no'
    assert form.billing_address.data == ''
    assert form.text.data == 'A <b>text</b>.'
    assert form.author_place.data == 'Govikon'
    assert form.author_name.data == 'State Chancellerist'
    assert form.author_date.data == standardize_date(
        datetime(2018, 1, 1), 'UTC'
    )
    assert form.issues.data == ['2017-43']

    form.title.data = 'Notice'
    form.organization.data = '300'
    form.category.data = '11'
    form.print_only.data = True
    form.at_cost.data = 'yes'
    form.billing_address.data = 'someone\nsomewhere'
    form.text.data = 'A <b>notice</b>.'
    form.author_place.data = 'Govtown'
    form.author_name.data = 'Bureau of Public Affairs'
    form.author_date.data = standardize_date(datetime(2019, 1, 1), 'UTC')
    form.issues.data = ['2017-44']

    form.update_model(notice)
    assert notice.title == 'Notice'
    assert notice.organization == 'Municipality'
    assert notice.category == 'Education'
    assert notice.print_only is True
    assert notice.at_cost is True
    assert notice.billing_address == 'someone\nsomewhere'
    assert notice.text == 'A <b>notice</b>.'
    assert notice.author_place == 'Govtown'
    assert notice.author_name == 'Bureau of Public Affairs'
    assert notice.author_date == standardize_date(datetime(2019, 1, 1), 'UTC')
    assert notice.issues == {'2017-44': None}
    assert notice.first_issue == standardize_date(datetime(2017, 11, 3), 'UTC')

    # Test validation
    form = NoticeForm()
    form.request = DummyRequest(session)
    assert not form.validate()

    form = NoticeForm()
    form.request = DummyRequest(session)
    form.issues.choices = [('2017-5', '2017-5')]
    form.organization.choices = [('onegov', 'onegov')]
    form.category.choices = [('important', 'important')]
    form.process(
        DummyPostData({
            'title': 'Title',
            'organization': 'onegov',
            'category': 'important',
            'issues': ['2017-5'],
            'text': 'Text',
            'author_place': 'Govtown',
            'author_name': 'Bureau of Public Affairs',
            'author_date': '2019-01-01'
        })
    )
    assert form.validate()

    # Test UTC conversion
    assert form.author_date.data == date(2019, 1, 1)
    assert form.author_date_utc == standardize_date(
        datetime(2019, 1, 1), 'UTC'
    )
    assert NoticeForm().author_date_utc is None

    # Test on request
    with freeze_time("2017-11-01 14:00"):
        form = NoticeForm()
        form.model = None
        form.request = DummyRequest(session)
        form.on_request()
        assert form.organization.choices == [
            ('', 'Select one'),
            ('100', 'State Chancellery'),
            ('200', 'Civic Community'),
            ('300', 'Municipality'),
            ('410', 'Evangelical Reformed Parish'),
            ('430', 'Catholic Parish'),
            ('500', 'Corporation')
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
            ('13', 'Commercial Register'),
            ('11', 'Education'),
            ('14', 'Elections'),
            ('12', 'Submissions'),
        ]
        assert form.print_only is None

        form = NoticeForm()
        form.model = None
        form.request = DummyRequest(session, private=True)
        form.on_request()
        assert form.organization.choices == [
            ('', 'Select one'),
            ('100', 'State Chancellery'),
            ('200', 'Civic Community'),
            ('300', 'Municipality'),
            ('410', 'Evangelical Reformed Parish'),
            ('430', 'Catholic Parish'),
            ('500', 'Corporation')
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
            ('13', 'Commercial Register'),
            ('11', 'Education'),
            ('14', 'Elections'),
            ('12', 'Submissions'),
        ]
        assert form.issues.render_kw['data-hot-issue'] == '2017-44'
        assert form.print_only is not None


def test_unrestricted_notice_form(session, categories, organizations, issues):
    # Test apply / update
    form = UnrestrictedNoticeForm()
    form.request = DummyRequest(session)

    notice = GazetteNotice(title='Title', text='A <b>text</b>.')
    notice.organization_id = '200'
    notice.category_id = '13'
    notice.issues = ['2017-43']

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

    notice.state = 'published'
    form.issues.data = ['2017-45']
    form.update_model(notice)
    assert notice.issues == {'2017-44': None}

    # Test on request
    with freeze_time("2019-11-01 14:00"):
        form = UnrestrictedNoticeForm()
        form.model = None
        form.request = DummyRequest(session)
        form.on_request()
        assert form.organization.choices == [
            ('', 'Select one'),
            ('100', 'State Chancellery'),
            ('200', 'Civic Community'),
            ('300', 'Municipality'),
            ('410', 'Evangelical Reformed Parish'),
            ('420', '(Sikh Community)'),
            ('430', 'Catholic Parish'),
            ('500', 'Corporation')
        ]
        assert form.issues.choices == [
            ('2017-40', 'No. 40, Freitag 06.10.2017'),
            ('2017-41', 'No. 41, Freitag 13.10.2017'),
            ('2017-42', 'No. 42, Freitag 20.10.2017'),
            ('2017-43', 'No. 43, Freitag 27.10.2017'),
            ('2017-44', 'No. 44, Freitag 03.11.2017'),
            ('2017-45', 'No. 45, Freitag 10.11.2017'),
            ('2017-46', 'No. 46, Freitag 17.11.2017'),
            ('2017-47', 'No. 47, Freitag 24.11.2017'),
            ('2017-48', 'No. 48, Freitag 01.12.2017'),
            ('2017-49', 'No. 49, Freitag 08.12.2017'),
            ('2017-50', 'No. 50, Freitag 15.12.2017'),
            ('2017-51', 'No. 51, Freitag 22.12.2017'),
            ('2017-52', 'No. 52, Freitag 29.12.2017'),
            ('2018-1', 'No. 1, Freitag 05.01.2018')
        ]
        assert form.category.choices == [
            ('13', 'Commercial Register'),
            ('10', '(Complaints)'),
            ('11', 'Education'),
            ('14', 'Elections'),
            ('12', 'Submissions'),
        ]

    # Test disable issues
    form = UnrestrictedNoticeForm()
    form.model = None
    form.request = DummyRequest(session)
    form.on_request()
    form.disable_issues()
    assert form.issues.validators == []
    assert all([field.render_kw['disabled'] for field in form.issues])
