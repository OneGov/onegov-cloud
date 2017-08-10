from datetime import date
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.models import Principal
from onegov.gazette.models import UserGroup
from onegov.gazette.models.notice import GazetteNoticeChange
from onegov.user import User
from pytest import raises
from textwrap import dedent


def test_issue():
    issue = Issue(2017, 1)
    assert issue.year == 2017
    assert issue.number == 1
    assert Issue.from_string(str(issue)) == issue


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
    assert dict(principal.organizations) == {}
    assert dict(principal.categories) == {}
    assert dict(principal.issues) == {}
    assert dict(principal.issues_by_date) == {}

    principal = Principal.from_yaml(dedent("""
        name: Govikon
        color: '#aabbcc'
        logo: 'logo.svg'
        publish_to: 'printer@govikon.org'
        organizations:
            - '1': Organization 1
            - '2': Örgänizätiön 2
        categories:
            - 'A': Category A
            - 'B': Category B
            - 'C': Category C
        issues:
            2018:
                1: 2018-01-05
            2016:
                10: 2016-01-01
            2017:
                40: 2017-10-06
                50: 2017-12-15
                52: 2017-12-29
                41: 2017-10-13
                46: 2017-11-17
                45: 2017-11-10
    """))
    assert principal.name == 'Govikon'
    assert principal.color == '#aabbcc'
    assert principal.logo == 'logo.svg'
    assert principal.publish_to == 'printer@govikon.org'
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
    assert list(principal.issues[2017].values()) == [
        date(2017, 10, 6),
        date(2017, 10, 13),
        date(2017, 11, 10),
        date(2017, 11, 17),
        date(2017, 12, 15),
        date(2017, 12, 29)
    ]
    assert list(principal.issues_by_date) == [
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


def test_user_group(session):
    session.add(UserGroup(name='Group'))
    session.flush()

    group = session.query(UserGroup).one()
    assert group.number_of_users == 0

    session.add(User(username='1@2.com', password='test', role='editor'))
    session.flush()
    assert group.number_of_users == 0

    user = session.query(User).one()
    user.data = {}
    assert group.number_of_users == 0

    user.data['group'] = str(group.id)
    assert group.number_of_users == 1


def test_notice_change(session):
    session.add(GazetteNoticeChange(text='text', channel_id='channel'))
    session.flush()

    change = session.query(GazetteNoticeChange).one()
    assert change.text == 'text'
    assert change.channel_id == 'channel'
    assert change.user == None
    assert change.notice == None
    assert change.event == None

    session.add(User(username='1@2.com', password='test', role='editor'))
    session.flush()
    user = session.query(User).one()
    change.user = user
    change.meta = {'event': 'event'}

    session.add(GazetteNotice(state='drafted', title='title', name='notice'))
    session.flush()
    notice = session.query(GazetteNotice).one()
    change.notice = notice

    session.flush()
    assert user.changes.one().text == 'text'
    assert user.changes.one().event == 'event'
    assert notice.changes.one().text == 'text'
    assert notice.changes.one().event == 'event'


def test_gazette_notice_issues():
    notice = GazetteNotice()
    assert notice.issues == {}

    notice.issues = [1, 2, 3]
    assert notice.issues == {1: None, 2: None, 3: None}
    notice.issues = ['a', 'b', 'c']
    assert notice.issues == {'a': None, 'b': None, 'c': None}

    notice.issues = {1, 2, 3}
    assert notice.issues == {1: None, 2: None, 3: None}
    notice.issues = {'a', 'b', 'c'}
    assert notice.issues == {'a': None, 'b': None, 'c': None}

    notice.issues = {1: 'a', 2: 'b', 3: 'c'}
    assert notice.issues == {1: 'a', 2: 'b', 3: 'c'}
    notice.issues = {'a': 1, 'b': 2, 'c': 3}
    assert notice.issues == {'a': 1, 'b': 2, 'c': 3}

    notice.issues = {
        str(Issue(2017, 10)): 1004,
        str(Issue(2017, 11)): 1022,
    }
    assert notice.issues == {'2017-10': 1004, '2017-11': 1022}


def test_gazette_notice_states(session):

    class DummyIdentity():
        userid = None

    class DummyRequest():
        identity = None

    session.add(GazetteNotice(state='drafted', title='title', name='notice'))
    session.add(User(username='1@2.com', password='p', role='publisher'))
    session.flush()
    notice = session.query(GazetteNotice).one()
    user = session.query(User).one()

    request = DummyRequest()
    with raises(AssertionError):
        notice.publish(request)
    with raises(AssertionError):
        notice.reject(request, 'XXX')
    notice.submit(request)

    with raises(AssertionError):
        notice.submit(request)
    notice.reject(request, 'Some reason')
    notice.submit(request)
    notice.reject(request, 'Some other reason')
    notice.submit(request)
    notice.publish(request)

    with raises(AssertionError):
        notice.submit(request)
    with raises(AssertionError):
        notice.publish(request)
    with raises(AssertionError):
        notice.reject(request, 'Some reason')

    notice.add_change(request, 'printed')

    request.identity = DummyIdentity()
    request.identity.userid = user.username
    notice.add_change(request, 'finished', text='all went well')

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
