from datetime import datetime
from datetime import timezone
from onegov.notice import OfficialNoticeCollection
from onegov.user import UserCollection
from onegov.user import UserGroupCollection
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
    groups = UserGroupCollection(session)
    group_a = groups.add(name='GroupA')
    group_b = groups.add(name='GroupB1')

    users = UserCollection(session)
    user_a = users.add('a@example.org', 'password', 'editor', realname='Hans')
    user_b = users.add('b@example.org', 'password', 'editor')

    notices = OfficialNoticeCollection(session)

    notice = notices.add(
        title='First',
        text='Lorem Ipsum',
        category='Cat1',
        group=group_a
    )
    notice.state = 'drafted'

    notice = notices.add(
        title='Second',
        text='A text',
        category='Cat1',
        organization='Org1',
        user=user_a,
        group=group_b
    )
    notice.state = 'submitted'

    notice = notices.add(
        title='Third',
        text='Anöther text',
        category='Cat2'
    )
    notice.state = 'drafted'

    notice = notices.add(
        title='Fourth',
        text='A fourth text',
        organization='Org2'
    )
    notice.state = 'published'

    notice = notices.add(
        title='Fifth',
        text='Lorem Ipsum',
        user=user_a
    )
    notice.state = 'rejected'

    notice = notices.add(
        title='Sixt',
        text='<p>Six</p>',
        author_name='Cysat',
        note='Papanikolaou',
        user=user_b,
        group=group_a
    )
    notice.state = 'published'

    notice = notices.add(
        title='Sübent',
        text='Sübent',
        author_place='Wynmärkt'
    )
    notice.state = 'drafted'

    assert notices.query().count() == 7

    assert notices.for_term('Third').query().count() == 1

    assert notices.for_term('ourth').query().count() == 1

    assert notices.for_term('ipsum').query().count() == 2
    assert notices.for_term('ipsum').for_state('rejected').query().count() == 1

    assert notices.for_term('six').query().count() == 1
    assert notices.for_term('six').for_state('rejected').query().count() == 0

    assert notices.for_term('üb').query().count() == 1

    assert notices.for_term('Cat1').query().count() == 2
    assert notices.for_term('Cat2').query().count() == 1
    assert notices.for_term('Cat').query().count() == 3

    assert notices.for_term('Org1').query().count() == 1
    assert notices.for_term('Org').query().count() == 4

    assert notices.for_term('@example.org').query().count() == 3
    assert notices.for_term('ans').query().count() == 2

    assert notices.for_term('group').query().count() == 3
    assert notices.for_term('groupb').query().count() == 1

    assert notices.for_term('Cysat').query().count() == 1

    assert notices.for_term('Wynmärkt').query().count() == 1

    assert notices.for_term('Papanikolaou').query().count() == 1

    assert notices.for_term(str(notice.id).split('-')[0]).query().count() == 1


