from collections import OrderedDict
from datetime import date
from datetime import datetime
from freezegun import freeze_time
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models.notice import GazetteNoticeChange
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from sedate import standardize_date
from transaction import commit


class DummyIdentity():
    def __init__(self, userid):
        self.userid = userid


class DummyApp(object):
    def __init__(self, principal):
        self.principal = principal


class DummyRequest(object):
    def __init__(self, principal, identity=None):
        self.app = DummyApp(principal)
        self.identity = identity


def test_category_collection(session):
    collection = CategoryCollection(session)

    collection.add_root(title='First', active=True)
    collection.add_root(title='Second', active=False)
    collection.add_root(title='Third')
    collection.add_root(title='Fourth', active=True)

    categories = collection.query().all()
    assert categories[0].title == 'First'
    assert categories[0].name == '1'

    assert categories[1].title == 'Fourth'
    assert categories[1].name == '4'

    assert categories[2].title == 'Second'
    assert categories[2].name == '2'

    assert categories[3].title == 'Third'
    assert categories[3].name == '3'


def test_organization_collection(session):
    collection = OrganizationCollection(session)

    collection.add_root(title='First', active=True)
    collection.add_root(title='Second', active=False)
    collection.add_root(title='Third')
    collection.add_root(title='Fourth', active=True)

    categories = collection.query().all()
    assert categories[0].title == 'First'
    assert categories[0].name == '1'

    assert categories[1].title == 'Fourth'
    assert categories[1].name == '4'

    assert categories[2].title == 'Second'
    assert categories[2].name == '2'

    assert categories[3].title == 'Third'
    assert categories[3].name == '3'


def test_issue_collection(session):
    collection = IssueCollection(session)

    issue_1 = collection.add(
        name='2017-1', number=1, date=date(2017, 1, 2),
        deadline=standardize_date(datetime(2017, 1, 1, 12, 0), 'UTC')
    )
    issue_3 = collection.add(
        name='2017-3', number=3, date=date(2017, 3, 2),
        deadline=standardize_date(datetime(2017, 3, 1, 12, 0), 'UTC')
    )
    issue_2 = collection.add(
        name='2017-2', number=2, date=date(2017, 2, 2),
        deadline=standardize_date(datetime(2017, 2, 1, 12, 0), 'UTC')
    )
    issue_4 = collection.add(
        name='2018-1', number=1, date=date(2018, 1, 1),
        deadline=standardize_date(datetime(2017, 12, 20, 12, 0), 'UTC')
    )

    # test query
    assert [issue.name for issue in collection.query()] == [
        '2017-1', '2017-2', '2017-3', '2018-1'
    ]

    # test current issue
    with freeze_time("2017-01-01 11:00"):
        assert collection.current_issue == issue_1
    with freeze_time("2017-01-01 13:00"):
        assert collection.current_issue == issue_2
    with freeze_time("2017-02-10 13:00"):
        assert collection.current_issue == issue_3
    with freeze_time("2017-12-10 13:00"):
        assert collection.current_issue == issue_4
    with freeze_time("2018-04-10 13:00"):
        assert collection.current_issue is None

    # test by name
    assert collection.by_name('2017-1') == issue_1
    assert collection.by_name('2017-2') == issue_2
    assert collection.by_name('2017-3') == issue_3
    assert collection.by_name('2018-1') == issue_4
    assert collection.by_name('2018-2') is None

    # test years
    assert collection.years == [2017, 2018]
    assert collection.by_years() == OrderedDict((
        (2017, [issue_1, issue_2, issue_3]),
        (2018, [issue_4]),
    ))
    assert collection.by_years(desc=True) == OrderedDict((
        (2018, [issue_4]),
        (2017, [issue_3, issue_2, issue_1]),
    ))


