from datetime import datetime
from datetime import timezone
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


def test_notice_collection_issues(session):
    notices = OfficialNoticeCollection(session)
    notices.add(title='a', text='text', issues=None)
    notices.add(title='b', text='text', issues=[])
    notices.add(title='c', text='text', issues=['1', '2'])
    notices.add(title='d', text='text', issues=['1'])
    notices.add(title='e', text='text', issues=['2'])
    notices.add(title='f', text='text', issues=['2', '3'])
    notices.add(title='g', text='text', issues=['4'])

    for issues, result in (
        (None, ['a', 'b', 'c', 'd', 'e', 'f', 'g']),
        ([], ['a', 'b', 'c', 'd', 'e', 'f', 'g']),
        (['1'], ['c', 'd']),
        (['2'], ['c', 'e', 'f']),
        (['3'], ['f']),
        (['4'], ['g']),
        (['1', '4'], ['c', 'd', 'g']),
        (['2', '3'], ['c', 'e', 'f']),
    ):
        notices.issues = issues
        assert sorted([notice.title for notice in notices.query()]) == result


def test_notice_collection_order(session):
    users = UserCollection(session)
    user_a = users.add('a@example.org', 'password', 'editor').id
    user_b = users.add('b@example.org', 'password', 'editor').id
    user_c = users.add('c@example.org', 'password', 'editor').id

    date_1 = datetime(2007, 10, 10, tzinfo=timezone.utc)
    date_2 = datetime(2007, 11, 11, tzinfo=timezone.utc)
    date_3 = datetime(2007, 12, 12, tzinfo=timezone.utc)

    notices = OfficialNoticeCollection(session)
    for title, text, user_id, organization, category, first_issue in (
        ('A', 'g', user_a, 'p', 'X', date_1),
        ('B', 'g', user_b, 'q', 'X', date_1),
        ('B', 'h', user_c, 'p', 'X', date_2),
        ('C', 'h', user_a, 'q', 'X', date_1),
        ('D', 'i', user_b, 'p', 'Y', date_1),
        ('E', 'j', user_c, 'q', 'Y', date_3),
    ):
        notices.add(
            title=title,
            text=text,
            user_id=user_id,
            organization=organization,
            category=category,
            first_issue=first_issue,
        )

    # Default ordering by title
    result = [n.title for n in notices.query()]
    assert result == ['A', 'B', 'B', 'C', 'D', 'E']

    # Explicit direction
    result = [n.title for n in notices.for_order('title', 'asc').query()]
    assert result == ['A', 'B', 'B', 'C', 'D', 'E']

    result = [n.title for n in notices.for_order('title', 'desc').query()]
    assert result == ['E', 'D', 'C', 'B', 'B', 'A']

    result = [n.title for n in notices.for_order('title', '').query()]
    assert result == ['A', 'B', 'B', 'C', 'D', 'E']

    result = [n.title for n in notices.for_order('title', 'xxx').query()]
    assert result == ['A', 'B', 'B', 'C', 'D', 'E']

    # Default direction
    # ... default
    result = [
        n.title
        for n in notices.for_order('text', 'desc').for_order('title').query()
    ]
    assert result == ['A', 'B', 'B', 'C', 'D', 'E']

    # ... flip direction
    result = [
        n.title
        for n in notices.for_order('title', 'asc').for_order('title').query()
    ]
    assert result == ['E', 'D', 'C', 'B', 'B', 'A']

    # Invalid
    result = [n.title for n in notices.for_order('result').query()]
    assert result == ['A', 'B', 'B', 'C', 'D', 'E']

    result = [n.title for n in notices.for_order('users').query()]
    assert result == ['A', 'B', 'B', 'C', 'D', 'E']

    result = [n.title for n in notices.for_order(None).query()]
    assert result == ['A', 'B', 'B', 'C', 'D', 'E']

    # Valid
    result = [n.text for n in notices.for_order('text').query()]
    assert result == ['g', 'g', 'h', 'h', 'i', 'j']

    result = [n.user_id for n in notices.for_order('user_id').query()]
    assert result == sorted(2 * [user_a] + 2 * [user_b] + 2 * [user_c])

    result = [
        n.organization for n in notices.for_order('organization').query()
    ]
    assert result == ['p', 'p', 'p', 'q', 'q', 'q']

    result = [n.category for n in notices.for_order('category').query()]
    assert result == ['X', 'X', 'X', 'X', 'Y', 'Y']

    result = [n.first_issue for n in notices.for_order('first_issue').query()]
    assert result == [date_1, date_1, date_1, date_1, date_2, date_3]

    result = [n.name for n in notices.for_order('name').query()]
    assert result == ['a', 'b', 'b-1', 'c', 'd', 'e']


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

    rejected = notices.for_state('rejected')
    assert rejected.subset_count == 12
    assert len(rejected.next.batch) == 12 - rejected.batch_size
