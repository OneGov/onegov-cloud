from onegov.notice import OfficialNoticeCollection
from onegov.user import UserCollection
from transaction import commit


def test_notice_collection(session):
    notices = OfficialNoticeCollection(session)
    assert notices.query().count() == 0

    notice_1 = notices.add(
        title='Important Announcement',
        text='<em>Important</em> things happened!',
        category='important',
        organization='onegov'
    )
    notice_1.submit()
    notice_1.accept()
    notice_1.publish()

    commit()

    notice_1 = notices.query().one()
    assert notice_1.title == 'Important Announcement'
    assert notice_1.text == '<em>Important</em> things happened!'
    assert notice_1.category == 'important'
    assert notice_1.organization == 'onegov'

    notice_2 = notices.add(
        title='Important Announcement',
        text='<em>Important</em> things happened!'
    )
    notice_2.submit()

    assert notices.query().count() == 2
    assert notices.for_state('drafted').query().count() == 0
    assert notices.for_state('submitted').query().count() == 1
    assert notices.for_state('accepted').query().count() == 0
    assert notices.for_state('published').query().count() == 1

    assert notices.by_name('important-announcement')
    assert notices.by_name('important-announcement-1')

    assert notices.by_id(notice_1.id)
    assert notices.by_id(notice_2.id)

    notices.delete(notice_1)
    notices.delete(notice_2)

    assert notices.query().count() == 0
    assert notices.for_state('drafted').query().count() == 0
    assert notices.for_state('submitted').query().count() == 0
    assert notices.for_state('accepted').query().count() == 0
    assert notices.for_state('published').query().count() == 0


def test_notice_collection_search(session):
    notices = OfficialNoticeCollection(session)
    for title, text, state in (
        ('First', 'Lorem Ipsum', 'drafted'),
        ('Second', 'A text', 'submitted'),
        ('Third', 'Anöther text', 'drafted'),
        ('Fourth', 'A fourth text', 'published'),
        ('Fifth', 'Lorem Ipsum', 'rejected'),
        ('Sixt', '<p>Six</p>', 'published'),
        ('Sübent', 'Sübent', 'drafted'),
    ):
        notice = notices.add(title=title, text=text)
        notice.state = state

    assert notices.query().count() == 7

    notices.term = 'Third'
    assert notices.query().count() == 1

    notices.term = 'ourth'
    assert notices.query().count() == 1

    notices.term = 'ipsum'
    assert notices.query().count() == 2
    assert notices.for_state('rejected').query().count() == 1

    notices.term = 'six'
    assert notices.query().count() == 1
    assert notices.for_state('rejected').query().count() == 0

    notices.term = 'üb'
    assert notices.query().count() == 1


def test_notice_collection_users(session):
    users = UserCollection(session)
    user_a = users.add('a@example.org', 'password', 'editor').id
    user_b = users.add('b@example.org', 'password', 'editor').id
    user_c = users.add('c@example.org', 'password', 'editor').id

    notices = OfficialNoticeCollection(session)
    notices.add(title='A1', text='text', user_id=user_a)
    notices.add(title='A2', text='text', user_id=user_a)
    notices.add(title='A3', text='text', user_id=user_a)
    notices.add(title='B1', text='text', user_id=user_b)
    notices.add(title='B2', text='text', user_id=user_b)
    notices.add(title='C1', text='text', user_id=user_c)
    notices.add(title='C2', text='text', user_id=user_c)

    assert notices.query().count() == 7

    notices.user_ids = [user_a]
    assert notices.query().count() == 3

    notices.user_ids = [user_b]
    assert notices.query().count() == 2

    notices.user_ids = [user_c]
    assert notices.query().count() == 2

    notices.user_ids = [user_a, user_c]
    assert notices.query().count() == 5
    assert sorted([notice.title for notice in notices.query()]) == [
        'A1', 'A2', 'A3', 'C1', 'C2'
    ]


def test_notice_collection_pagination(session):
    notices = OfficialNoticeCollection(session)

    assert notices.page_index == 0
    assert notices.pages_count == 0
    assert notices.batch == []

    for year in range(2008, 2013):
        for month in range(1, 13):
            notice = notices.add(
                title='Notice {0}-{1}'.format(year, month),
                text='A' if month % 3 else 'B'
            )
            if 2009 <= year:
                notice.submit()
            if 2010 <= year <= 2011:
                notice.accept()
            if 2011 <= year <= 2011:
                notice.publish()
            if 2012 <= year:
                notice.reject()

    assert notices.query().count() == 60

    drafted = notices.for_state('drafted')
    assert drafted.subset_count == 12
    assert len(drafted.next.batch) == 12 - drafted.batch_size

    submitted = notices.for_state('submitted')
    assert submitted.subset_count == 12
    assert len(submitted.next.batch) == 12 - submitted.batch_size

    accepted = notices.for_state('accepted')
    assert accepted.subset_count == 12
    assert len(accepted.next.batch) == 12 - accepted.batch_size

    published = notices.for_state('published')
    assert published.subset_count == 12
    assert len(published.next.batch) == 12 - published.batch_size

    published.term = 'A'
    assert published.subset_count == 12
    assert len(published.next.batch) == 0
