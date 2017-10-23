from datetime import date
from datetime import datetime
from freezegun import freeze_time
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.models import IssueDates
from onegov.gazette.models import Principal
from onegov.gazette.models.notice import GazetteNoticeChange
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from pytest import raises
from sedate import standardize_date
from textwrap import dedent


def test_issue():
    issue = Issue(2017, 1)
    assert issue.year == 2017
    assert issue.number == 1
    assert Issue.from_string(str(issue)) == issue


def test_issue_dates():
    issue_dates = IssueDates(date(2015, 10, 10), datetime(2015, 9, 9, 9, 9))
    assert issue_dates.issue_date == date(2015, 10, 10)
    assert issue_dates.deadline == datetime(2015, 9, 9, 9, 9)
    assert IssueDates.from_string(str(issue_dates)) == issue_dates


def test_principal():
    principal = Principal.from_yaml(dedent("""
        name: Govikon
        color: '#aabbcc'
        logo: 'logo.svg'
        publish_to: 'printer@govikon.org'
        organizations:
        categories:
        issues:
    """))
    assert principal.name == 'Govikon'
    assert principal.color == '#aabbcc'
    assert principal.logo == 'logo.svg'
    assert principal.publish_to == 'printer@govikon.org'
    assert principal.publish_from == ''
    assert dict(principal.organizations) == {}
    assert dict(principal.categories) == {}
    assert dict(principal.issues) == {}
    assert dict(principal.issues_by_date) == {}

    principal = Principal.from_yaml(dedent("""
        name: Govikon
        color: '#aabbcc'
        logo: 'logo.svg'
        publish_to: 'printer@govikon.org'
        publish_from: 'publisher@govikon.org'
        help_link: 'https://help.me'
        organizations:
            - '1': Organization 1
            - '2': Örgänizätiön 2
        categories:
            - 'A': Category A
            - 'B': Category B
            - 'C': Category C
        issues:
            2018:
                1: 2018-01-05 / 2018-01-04T23:59:59
            2016:
                10: 2016-01-01 / 2015-12-31T23:59:59
            2017:
                40: 2017-10-06 / 2017-10-05T23:59:59
                50: 2017-12-15 / 2017-12-14T23:59:59
                52: 2017-12-29 / 2017-12-28T23:59:59
                41: 2017-10-13 / 2017-10-12T23:59:59
                46: 2017-11-17 / 2017-11-16T23:59:59
                45: 2017-11-10 / 2017-11-09T23:59:59
    """))
    assert principal.name == 'Govikon'
    assert principal.color == '#aabbcc'
    assert principal.logo == 'logo.svg'
    assert principal.publish_to == 'printer@govikon.org'
    assert principal.publish_from == 'publisher@govikon.org'
    assert principal.help_link == 'https://help.me'
    assert dict(principal.organizations) == {
        '1': 'Organization 1', '2': 'Örgänizätiön 2'
    }
    assert list(principal.organizations.keys()) == ['1', '2']
    assert dict(principal.categories) == {
        'C': 'Category C', 'B': 'Category B', 'A': 'Category A'
    }
    assert list(principal.categories.keys()) == ['A', 'B', 'C']
    assert list(principal.issues.keys()) == [2016, 2017, 2018]
    assert list(principal.issues[2016]) == [10]
    assert list(principal.issues[2017]) == [40, 41, 45, 46, 50, 52]
    assert list(principal.issues[2018]) == [1]
    assert [dates.issue_date for dates in principal.issues[2017].values()] == [
        date(2017, 10, 6),
        date(2017, 10, 13),
        date(2017, 11, 10),
        date(2017, 11, 17),
        date(2017, 12, 15),
        date(2017, 12, 29)
    ]
    assert [dates.deadline for dates in principal.issues[2017].values()] == [
        datetime(2017, 10, 5, 23, 59, 59),
        datetime(2017, 10, 12, 23, 59, 59),
        datetime(2017, 11, 9, 23, 59, 59),
        datetime(2017, 11, 16, 23, 59, 59),
        datetime(2017, 12, 14, 23, 59, 59),
        datetime(2017, 12, 28, 23, 59, 59)
    ]
    assert list(principal.issues_by_date.keys()) == [
        date(2016, 1, 1),
        date(2017, 10, 6),
        date(2017, 10, 13),
        date(2017, 11, 10),
        date(2017, 11, 17),
        date(2017, 12, 15),
        date(2017, 12, 29),
        date(2018, 1, 5)
    ]
    assert list(principal.issues_by_date.values()) == [
        Issue(2016, 10),
        Issue(2017, 40),
        Issue(2017, 41),
        Issue(2017, 45),
        Issue(2017, 46),
        Issue(2017, 50),
        Issue(2017, 52),
        Issue(2018, 1),
    ]
    assert list(principal.issues_by_deadline.keys()) == [
        datetime(2015, 12, 31, 23, 59, 59),
        datetime(2017, 10, 5, 23, 59, 59),
        datetime(2017, 10, 12, 23, 59, 59),
        datetime(2017, 11, 9, 23, 59, 59),
        datetime(2017, 11, 16, 23, 59, 59),
        datetime(2017, 12, 14, 23, 59, 59),
        datetime(2017, 12, 28, 23, 59, 59),
        datetime(2018, 1, 4, 23, 59, 59)
    ]
    assert list(principal.issues_by_deadline.values()) == [
        Issue(2016, 10),
        Issue(2017, 40),
        Issue(2017, 41),
        Issue(2017, 45),
        Issue(2017, 46),
        Issue(2017, 50),
        Issue(2017, 52),
        Issue(2018, 1),
    ]

    with raises(ValueError):
        principal.issue(None)
    with raises(ValueError):
        principal.issue('')
    with raises(ValueError):
        principal.issue('2015/1')
    assert principal.issue('2014-1') is None
    assert principal.issue(Issue(2016, 10)).deadline == \
        datetime(2015, 12, 31, 23, 59, 59)
    assert principal.issue('2016-10').deadline == \
        datetime(2015, 12, 31, 23, 59, 59)

    with freeze_time("2015-01-01 12:00"):
        assert principal.current_issue == Issue(2016, 10)
    with freeze_time("2017-12-14 12:00"):
        assert principal.current_issue == Issue(2017, 50)
    with freeze_time("2017-12-15 2:00"):
        assert principal.current_issue == Issue(2017, 52)
    with freeze_time("2020-01-01 0:00"):
        assert principal.current_issue == None


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
    assert change.user == None
    assert change.user_name == None
    assert change._user_name == None
    assert change.notice == None
    assert change.event == None

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
    assert change.notice == None
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

    assert change.user == None
    assert change.user_name == '(Peter)'
    assert change._user_name == 'Peter'