def test_notice_collection(session, organizations, categories, issues):
    user = UserCollection(session).add(
        username='a@a.a', password='a', role='admin'
    )

    collection = GazetteNoticeCollection(session)
    collection.add(
        title='Notice A',
        text='An <strong>important</strong> Notice!',
        organization_id='100',
        category_id='11',
        issues=['2017-46', '2017-47'],
        user=user
    )
    collection.add(
        title='Notice B',
        text='Another Notice',
        organization_id='200',
        category_id='13',
        issues={'2017-47', '2017-48'},
        user=user
    )

    notice = collection.for_term('Notice A').query().one()
    assert notice.title == 'Notice A'
    assert notice.text == 'An <strong>important</strong> Notice!'
    assert notice.organization_id == '100'
    assert notice.organization == 'State Chancellery'
    assert notice.category_id == '11'
    assert notice.category == 'Education'
    assert notice.issues == {'2017-46': None, '2017-47': None}
    assert notice.first_issue == standardize_date(
        datetime(2017, 11, 17), 'UTC'
    )
    assert notice.user == user
    assert notice.changes.one().event == 'created'
    assert notice.changes.one().user == user

    notice = collection.for_term('Notice B').query().one()
    assert notice.title == 'Notice B'
    assert notice.text == 'Another Notice'
    assert notice.organization_id == '200'
    assert notice.organization == 'Civic Community'
    assert notice.category_id == '13'
    assert notice.category == 'Commercial Register'
    assert notice.issues == {'2017-47': None, '2017-48': None}
    assert notice.first_issue == standardize_date(
        datetime(2017, 11, 24), 'UTC'
    )
    assert notice.user == user
    assert notice.changes.one().event == 'created'
    assert notice.changes.one().user == user


def test_notice_collection_issues(session, issues):
    collection = GazetteNoticeCollection(session)
    assert collection.from_date is None
    assert collection.to_date is None
    assert collection.issues is None
    assert collection.issues is None

    for start, end, length in (
        (date(2015, 1, 1), date(2020, 1, 1), 14),
        (None, date(2020, 1, 1), 14),
        (date(2015, 1, 1), None, 14),
        (date(2017, 10, 14), date(2017, 11, 18), 5),
        (None, date(2017, 11, 18), 7),
        (date(2017, 10, 14), None, 12),
        (date(2017, 10, 20), date(2017, 10, 20), 1),
        (date(2017, 10, 21), date(2017, 10, 21), 0),
        (date(2017, 10, 1), date(2017, 9, 1), 0),
    ):
        collection = collection.for_dates(start, end)
        assert len(collection.issues) == length

    collection = collection.for_dates(date(2017, 12, 1), date(2017, 12, 10))
    assert sorted(collection.issues) == ['2017-48', '2017-49']


def test_notice_collection_own_user_id(session):
    users = UserCollection(session)
    user_a = users.add(username='a@a.a', password='a', role='admin')
    user_b = users.add(username='b@b.b', password='b', role='admin')
    user_c = users.add(username='c@c.c', password='c', role='admin')

    collection = GazetteNoticeCollection(session)
    for title, user, annotators in (
        ('A', user_a, []),
        ('B', user_b, [user_a]),
        ('C', user_c, [user_a, user_b]),
    ):
        notice = collection.add(
            title=title,
            text='Text',
            organization_id='100',
            category_id='11',
            issues=['2017-46'],
            user=user
        )
        for annotator in annotators:
            notice.changes.append(
                GazetteNoticeChange(
                    channel_id=str(notice.id),
                    owner=str(annotator.id),
                )
            )

    assert collection.query().count() == 3

    collection.own_user_id = str(user_a.id)
    assert collection.query().count() == 3

    collection.own_user_id = str(user_b.id)
    assert collection.query().count() == 2

    collection.own_user_id = str(user_c.id)
    assert collection.query().count() == 1


