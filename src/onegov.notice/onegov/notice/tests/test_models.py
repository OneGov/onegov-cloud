from datetime import datetime
from datetime import timezone
from freezegun import freeze_time
from onegov.notice import OfficialNotice
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
from pytest import raises


def test_notice_create(session):
    notice = OfficialNotice()
    notice.state = 'drafted'
    notice.title = 'Very Important Official Announcement'
    notice.text = '<em>Important</em> things happened!'
    notice.author_name = 'Renward Cysat'
    notice.author_place = 'Wynmärkt'
    notice.author_date = datetime(1545, 1, 1, 0, 0, tzinfo=timezone.utc)
    notice.name = 'notice'
    notice.first_issue = datetime(2008, 1, 1, 0, 0, tzinfo=timezone.utc)
    notice.expiry_date = datetime(2018, 1, 1, 0, 0, tzinfo=timezone.utc)
    notice.category = 'category'
    notice.organization = 'organization'
    notice.note = 'note'
    session.add(notice)

    notice.submit()
    notice.accept()
    notice.publish()

    notice = session.query(OfficialNotice).one()

    assert notice.state == 'published'
    assert notice.title == 'Very Important Official Announcement'
    assert notice.text == '<em>Important</em> things happened!'
    assert notice.author_name == 'Renward Cysat'
    assert notice.author_place == 'Wynmärkt'
    assert notice.author_date == datetime(
        1545, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    assert notice.name == 'notice'
    assert notice.category == 'category'
    assert notice.organization == 'organization'
    assert notice.note == 'note'
    assert notice.first_issue == datetime(
        2008, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    assert notice.expiry_date == datetime(
        2018, 1, 1, 0, 0, tzinfo=timezone.utc
    )
    assert notice.categories == {}
    assert notice.organizations == {}
    assert notice.issues == {}


def test_notice_ownership(session):
    users = UserCollection(session)
    groups = UserGroupCollection(session)
    user = users.add('1@2.3', '1234', 'admin', realname='user')
    group = groups.add(name='group')

    notice = OfficialNotice(
        title='title',
        state='drafted',
        text='Text',
    )
    notice.user = user
    notice.group = group
    session.add(notice)
    session.flush()

    notice = session.query(OfficialNotice).one()
    notice.user == user
    notice.user.realname == 'user'
    notice.group == group
    notice.group.name == 'group'


def test_notice_expired(session):
    notice = OfficialNotice(
        title='title',
        state='drafted',
        text='Text',
    )
    session.add(notice)
    session.flush()

    notice = session.query(OfficialNotice).one()
    assert notice.expired is False

    notice.expiry_date = datetime(2018, 1, 2, 0, 0, tzinfo=timezone.utc)
    with freeze_time("2018-01-01"):
        assert notice.expired is False
    with freeze_time("2018-01-02"):
        assert notice.expired is False
    with freeze_time("2018-01-02 00:01"):
        assert notice.expired is True
    with freeze_time("2018-01-03"):
        assert notice.expired is True


def test_notice_transitions():

    # Drafted
    notice = OfficialNotice(state='drafted')
    assert notice.state == 'drafted'

    with raises(AssertionError):
        notice.reject()
    with raises(AssertionError):
        notice.accept()
    with raises(AssertionError):
        notice.publish()
    notice.submit()
    assert notice.state == 'submitted'

    # Submitted
    notice = OfficialNotice(state='submitted')
    with raises(AssertionError):
        notice.submit()
    with raises(AssertionError):
        notice.publish()
    notice.accept()
    assert notice.state == 'accepted'

    notice = OfficialNotice(state='submitted')
    notice.reject()
    assert notice.state == 'rejected'

    # Imported
    notice = OfficialNotice(state='imported')
    with raises(AssertionError):
        notice.submit()
    with raises(AssertionError):
        notice.publish()
    notice.accept()
    assert notice.state == 'accepted'

    # Accepted
    notice = OfficialNotice(state='accepted')
    with raises(AssertionError):
        notice.submit()
    with raises(AssertionError):
        notice.reject()
    with raises(AssertionError):
        notice.accept()
    notice.publish()
    assert notice.state == 'published'

    # Published
    notice = OfficialNotice(state='published')
    with raises(AssertionError):
        notice.submit()
    with raises(AssertionError):
        notice.reject()
    with raises(AssertionError):
        notice.accept()
    with raises(AssertionError):
        notice.publish()

    # Rejected
    notice = OfficialNotice(state='rejected')
    with raises(AssertionError):
        notice.reject()
    with raises(AssertionError):
        notice.accept()
    with raises(AssertionError):
        notice.publish()
    notice.submit()
    assert notice.state == 'submitted'


def test_notice_polymorphism(session):

    class MyOfficialNotice(OfficialNotice):
        __mapper_args__ = {'polymorphic_identity': 'my'}

    class MyOtherOfficialNotice(OfficialNotice):
        __mapper_args__ = {'polymorphic_identity': 'other'}

    session.add(
        OfficialNotice(
            title='original',
            state='drafted',
            text='Text',
        )
    )

    session.add(
        MyOfficialNotice(
            title='my',
            state='drafted',
            text='Text',
        )
    )

    session.add(
        MyOtherOfficialNotice(
            title='other',
            state='drafted',
            text='Text',
        )
    )

    session.flush()

    assert session.query(OfficialNotice).count() == 3
    assert session.query(MyOfficialNotice).one().title == 'my'
    assert session.query(MyOtherOfficialNotice).one().title == 'other'


def test_issue(session):
    session.add(OfficialNotice(title='title', state='drafted'))
    session.flush()
    notice = session.query(OfficialNotice).one()
    assert notice.issues == {}

    notice.issues = {
        '1': datetime(2010, 1, 1, 12, 0).isoformat(),
        '3': 'xxx-bbb-abd',
    }
    assert notice.issues == {
        '1': '2010-01-01T12:00:00',
        '3': 'xxx-bbb-abd'
    }

    notice.issues = ['a', 'b', 'c']
    assert notice.issues == {'a': None, 'b': None, 'c': None}


def test_category(session):
    session.add(OfficialNotice(title='title', state='drafted'))
    session.flush()
    notice = session.query(OfficialNotice).one()
    assert notice.categories == {}

    notice.categories = {
        'A': 'Category A',
        'B': 'Category B',
    }
    assert notice.categories == {
        'A': 'Category A',
        'B': 'Category B',
    }

    notice.categories = ['a', 'b', 'c']
    assert notice.categories == {'a': None, 'b': None, 'c': None}


def test_organization(session):
    session.add(OfficialNotice(title='title', state='drafted'))
    session.flush()
    notice = session.query(OfficialNotice).one()
    assert notice.organizations == {}

    notice.organizations = {
        'A': 'Organization A',
        'B': 'Organization B',
    }
    assert notice.organizations == {
        'A': 'Organization A',
        'B': 'Organization B',
    }

    notice.organizations = ['a', 'b', 'c']
    assert notice.organizations == {'a': None, 'b': None, 'c': None}
