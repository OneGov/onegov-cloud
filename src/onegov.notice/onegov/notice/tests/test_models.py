from datetime import datetime
from datetime import timezone
from onegov.notice import OfficialNotice
from onegov.user import User
from pytest import raises
from transaction import commit


def test_create_notice(session):
    notice = OfficialNotice()
    notice.state = 'drafted'
    notice.title = 'Very Important Official Announcement'
    notice.text = '<em>Important</em> things happened!'
    notice.name = 'notice'
    notice.category = 'category'
    notice.organization = 'organization'
    notice.first_issue = datetime(2008, 1, 1, 0, 0, tzinfo=timezone.utc)
    session.add(notice)

    notice.submit()
    notice.accept()
    notice.publish()

    commit()

    notice = session.query(OfficialNotice).one()

    assert notice.state == 'published'
    assert notice.title == 'Very Important Official Announcement'
    assert notice.text == '<em>Important</em> things happened!'
    assert notice.name == 'notice'
    assert notice.category == 'category'
    assert notice.organization == 'organization'
    assert notice.first_issue == datetime(
        2008, 1, 1, 0, 0, tzinfo=timezone.utc
    )


def test_ownership(session):
    user = User(username='hans@dampf.ch', password='1234', role='admin')
    session.add(user)

    notice = OfficialNotice(
        title='title',
        state='drafted',
        text='Text',
    )
    notice.user = user
    session.add(notice)

    session.flush()
    commit()

    assert session.query(OfficialNotice).one().user.username == 'hans@dampf.ch'


def test_transitions():

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


def test_polymorphism(session):

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


def test_issues(session):
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