def test_gazette_notice_issues():
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

    notice.issues = {str(Issue(2017, 10)): 1004, str(Issue(2017, 11)): 1022}
    assert notice.issues == {'2017-10': 1004, '2017-11': 1022}


def test_gazette_notice_states(session):

    class DummyIdentity():
        userid = None

    class DummyRequest():
        identity = None

    user = UserCollection(session).add('1@2.com', 'test', 'publisher')

    session.add(GazetteNotice(state='drafted', title='title', name='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()

    request = DummyRequest()
    with raises(AssertionError):
        notice.accept(request)
    with raises(AssertionError):
        notice.reject(request, 'XXX')
    notice.submit(request)

    with raises(AssertionError):
        notice.submit(request)
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
    [(change.event, change.user, change.text) for change in changes]
    assert [
        (change.event, change.user, change.text) for change in changes
    ] == [
        ('submitted', None, ''),
        ('rejected', None, 'Some reason'),
        ('submitted', None, ''),
        ('rejected', None, 'Some other reason'),
        ('submitted', None, ''),
        ('accepted', None, ''),
        ('printed', None, ''),
        ('finished', user, 'all went well')
    ]
    assert notice.rejected_comment == 'Some other reason'

    assert [
        (change.event, change.user, change.text) for change in user.changes
    ] == [
        ('finished', user, 'all went well')
    ]


def test_gazette_notice_apply_meta(principal):
    notice = GazetteNotice()

    notice.apply_meta(principal)
    assert notice.organization is None
    assert notice.category is None
    assert notice.first_issue is None

    notice.organization_id = 'invalid'
    notice.category_id = 'invalid'
    notice.issues = [str(Issue(2020, 1))]
    notice.apply_meta(principal)
    assert notice.organization is None
    assert notice.category is None
    assert notice.first_issue is None

    notice.organization_id = '100'
    notice.category_id = '12'
    notice.issues = [str(Issue(2017, 46))]
    notice.apply_meta(principal)
    assert notice.organization == 'State Chancellery'
    assert notice.category == 'Submissions'
    assert notice.first_issue == standardize_date(
        datetime(2017, 11, 17), 'UTC'
    )

    notice.issues = [str(Issue(2017, 46)), str(Issue(2017, 40))]
    notice.apply_meta(principal)
    assert notice.first_issue == standardize_date(
        datetime(2017, 10, 6), 'UTC'
    )


def test_gazette_notice_overdue_issues(principal):
    notice = GazetteNotice()
    assert not notice.overdue_issues(principal)

    notice.issues = ['2017-40']
    with freeze_time("2017-01-01 12:00"):
        assert not notice.overdue_issues(principal)
    with freeze_time("2017-10-04 10:00"):
        assert not notice.overdue_issues(principal)

    with freeze_time("2017-10-04 12:01"):
        assert notice.overdue_issues(principal)
    with freeze_time("2018-01-01 12:00"):
        assert notice.overdue_issues(principal)


def test_gazette_notice_expired_issues(principal):
    notice = GazetteNotice()
    notice.expired_issues(principal)

    notice.issues = ['2017-40']
    with freeze_time("2017-01-01 12:00"):
        assert not notice.expired_issues(principal)
    with freeze_time("2017-10-05 23:59"):
        assert not notice.expired_issues(principal)

    with freeze_time("2017-10-06 00:01"):
        assert notice.expired_issues(principal)
    with freeze_time("2018-01-01 12:00"):
        assert notice.expired_issues(principal)
