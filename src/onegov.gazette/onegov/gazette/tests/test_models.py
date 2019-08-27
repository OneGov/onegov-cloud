from datetime import date
from datetime import datetime
from freezegun import freeze_time
from onegov.file.utils import as_fileintent
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.models import Category
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import GazetteNoticeFile
from onegov.gazette.models import Issue
from onegov.gazette.models import IssueName
from onegov.gazette.models import Organization
from onegov.gazette.models import OrganizationMove
from onegov.gazette.models import Principal
from onegov.gazette.models.issue import IssuePdfFile
from onegov.gazette.models.notice import GazetteNoticeChange
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from pytest import raises
from sedate import standardize_date
from textwrap import dedent


class DummyPrincipal(object):
    name = 'Govikon'
    links = None


class DummyApp(object):
    def __init__(self, session):
        self._session = session
        self.principal = DummyPrincipal()
        self.logo_for_pdf = None

    def session(self):
        return self._session


class DummyRequest(object):
    def __init__(self, session):
        self.app = DummyApp(session)
        self.identity = None
        self.locale = 'de_CH'
        self.session = session

    def include(self, resource):
        pass

    def translate(self, text):
        return text.interpolate()


def test_category(session):
    session.add(
        Category(
            name='100',
            title='Election',
            active=True
        )
    )
    session.flush()
    category = session.query(Category).one()

    assert category.name == '100'
    assert category.title == 'Election'
    assert category.active is True

    # Test helpers
    assert len(category.notices().all()) == 0
    assert category.in_use is False

    session.add(GazetteNotice(title='notice', category_id=category.name))
    session.flush()

    assert len(category.notices().all()) == 1
    assert category.in_use is True

    # Test title observer
    category.title = 'Vote'
    session.flush()
    assert session.query(GazetteNotice).one().category == 'Vote'


def test_organization(session):
    session.add(
        Organization(
            name='100',
            title='State Chancellery',
            active=True
        )
    )
    session.flush()
    parent = session.query(Organization).one()

    assert parent.name == '100'
    assert parent.title == 'State Chancellery'
    assert parent.active is True
    assert parent.external_name is None

    # Test in use
    session.add(
        Organization(
            parent=parent,
            name='101',
            title='Administration',
            active=True
        )
    )
    session.flush()
    child = session.query(Organization).filter_by(name='101').one()

    assert len(parent.notices().all()) == 0
    assert len(child.notices().all()) == 0
    assert parent.in_use is False
    assert child.in_use is False

    session.add(
        GazetteNotice(title='notice', organization_id='101')
    )
    session.flush()

    assert len(parent.notices().all()) == 0
    assert len(child.notices().all()) == 1
    assert parent.in_use is False
    assert child.in_use is True

    # Test title observer
    child.title = 'Administrations'
    session.flush()
    assert session.query(GazetteNotice).one().organization == 'Administrations'


def test_organization_move(session):
    # test URL template
    move = OrganizationMove(None, None, None, None).for_url_template()
    assert move.direction == '{direction}'
    assert move.subject_id == '{subject_id}'
    assert move.target_id == '{target_id}'

    # test execute
    collection = OrganizationCollection(session)
    collection.add_root(title='2', id=2, order=2)
    collection.add_root(title='1', id=1, oder=1)
    parent = collection.add_root(title='3', id=3, order=3)
    collection.add(parent=parent, title='5', id=5, order=2)
    collection.add(parent=parent, title='4', id=4, order=1)

    def tree():
        return [
            [o.title, [c.title for c in o.children]]
            for o in collection.query().filter_by(parent_id=None)
        ]

    assert tree() == [['1', []], ['2', []], ['3', ['4', '5']]]

    OrganizationMove(session, 1, 2, 'below').execute()
    assert tree() == [['2', []], ['1', []], ['3', ['4', '5']]]

    OrganizationMove(session, 3, 1, 'above').execute()
    assert tree() == [['2', []], ['3', ['4', '5']], ['1', []]]

    OrganizationMove(session, 5, 4, 'above').execute()
    session.flush()
    session.expire_all()
    assert tree() == [['2', []], ['3', ['5', '4']], ['1', []]]

    # invalid
    OrganizationMove(session, 8, 9, 'above').execute()
    assert tree() == [['2', []], ['3', ['5', '4']], ['1', []]]

    OrganizationMove(session, 5, 2, 'above').execute()
    session.expire_all()
    assert tree() == [['2', []], ['3', ['5', '4']], ['1', []]]