def test_notice_collection_query_deleted_user(session):
    groups = UserGroupCollection(session)
    group_a = groups.add(name="Group A")
    group_b = groups.add(name="Group B")

    users = UserCollection(session)
    user_a = users.add(
        realname="User A",
        username='a@a.a',
        password='a',
        role='admin',
        group=group_a
    )
    user_b = users.add(
        realname="User B",
        username='b@b.b',
        password='b',
        role='admin',
        group=group_b
    )

    notices = GazetteNoticeCollection(session)
    notice_a = notices.add(
        title='A',
        text='Text',
        organization_id='100',
        category_id='11',
        issues=['2017-46'],
        user=user_a
    )
    notice_b = notices.add(
        title='B',
        text='Text',
        organization_id='100',
        category_id='11',
        issues=['2017-46'],
        user=user_b
    )

    assert notices.query().count() == 2

    assert notice_a.user is not None
    assert notice_b.user is not None
    assert notice_a.group is not None
    assert notice_b.group is not None

    assert notices.for_term("User A").query().one() == notice_a
    assert notices.for_term("User B").query().one() == notice_b
    assert notices.for_term("Group A").query().one() == notice_a
    assert notices.for_term("Group B").query().one() == notice_b

    users.delete(user_a.username)
    users.delete(user_b.username)
    groups.delete(group_a)
    groups.delete(group_b)
    commit()

    assert users.query().count() == 0
    assert groups.query().count() == 0

    notice_a = notices.query().filter(GazetteNotice.title == 'A').one()
    notice_b = notices.query().filter(GazetteNotice.title == 'B').one()

    assert notice_a.user is None
    assert notice_b.user is None
    assert notice_a.group is None
    assert notice_b.group is None

    assert notices.query().count() == 2
    assert notices.for_term("User A").query().one() == notice_a
    assert notices.for_term("User B").query().one() == notice_b
    assert notices.for_term("Group A").query().one() == notice_a
    assert notices.for_term("Group B").query().one() == notice_b


def test_notice_collection_on_request(session):
    collection = GazetteNoticeCollection(session)

    collection.on_request(DummyRequest(None))
    assert collection.own_user_id is None

    collection.own = True
    collection.on_request(DummyRequest(None))
    assert collection.own_user_id is None

    collection.on_request(DummyRequest(None, DummyIdentity(None)))
    assert collection.own_user_id is None

    collection.on_request(DummyRequest(None, DummyIdentity('a@a.a')))
    assert collection.own_user_id is None

    users = UserCollection(session)
    user = users.add(username='a@a.a', password='a', role='admin')

    collection.on_request(DummyRequest(None, DummyIdentity('a@a.a')))
    assert collection.own_user_id == str(user.id)


def test_notice_collection_for_organizations(session):
    collection = GazetteNoticeCollection(session)

    organizations = OrganizationCollection(session)
    organizations.add_root(name='1', title='A')
    organizations.add_root(name='2', title='B')
    organizations.add_root(name='3', title='C')
    for organization, count in (('1', 2), ('2', 4), ('3', 10)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=organization,
                category_id='',
                issues=['2017-{}'.format(y) for y in range(x)],
                user=None
            )

    assert collection.for_organizations(['1']).query().count() == 2
    assert collection.for_organizations(['2']).query().count() == 4
    assert collection.for_organizations(['3']).query().count() == 10
    assert collection.for_organizations(['1', '3']).query().count() == 12


def test_notice_collection_for_categories(session):
    collection = GazetteNoticeCollection(session)

    categories = CategoryCollection(session)
    categories.add_root(name='1', title='A')
    categories.add_root(name='2', title='B')
    categories.add_root(name='3', title='C')
    for category, count in (('1', 2), ('2', 4), ('3', 1)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=None,
                category_id=category,
                issues=['2017-{}'.format(y) for y in range(x)],
                user=None
            )

    assert collection.for_categories(['1']).query().count() == 2
    assert collection.for_categories(['2']).query().count() == 4
    assert collection.for_categories(['3']).query().count() == 1
    assert collection.for_categories(['1', '3']).query().count() == 3


def test_notice_collection_count_by_organization(session):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_organization() == []

    organizations = OrganizationCollection(session)
    organizations.add_root(name='1', title='A')
    organizations.add_root(name='2', title='B')
    organizations.add_root(name='3', title='C')
    for organization, count in (('1', 2), ('2', 4), ('3', 10)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=organization,
                category_id='',
                issues=['2017-{}'.format(y) for y in range(x)],
                user=None
            )
    assert collection.count_by_organization() == [
        ('A', 1), ('B', 6), ('C', 45),
    ]

    assert collection.count_by_organization() == \
        collection.for_state('drafted').count_by_organization()

    collection.issues = ['2017-1', '2017-4']
    assert collection.count_by_organization() == [('B', 2), ('C', 13)]