def test_notice_collection_users_and_groups(session):
    groups = UserGroupCollection(session)
    group_ab = groups.add(name='AB')
    group_c = groups.add(name='C')
    group_d = groups.add(name='D')

    users = UserCollection(session)
    user_a = users.add('a@example.org', 'password', 'editor', group=group_ab)
    user_b = users.add('b@example.org', 'password', 'editor', group=group_ab)
    user_c = users.add('c@example.org', 'password', 'editor', group=group_c)
    user_d = users.add('d@example.org', 'password', 'editor', group=group_d)
    user_e = users.add('e@example.org', 'password', 'editor')

    notices = OfficialNoticeCollection(session)
    for title, user in (
        ('A1', user_a),
        ('A2', user_a),
        ('A3', user_a),
        ('B1', user_b),
        ('B2', user_b),
        ('C1', user_c),
        ('C2', user_c),
        ('D1', user_d),
        ('D2', user_d),
        ('D3', user_d),
    ):
        notices.add(
            title=title,
            text='text',
            user_id=user.id,
            group_id=user.group.id if user.group else None
        )

    assert notices.query().count() == 10

    # test users
    notices.user_ids = [user_a.id]
    assert sorted([n.title for n in notices.query()]) == ['A1', 'A2', 'A3']

    notices.user_ids = [user_b.id]
    assert sorted([n.title for n in notices.query()]) == ['B1', 'B2']

    notices.user_ids = [user_c.id]
    assert sorted([n.title for n in notices.query()]) == ['C1', 'C2']

    notices.user_ids = [user_d.id]
    assert sorted([n.title for n in notices.query()]) == ['D1', 'D2', 'D3']

    notices.user_ids = [user_e.id]
    assert sorted([n.title for n in notices.query()]) == []

    notices.user_ids = [user_b.id, user_c.id]
    assert sorted([n.title for n in notices.query()]) == [
        'B1', 'B2', 'C1', 'C2'
    ]

    # test groups
    notices.user_ids = []

    notices.group_ids = [group_ab.id]
    assert sorted([n.title for n in notices.query()]) == [
        'A1', 'A2', 'A3', 'B1', 'B2'
    ]

    notices.group_ids = [group_c.id]
    assert sorted([n.title for n in notices.query()]) == ['C1', 'C2']

    notices.group_ids = [group_d.id]
    assert sorted([n.title for n in notices.query()]) == ['D1', 'D2', 'D3']

    notices.group_ids = [group_ab.id, group_d.id]
    assert sorted([n.title for n in notices.query()]) == [
        'A1', 'A2', 'A3', 'B1', 'B2', 'D1', 'D2', 'D3'
    ]

    # test users and groups
    notices.group_ids = [group_ab.id, group_d.id]
    notices.user_ids = [user_b.id, user_d.id]
    assert sorted([n.title for n in notices.query()]) == [
        'B1', 'B2', 'D1', 'D2', 'D3'
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


def test_notice_collection_categories(session):
    notices = OfficialNoticeCollection(session)
    notices.add(title='a', text='text', categories=None)
    notices.add(title='b', text='text', categories=[])
    notices.add(title='c', text='text', categories=['1', '2'])
    notices.add(title='d', text='text', categories=['1'])
    notices.add(title='e', text='text', categories=['2'])
    notices.add(title='f', text='text', categories=['2', '3'])
    notices.add(title='g', text='text', categories=['4'])

    for categories, result in (
        (None, ['a', 'b', 'c', 'd', 'e', 'f', 'g']),
        ([], ['a', 'b', 'c', 'd', 'e', 'f', 'g']),
        (['1'], ['c', 'd']),
        (['2'], ['c', 'e', 'f']),
        (['3'], ['f']),
        (['4'], ['g']),
        (['1', '4'], ['c', 'd', 'g']),
        (['2', '3'], ['c', 'e', 'f']),
    ):
        assert sorted([
            n.title for n in notices.for_categories(categories).query()
        ]) == result


def test_notice_collection_organizations(session):
    notices = OfficialNoticeCollection(session)
    notices.add(title='a', text='text', organizations=None)
    notices.add(title='b', text='text', organizations=[])
    notices.add(title='c', text='text', organizations=['1', '2'])
    notices.add(title='d', text='text', organizations=['1'])
    notices.add(title='e', text='text', organizations=['2'])
    notices.add(title='f', text='text', organizations=['2', '3'])
    notices.add(title='g', text='text', organizations=['4'])

    for organizations, result in (
        (None, ['a', 'b', 'c', 'd', 'e', 'f', 'g']),
        ([], ['a', 'b', 'c', 'd', 'e', 'f', 'g']),
        (['1'], ['c', 'd']),
        (['2'], ['c', 'e', 'f']),
        (['3'], ['f']),
        (['4'], ['g']),
        (['1', '4'], ['c', 'd', 'g']),
        (['2', '3'], ['c', 'e', 'f']),
    ):
        assert sorted([
            n.title for n in notices.for_organizations(organizations).query()
        ]) == result


def test_notice_collection_order(session):
    groups = UserGroupCollection(session)
    group_c = groups.add(name='C').id
    group_d = groups.add(name='D').id

    users = UserCollection(session)
    user_a = users.add('a@example.org', 'password', 'editor', realname='o').id
    user_b = users.add('b@example.org', 'password', 'editor', realname='p').id
    user_c = users.add('c@example.org', 'password', 'editor').id

    date_1 = datetime(2007, 10, 10, tzinfo=timezone.utc)
    date_2 = datetime(2007, 11, 11, tzinfo=timezone.utc)
    date_3 = datetime(2007, 12, 12, tzinfo=timezone.utc)

    notices = OfficialNoticeCollection(session)
    for title, text, user, group, organization, category, first_issue in (
        ('A', 'g', user_a, group_c, 'p', 'X', date_1),
        ('B', 'g', user_b, group_d, 'q', 'X', date_1),
        ('B', 'h', None, None, 'p', 'X', date_2),
        ('C', 'h', user_a, None, 'q', 'X', date_1),
        ('D', 'i', user_b, group_d, 'p', 'Y', date_1),
        ('E', 'j', user_c, group_c, 'q', 'Y', date_3),
    ):
        notices.add(
            title=title,
            text=text,
            user_id=user,
            group_id=group,
            organization=organization,
            category=category,
            first_issue=first_issue,
        )

    # Default ordering by issue date
    result = [n.first_issue for n in notices.query()]
    assert result == [date_1, date_1, date_1, date_1, date_2, date_3]

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
    result = [n.first_issue for n in notices.for_order('result').query()]
    assert result == [date_1, date_1, date_1, date_1, date_2, date_3]

    result = [n.first_issue for n in notices.for_order('users').query()]
    assert result == [date_1, date_1, date_1, date_1, date_2, date_3]

    result = [n.first_issue for n in notices.for_order(None).query()]
    assert result == [date_1, date_1, date_1, date_1, date_2, date_3]

    # Valid
    result = [n.text for n in notices.for_order('text').query()]
    assert result == ['g', 'g', 'h', 'h', 'i', 'j']

    # ... user_id
    result = [n.user_id for n in notices.for_order('user_id').query()]
    assert result == sorted(2 * [user_a] + 2 * [user_b] + [user_c]) + [None]

    # ... organization
    result = [
        n.organization for n in notices.for_order('organization').query()
    ]
    assert result == ['p', 'p', 'p', 'q', 'q', 'q']

    # ... category
    result = [n.category for n in notices.for_order('category').query()]
    assert result == ['X', 'X', 'X', 'X', 'Y', 'Y']

    # ... name
    result = [n.name for n in notices.for_order('name').query()]
    assert result == ['a', 'b', 'b-1', 'c', 'd', 'e']

    # ... group.name
    result = [
        n.group.name if n.group else None
        for n in notices.for_order('group.name').query()
    ]
    assert result == [None, None, 'C', 'C', 'D', 'D']

    # ... user.name(s)
    result = [
        n.user.realname if n.user else None
        for n in notices.for_order('user.realname').query()
    ]
    assert result == [None, None, 'o', 'o', 'p', 'p']

    result = [
        n.user.username if n.user else None
        for n in notices.for_order('user.username').query()
    ]
    assert result == [
        None, 'a@example.org', 'a@example.org',
        'b@example.org', 'b@example.org', 'c@example.org'
    ]

    result = [
        n.user.realname or n.user.username if n.user else None
        for n in notices.for_order('user.name').query()
    ]
    assert result == [None, 'c@example.org', 'o', 'o', 'p', 'p']


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