def test_issue_name():
    issue_name = IssueName(2017, 1)
    assert issue_name.year == 2017
    assert issue_name.number == 1
    assert IssueName.from_string(str(issue_name)) == issue_name


def test_issue_file(gazette_app, session):
    session.add(
        IssuePdfFile(
            id='abcd',
            name='test.txt',
            reference=as_fileintent('Test text.'.encode('utf-8'), 'test.txt')
        )
    )
    session.flush()

    file = session.query(IssuePdfFile).one()

    assert file.id == 'abcd'
    assert file.name == 'test.txt'
    assert file.type == 'gazette_issue'
    assert file.reference.file.read().decode('utf-8') == 'Test text.'


def test_issue(gazette_app, session):
    issue = Issue(
        id=0,
        name='2018-7',
        number=7,
        date=date(2017, 7, 1),
        deadline=standardize_date(datetime(2017, 6, 25, 12, 0), 'UTC'),
    )
    issue.pdf = 'PDF'.encode('utf-8')
    session.add(issue)
    session.flush()
    issue = session.query(Issue).one()

    assert issue.id == 0
    assert issue.name == '2018-7'
    assert issue.number == 7
    assert issue.date == date(2017, 7, 1)
    assert issue.deadline == standardize_date(
        datetime(2017, 6, 25, 12, 0), 'UTC'
    )
    assert issue.pdf.id
    assert issue.pdf.name == '2018-7.pdf'
    assert issue.pdf.type == 'gazette_issue'
    assert issue.pdf.reference.file.read().decode('utf-8') == 'PDF'

    # Test query etc
    assert len(issue.notices().all()) == 0
    assert issue.notices('accepted').all() == []
    assert issue.notices('submitted').all() == []
    assert issue.in_use is False

    issues = [issue.name]
    session.add(GazetteNotice(title='d', issues=issues))
    session.add(GazetteNotice(title='a', state='accepted', issues=issues))
    session.add(GazetteNotice(title='s', state='submitted', issues=issues))
    session.add(GazetteNotice(title='s', issues=['2018-1']))
    session.add(GazetteNotice(title='s', issues=['2018-1', issue.name]))
    session.flush()

    assert len(issue.notices().all()) == 4
    assert issue.notices('accepted').all()[0].title == 'a'
    assert issue.notices('submitted').one().title == 's'
    assert issue.in_use is True

    # Test date observer
    issue.date = date(2018, 7, 2)
    session.flush()
    dates = [i.first_issue for i in session.query(GazetteNotice)]
    dates = [d.date() for d in dates if d]
    assert set(dates) == set([issue.date])

    # Test publish
    issue.publish(DummyRequest(session))
    assert len(issue.notices().all()) == 4
    assert issue.notices('accepted').all() == []
    assert issue.notices('published').count() == 1