def test_notice_collection_count_by_category(session):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_category() == []

    categories = CategoryCollection(session)
    categories.add_root(name='1', title='A')
    categories.add_root(name='2', title='B')
    categories.add_root(name='3', title='C')
    for category, count in (('1', 2), ('2', 4), ('3', 1)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=None,
                category_id=category,
                issues=['2017-{}'.format(y) for y in range(x)],
                user=None
            )
    assert collection.count_by_category() == [('A', 1), ('B', 6)]

    assert collection.count_by_category() == \
        collection.for_state('drafted').count_by_category()

    collection.issues = ['2017-0', '2017-2']
    assert collection.count_by_category() == [('A', 1), ('B', 4)]


def test_notice_collection_count_by_group(session):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_group() == []

    groups = UserGroupCollection(session)
    group_a = groups.add(name='A')
    group_b = groups.add(name='B')
    groups.add(name='C')

    users = UserCollection(session)
    user_a = users.add('a@example.org', 'pw', 'editor', group=group_a)
    user_b = users.add('b@example.org', 'pw', 'editor', group=group_a)
    user_c = users.add('c@example.org', 'pw', 'admin')
    user_d = users.add('d@example.org', 'pw', 'publisher')
    user_e = users.add('e@example.org', 'pw', 'publisher', group=group_b)
    user_f = users.add('f@example.org', 'pw', 'publisher')
    user_g = users.add('g@example.org', 'pw', 'publisher')
    user_h = users.add('h@example.org', 'pw', 'publisher')

    for user, count in (
        (user_a, 2),
        (user_b, 4),
        (user_c, 1),
        (user_d, 7),
        (user_e, 2),
        (user_f, 3),
        (user_g, 6),
        (user_h, 2),
    ):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id='',
                category_id='',
                issues=['2017-{}'.format(y) for y in range(x)],
                user=user
            )
    assert collection.count_by_group() == [
        ('A', 7), ('B', 1)
    ]

    assert collection.count_by_group() == \
        collection.for_state('drafted').count_by_group()

    collection.issues = ['2017-2', '2017-4']
    assert collection.count_by_group() == [
        ('A', 1)
    ]


def test_notice_collection_used_issues(session):
    collection = GazetteNoticeCollection(session)

    issues = IssueCollection(session)
    a = issues.add(
        name='2017-1', number=1, date=date(2017, 1, 2),
        deadline=standardize_date(datetime(2017, 1, 1, 12, 0), 'UTC')
    )
    b = issues.add(
        name='2017-2', number=2, date=date(2017, 2, 2),
        deadline=standardize_date(datetime(2017, 2, 1, 12, 0), 'UTC')
    )
    c = issues.add(
        name='2017-3', number=3, date=date(2017, 3, 2),
        deadline=standardize_date(datetime(2017, 3, 1, 12, 0), 'UTC')
    )
    for issues in (('3', '2'), ('1',), ('1', '3')):
        collection.add(
            title='',
            text='',
            organization_id='',
            category_id='',
            issues=[f'2017-{issue}' for issue in issues],
            user=None
        )

    assert collection.used_issues == [a, b, c]


def test_notice_collection_used_organizations(session):
    collection = GazetteNoticeCollection(session)

    organizations = OrganizationCollection(session)
    a = organizations.add_root(name='1', title='A')
    b = organizations.add_root(name='2', title='B')
    c = organizations.add_root(name='3', title='C')
    for organization, count in (('1', 2), ('2', 4), ('3', 10)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=organization,
                category_id='',
                issues=['2017-{}'.format(y) for y in range(x)],
                user=None
            )

    assert collection.used_organizations == [a, b, c]


def test_notice_collection_used_categories(session):
    collection = GazetteNoticeCollection(session)

    categories = CategoryCollection(session)
    a = categories.add_root(name='1', title='A')
    b = categories.add_root(name='2', title='B')
    c = categories.add_root(name='3', title='C')
    for category, count in (('1', 2), ('2', 4), ('3', 1)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=None,
                category_id=category,
                issues=['2017-{}'.format(y) for y in range(x)],
                user=None
            )

    assert collection.used_categories == [a, b, c]
