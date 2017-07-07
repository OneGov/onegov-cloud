from datetime import datetime
from onegov.notice import OfficialNotice
from onegov.user import User
from pytest import raises
from sedate import replace_timezone
from transaction import commit


def tzdatetime(year, month, day, hour, minute, timezone):
    return replace_timezone(datetime(year, month, day, hour, minute), timezone)


def test_create_notice(session):
    timezone = 'Europe/Zurich'
    issue_date = tzdatetime(2008, 2, 7, 10, 15, timezone)
    title = 'Very Important Official Announcement'
    text = '<em>Important</em> things happened!'

    notice = OfficialNotice()
    notice.state = 'drafted'
    notice.issue_date = issue_date
    notice.timezone = timezone
    notice.title = title
    notice.text = text
    notice.name = 'notice'
    notice.code = 'code'
    notice.category = 'category'
    session.add(notice)

    notice.submit()
    notice.publish()

    commit()

    notice = session.query(OfficialNotice).one()

    assert notice.state == 'published'
    assert notice.issue_date == issue_date
    assert notice.timezone == timezone
    assert notice.issue_date_localized == issue_date
    assert str(notice.issue_date.tzinfo) == 'UTC'
    assert str(notice.issue_date_localized.tzinfo) == timezone
    assert notice.title == title
    assert notice.content == {'text': text}
    assert notice.text == text
    assert notice.name == 'notice'
    assert notice.code == 'code'
    assert notice.category == 'category'


def test_ownership(session):
    user = User(username='hans@dampf.ch', password='1234', role='admin')
    session.add(user)

    notice = OfficialNotice(
        title='title',
        state='drafted',
        issue_date=tzdatetime(2008, 2, 7, 10, 15, 'US/Eastern'),
        timezone='US/Eastern',
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
        notice.publish()
    with raises(AssertionError):
        notice.reject()
    with raises(AssertionError):
        notice.withdraw()
    notice.submit()
    assert notice.state == 'submitted'

    # Submitted
    notice = OfficialNotice(state='submitted')
    with raises(AssertionError):
        notice.submit()
    notice.withdraw()
    assert notice.state == 'drafted'

    notice = OfficialNotice(state='submitted')
    notice.publish()
    assert notice.state == 'published'

    notice = OfficialNotice(state='submitted')
    notice.reject()
    assert notice.state == 'rejected'

    # Published
    notice = OfficialNotice(state='published')
    with raises(AssertionError):
        notice.submit()
    with raises(AssertionError):
        notice.publish()
    with raises(AssertionError):
        notice.withdraw()

    # Rejected
    notice = OfficialNotice(state='rejected')
    with raises(AssertionError):
        notice.submit()
    with raises(AssertionError):
        notice.publish()
    with raises(AssertionError):
        notice.withdraw()


def test_polymorphism(session):

    class MyOfficialNotice(OfficialNotice):
        __mapper_args__ = {'polymorphic_identity': 'my'}

    class MyOtherOfficialNotice(OfficialNotice):
        __mapper_args__ = {'polymorphic_identity': 'other'}

    session.add(
        OfficialNotice(
            title='original',
            state='drafted',
            issue_date=tzdatetime(2008, 2, 7, 10, 15, 'US/Eastern'),
            timezone='US/Eastern',
            text='Text',
        )
    )

    session.add(
        MyOfficialNotice(
            title='my',
            state='drafted',
            issue_date=tzdatetime(2008, 2, 7, 10, 15, 'US/Eastern'),
            timezone='US/Eastern',
            text='Text',
        )
    )

    session.add(
        MyOtherOfficialNotice(
            title='other',
            state='drafted',
            issue_date=tzdatetime(2008, 2, 7, 10, 15, 'US/Eastern'),
            timezone='US/Eastern',
            text='Text',
        )
    )

    session.flush()

    assert session.query(OfficialNotice).count() == 3
    assert session.query(MyOfficialNotice).one().title == 'my'
    assert session.query(MyOtherOfficialNotice).one().title == 'other'