def test_issue_publication_numbers(session):
    session.add(Issue(name='2016-1', number=1, date=date(2016, 1, 1)))
    session.add(Issue(name='2017-1', number=1, date=date(2017, 1, 1)))
    session.add(Issue(name='2017-2', number=2, date=date(2017, 2, 2)))
    session.add(Issue(name='2018-1', number=1, date=date(2018, 1, 1)))
    session.add(Issue(name='2018-2', number=2, date=date(2018, 2, 2)))
    session.add(Issue(name='2018-3', number=2, date=date(2018, 3, 3)))
    session.flush()

    def issue(name):
        return session.query(Issue).filter_by(name=name).one()

    assert issue('2016-1').first_publication_number == 1
    assert issue('2017-1').first_publication_number == 1
    assert issue('2017-2').first_publication_number == 1
    assert issue('2018-1').first_publication_number == 1
    assert issue('2018-2').first_publication_number == 1
    assert issue('2018-3').first_publication_number == 1

    assert issue('2016-1').publication_numbers() == {}
    assert issue('2017-1').publication_numbers() == {}
    assert issue('2017-2').publication_numbers() == {}
    assert issue('2018-1').publication_numbers() == {}
    assert issue('2018-2').publication_numbers() == {}
    assert issue('2018-3').publication_numbers() == {}

    assert {1} == set([
        issue.first_publication_number for issue in session.query(Issue)
    ])

    session.add(GazetteNotice(title='1', _issues={'2016-1': '5'}))
    session.add(GazetteNotice(title='2', _issues={'2017-1': None}))
    session.add(GazetteNotice(title='3', _issues={'2017-1': '5',
                                                  '2017-2': '6'}))
    session.add(GazetteNotice(title='4', _issues={'2017-1': None,
                                                  '2018-3': '4'}))
    session.add(GazetteNotice(title='4', _issues={'2017-2': '9',
                                                  '2018-1': '1',
                                                  '2018-2': '2'}))
    session.flush()

    assert issue('2016-1').first_publication_number == 1
    assert issue('2017-1').first_publication_number == 1
    assert issue('2017-2').first_publication_number == 6
    assert issue('2018-1').first_publication_number == 1
    assert issue('2018-2').first_publication_number == 2
    assert issue('2018-3').first_publication_number == 3

    assert set(issue('2016-1').publication_numbers().values()) == {'5'}
    assert set(issue('2017-1').publication_numbers().values()) == {'5', None}
    assert set(issue('2017-2').publication_numbers().values()) == {'6', '9'}
    assert set(issue('2018-1').publication_numbers().values()) == {'1'}
    assert set(issue('2018-2').publication_numbers().values()) == {'2'}
    assert set(issue('2018-3').publication_numbers().values()) == {'4'}

    session.add(Issue(name='2016-2', number=2, date=date(2016, 2, 1)))
    session.add(Issue(name='2017-3', number=3, date=date(2017, 3, 1)))
    session.add(Issue(name='2018-4', number=4, date=date(2018, 4, 1)))
    session.flush()

    assert issue('2016-2').first_publication_number == 6
    assert issue('2017-3').first_publication_number == 10
    assert issue('2018-4').first_publication_number == 5

    session.add(Issue(name='2016-12', number=12, date=date(2016, 12, 1)))
    session.add(Issue(name='2017-12', number=12, date=date(2017, 12, 1)))
    session.add(Issue(name='2018-12', number=12, date=date(2018, 12, 1)))
    session.flush()

    assert issue(name='2016-12').first_publication_number == 6
    assert issue(name='2017-12').first_publication_number == 10
    assert issue(name='2018-12').first_publication_number == 5


def test_issue_publish(gazette_app, session):
    session.add(Category(name='a', title='a', active=True))
    session.add(Category(name='b', title='b', active=True))

    session.add(Organization(name='1', title='1', active=True))
    session.add(Organization(name='2', title='2', active=True))

    session.add(Issue(name='2016-1', number=1, date=date(2016, 1, 1)))
    session.add(Issue(name='2016-2', number=1, date=date(2016, 2, 1)))
    session.add(Issue(name='2016-4', number=1, date=date(2016, 4, 1)))
    session.add(Issue(name='2017-1', number=1, date=date(2017, 1, 1)))
    session.flush()

    session.add(
        GazetteNotice(
            title='x',
            organization_id='1',
            category_id='b',
            _issues={'2016-1': None, '2016-4': None, '2017-1': None},
            state='accepted',
            text='XXX'
        )
    )
    session.add(
        GazetteNotice(
            title='y',
            organization_id='1',
            category_id='a',
            _issues={'2016-1': None, '2016-2': None},
            state='accepted',
            text='YYY'
        )
    )
    session.add(
        GazetteNotice(
            title='z',
            organization_id='2',
            category_id='b',
            _issues={'2016-4': None, '2017-1': None},
            state='accepted',
            text='ZZZ'
        )
    )
    session.flush()

    request = DummyRequest(session)
    session.query(Issue).filter_by(name='2016-2').one().publish(request)

    def notice(title):
        return session.query(GazetteNotice).filter_by(title=title).one()

    assert notice('x').issues == {'2016-1': None, '2016-4': None,
                                  '2017-1': None}
    assert notice('y').issues == {'2016-1': None, '2016-2': '1'}
    assert notice('z').issues == {'2016-4': None, '2017-1': None}
    assert notice('x').state == 'accepted'
    assert notice('y').state == 'published'
    assert notice('z').state == 'accepted'

    session.query(Issue).filter_by(name='2016-4').one().publish(request)
    assert notice('x').issues == {'2016-1': None, '2016-4': '2',
                                  '2017-1': None}
    assert notice('y').issues == {'2016-1': None, '2016-2': '1'}
    assert notice('z').issues == {'2016-4': '3', '2017-1': None}
    assert notice('x').state == 'published'
    assert notice('y').state == 'published'
    assert notice('z').state == 'published'

    session.query(Issue).filter_by(name='2016-1').one().publish(request)
    assert notice('x').issues == {'2016-1': '2', '2016-4': '2', '2017-1': None}
    assert notice('y').issues == {'2016-1': '1', '2016-2': '1'}
    assert notice('z').issues == {'2016-4': '3', '2017-1': None}

    session.query(Issue).filter_by(name='2016-2').one().publish(request)
    assert notice('x').issues == {'2016-1': '2', '2016-4': '2', '2017-1': None}
    assert notice('y').issues == {'2016-1': '1', '2016-2': '3'}
    assert notice('z').issues == {'2016-4': '3', '2017-1': None}

    session.query(Issue).filter_by(name='2016-4').one().publish(request)
    assert notice('x').issues == {'2016-1': '2', '2016-4': '4', '2017-1': None}
    assert notice('y').issues == {'2016-1': '1', '2016-2': '3'}
    assert notice('z').issues == {'2016-4': '5', '2017-1': None}

    session.query(Issue).filter_by(name='2017-1').one().publish(request)
    assert notice('x').issues == {'2016-1': '2', '2016-4': '4', '2017-1': '1'}
    assert notice('y').issues == {'2016-1': '1', '2016-2': '3'}
    assert notice('z').issues == {'2016-4': '5', '2017-1': '2'}


def test_principal():
    principal = Principal.from_yaml(dedent("""
        name: Govikon
        color: '#aabbcc'
        logo: 'logo.svg'
    """))
    assert principal.name == 'Govikon'
    assert principal.color == '#aabbcc'
    assert principal.logo == 'logo.svg'
    assert principal.logo_for_pdf == ''
    assert principal.canton is None
    assert principal.on_accept == {}
    assert principal.publishing is False
    assert principal.frontend is False
    assert principal.sogc_import == {}

    principal = Principal.from_yaml(dedent("""
        name: Govikon
        canton: 'tg'
        color: '#aabbcc'
        logo: 'logo.svg'
        logo_for_pdf: 'logo-bw.svg'
        on_accept:
            mail_to: 'printer@govikon.org'
            mail_from: 'publisher@govikon.org'
        help_link: 'https://help.me'
        publishing: True
        frontend: True
        sogc_import:
            endpoint: 'https://localhost'
            username: 'user'
            password: 'pass'
            category: 190
            organization: 200
    """))
    assert principal.name == 'Govikon'
    assert principal.color == '#aabbcc'
    assert principal.logo == 'logo.svg'
    assert principal.logo_for_pdf == 'logo-bw.svg'
    assert principal.canton == 'tg'
    assert principal.on_accept == {
        'mail_to': 'printer@govikon.org',
        'mail_from': 'publisher@govikon.org'
    }
    assert principal.help_link == 'https://help.me'
    assert principal.publishing is True
    assert principal.frontend is True
    assert principal.sogc_import == {
        'endpoint': 'https://localhost',
        'username': 'user',
        'password': 'pass',
        'canton': 'TG',
        'category': 190,
        'organization': 200,
    }


def test_notice_organization(session):
    session.add(GazetteNotice(title='notice', organization_id='xxx'))
    session.flush()

    notice = session.query(GazetteNotice).one()
    assert notice.organization_id == 'xxx'
    assert notice.organization_object is None
    assert notice.organization is None

    session.add(Organization(name='xxx', title='Organization', active=True))
    organization = session.query(Organization).one()
    session.flush()
    assert notice.organization_id == 'xxx'
    assert notice.organization_object == organization
    assert notice.organization == 'Organization'  # through title observer


def test_notice_category(session):
    session.add(GazetteNotice(title='notice', category_id='xxx'))
    session.flush()

    notice = session.query(GazetteNotice).one()
    assert notice.category_id == 'xxx'
    assert notice.category_object is None
    assert notice.category is None

    session.add(Category(name='xxx', title='Category', active=True))
    category = session.query(Category).one()
    session.flush()
    assert notice.category_id == 'xxx'
    assert notice.category_object == category
    assert notice.category == 'Category'  # through title observer


def test_notice_issues(session):
    # Test connection to model
    session.add(GazetteNotice(title='notice', issues=['2017-1']))
    session.flush()

    notice = session.query(GazetteNotice).one()
    assert list(notice.issues.keys()) == ['2017-1']
    assert notice.issue_objects == []
    assert notice.first_issue is None

    session.add(Issue(name='2017-1', number=1, date=date(2017, 7, 1)))
    issue = session.query(Issue).one()
    session.flush()
    assert list(notice.issues.keys()) == ['2017-1']
    assert notice.issue_objects == [issue]
    assert notice.first_issue.date() == date(2017, 7, 1)  # through observer

    # Test HSTORE
    notice = GazetteNotice()
    assert notice.issues == {}

    notice.issues = ['2010-1', '2011-4', '2008-7']
    assert list(notice.issues.keys()) == ['2008-7', '2010-1', '2011-4']
    assert notice.issues == {'2008-7': None, '2010-1': None, '2011-4': None}

    notice.issues = {'2010-1', '2010-2', '2010-11'}
    assert list(notice.issues.keys()) == ['2010-1', '2010-2', '2010-11']
    assert notice.issues == {'2010-1': None, '2010-2': None, '2010-11': None}

    notice.issues = {'2010-1': 'a', '2009-2': 'b', '2010-11': 'c'}
    assert list(notice.issues.keys()) == ['2009-2', '2010-1', '2010-11']
    assert notice.issues == {'2009-2': 'b', '2010-1': 'a', '2010-11': 'c'}

    notice.issues = {
        str(IssueName(2017, 10)): 1004,
        str(IssueName(2017, 11)): 1022
    }
    assert notice.issues == {'2017-10': 1004, '2017-11': 1022}

    # Test settting the publication number
    notice = GazetteNotice()

    with raises(AssertionError):
        notice.set_publication_number('2017-10', 1)

    notice.issues = ['2010-1', '2010-2', '2010-3']
    notice.set_publication_number('2010-1', 1)
    notice.set_publication_number('2010-2', '2')
    notice.set_publication_number('2010-3', 3)
    assert notice.issues == {'2010-1': '1', '2010-2': '2', '2010-3': '3'}


def test_notice_user_and_group(session):
    users = UserCollection(session)
    groups = UserGroupCollection(session)

    session.add(GazetteNotice(title='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()

    assert notice.user is None
    assert notice.user_id is None
    assert notice.user_name is None
    assert notice._user_name is None
    assert notice.group is None
    assert notice.group_id is None
    assert notice.group_name is None
    assert notice._group_name is None

    # add user and group
    user = users.add('1@2.3', 'p', 'editor', realname='user')
    group = groups.add(name='group')
    notice.user = user
    notice.group = group
    session.flush()
    session.refresh(notice)

    assert notice.user == user
    assert notice.user_id == user.id
    assert notice.user_name == 'user'
    assert notice._user_name == 'user'
    assert notice.group == group
    assert notice.group_id == group.id
    assert notice.group_name == 'group'
    assert notice._group_name == 'group'

    # rename user and group
    user.realname = 'xxx'
    group.name = 'yyy'
    session.flush()
    session.refresh(notice)

    assert notice.user == user
    assert notice.user_id == user.id
    assert notice.user_name == 'xxx'
    assert notice._user_name == 'xxx'
    assert notice.group == group
    assert notice.group_id == group.id
    assert notice.group_name == 'yyy'
    assert notice._group_name == 'yyy'

    # delete user and group
    users.delete(user.username)
    groups.delete(group)
    session.flush()
    session.refresh(notice)

    assert notice.user is None
    assert notice.user_id is None
    assert notice.user_name == '(xxx)'
    assert notice._user_name == 'xxx'
    assert notice.group is None
    assert notice.group_id is None
    assert notice.group_name == '(yyy)'
    assert notice._group_name == 'yyy'


def test_notice_change(session):
    users = UserCollection(session)

    session.add(GazetteNoticeChange(text='text', channel_id='channel'))
    session.flush()

    change = session.query(GazetteNoticeChange).one()
    assert change.text == 'text'
    assert change.channel_id == 'channel'
    assert change.user is None
    assert change.user_name is None
    assert change._user_name is None
    assert change.notice is None
    assert change.event is None

    # Add user
    change.event = 'event'
    user = users.add('1@2.com', 'test', 'editor')
    change.user = user
    session.flush()
    session.refresh(change)

    assert change.text == 'text'
    assert change.channel_id == 'channel'
    assert change.user == user
    assert change.user_name == '1@2.com'
    assert change._user_name == '1@2.com'
    assert change.notice is None
    assert change.event == 'event'
    assert user.changes == [change]

    # Add to notice
    session.add(GazetteNotice(state='drafted', title='title', name='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()
    change.notice = notice

    assert notice.changes.one() == change

    # Rename user
    user.realname = 'Peter'
    session.flush()
    session.refresh(change)

    assert change.user == user
    assert change.user_name == 'Peter'
    assert change._user_name == 'Peter'
    assert user.changes == [change]

    # Delete user
    users.delete(user.username)
    session.flush()
    session.refresh(change)

    assert change.user is None
    assert change.user_name == '(Peter)'
    assert change._user_name == 'Peter'


def test_notice_states(session):

    class DummyIdentity():
        userid = None

    user = UserCollection(session).add('1@2.com', 'test', 'publisher')

    session.add(GazetteNotice(state='drafted', title='title', name='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()

    request = DummyRequest(session)
    with raises(AssertionError):
        notice.accept(request)
    with raises(AssertionError):
        notice.reject(request, 'XXX')
    with raises(AssertionError):
        notice.publish(request)
    notice.submit(request)

    with raises(AssertionError):
        notice.submit(request)
    with raises(AssertionError):
        notice.publish(request)
    notice.reject(request, 'Some reason')
    notice.submit(request)
    notice.reject(request, 'Some other reason')
    notice.submit(request)
    notice.accept(request)

    with raises(AssertionError):
        notice.submit(request)
    with raises(AssertionError):
        notice.accept(request)
    with raises(AssertionError):
        notice.reject(request, 'Some reason')

    notice.publish(request)

    with raises(AssertionError):
        notice.submit(request)
    with raises(AssertionError):
        notice.accept(request)
    with raises(AssertionError):
        notice.reject(request, 'Some reason')
    with raises(AssertionError):
        notice.publish(request)

    notice.add_change(request, 'printed')

    request.identity = DummyIdentity()
    request.identity.userid = user.username
    notice.add_change(request, 'finished', text='all went well')
    session.flush()
    session.refresh(user)

    # the test might be to fast for the implicit ordering by id, we sort it
    # ourselves
    changes = notice.changes.order_by(None)
    changes = changes.order_by(GazetteNoticeChange.edited.desc())
    assert [
        (change.event, change.user, change.text) for change in changes
    ] == [
        ('submitted', None, ''),
        ('rejected', None, 'Some reason'),
        ('submitted', None, ''),
        ('rejected', None, 'Some other reason'),
        ('submitted', None, ''),
        ('accepted', None, ''),
        ('published', None, ''),
        ('printed', None, ''),
        ('finished', user, 'all went well')
    ]
    assert notice.rejected_comment == 'Some other reason'

    assert [
        (change.event, change.user, change.text) for change in user.changes
    ] == [
        ('finished', user, 'all went well')
    ]


def test_notice_apply_meta(session, categories, organizations, issues):
    notice = GazetteNotice()

    notice.apply_meta(session)
    assert notice.organization is None
    assert notice.category is None
    assert notice.first_issue is None

    notice.organization_id = 'invalid'
    notice.category_id = 'invalid'
    notice.issues = [str(IssueName(2020, 1))]
    notice.apply_meta(session)
    assert notice.organization is None
    assert notice.category is None
    assert notice.first_issue is None

    notice.organization_id = '100'
    notice.category_id = '12'
    notice.issues = [str(IssueName(2017, 46))]
    notice.apply_meta(session)
    assert notice.organization == 'State Chancellery'
    assert notice.category == 'Submissions'
    assert notice.first_issue == standardize_date(
        datetime(2017, 11, 17), 'UTC'
    )

    notice.issues = [str(IssueName(2017, 46)), str(IssueName(2017, 40))]
    notice.apply_meta(session)
    assert notice.first_issue == standardize_date(
        datetime(2017, 10, 6), 'UTC'
    )


def test_notice_overdue_issues(session, issues):
    session.add(GazetteNotice(title='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()
    assert not notice.overdue_issues

    notice.issues = ['2017-40']
    with freeze_time("2017-01-01 12:00"):
        assert not notice.overdue_issues
    with freeze_time("2017-10-04 10:00"):
        assert not notice.overdue_issues

    with freeze_time("2017-10-04 12:01"):
        assert notice.overdue_issues
    with freeze_time("2018-01-01 12:00"):
        assert notice.overdue_issues


def test_notice_expired_issues(session, issues):
    session.add(GazetteNotice(title='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()
    assert not notice.expired_issues

    notice.issues = ['2017-40']
    with freeze_time("2017-01-01 12:00"):
        assert not notice.expired_issues
    with freeze_time("2017-10-05 23:59"):
        assert not notice.expired_issues

    with freeze_time("2017-10-06 00:01"):
        assert notice.expired_issues
    with freeze_time("2018-01-01 12:00"):
        assert notice.expired_issues


def test_notice_invalid_category(session, categories):
    session.add(GazetteNotice(title='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()
    assert notice.invalid_category

    notice.category_id = '0'
    assert notice.invalid_category

    notice.category_id = '10'
    assert notice.invalid_category

    notice.category_id = '13'
    assert not notice.invalid_category


def test_notice_invalid_organization(session, organizations):
    session.add(GazetteNotice(title='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()
    assert notice.invalid_organization

    notice.organization_id = '0'
    assert notice.invalid_organization

    notice.organization_id = '420'
    assert notice.invalid_organization

    notice.organization_id = '410'
    assert not notice.invalid_organization


def test_notice_file(gazette_app, session):
    session.add(GazetteNotice(title='notice'))
    session.flush()

    notice = session.query(GazetteNotice).one()
    notice.files.append(
        GazetteNoticeFile(
            id='abcd',
            name='test.txt',
            reference=as_fileintent('Test text.'.encode('utf-8'), 'test.txt')
        )
    )
    session.flush()

    file = session.query(GazetteNoticeFile).one()
    assert file.id == 'abcd'
    assert file.name == 'test.txt'
    assert file.type == 'gazette_notice'
    assert file.reference.file.read().decode('utf-8') == 'Test text.'

    assert notice.files[0] == file
    assert file.linked_official_notices[0] == notice
