from datetime import datetime
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.collections import UserGroupCollection
from onegov.gazette.models import Principal
from onegov.user import UserCollection
from sedate import standardize_date


def test_user_group_collection(session):
    collection = UserGroupCollection(session)
    collection.add(name='A')
    collection.add(name='C')
    collection.add(name='B')
    assert [group.name for group in collection.query()] == ['A', 'B', 'C']


def test_notice_collection(session, principal):
    user = UserCollection(session).add(
        username='a@a.a', password='a', role='admin'
    )

    collection = GazetteNoticeCollection(session)
    collection.add(
        title='Notice A',
        text='An <strong>important</strong> Notice!',
        organization_id='100',
        category_id='14',
        issues=['2017-46', '2017-47'],
        user_id=user.id,
        principal=principal
    )
    collection.add(
        title='Notice B',
        text='Another Notice',
        organization_id='210',
        category_id='20',
        issues={'2017-47', '2017-48'},
        user_id=user.id,
        principal=principal
    )

    notice = collection.query().filter_by(title='Notice A').one()
    assert notice.title == 'Notice A'
    assert notice.text == 'An <strong>important</strong> Notice!'
    assert notice.organization_id == '100'
    assert notice.organization == 'Staatskanzlei Kanton Zug'
    assert notice.category_id == '14'
    assert notice.category == 'Kantonale Mitteilungen'
    assert notice.issues == {'2017-46': None, '2017-47': None}
    assert notice.issue_date == standardize_date(
        datetime(2017, 11, 17), 'Europe/Zurich'
    )
    assert notice.user == user
    assert notice.changes.one().event == 'created'
    assert notice.changes.one().user == user

    notice = collection.query().filter_by(title='Notice B').one()
    assert notice.title == 'Notice B'
    assert notice.text == 'Another Notice'
    assert notice.organization_id == '210'
    assert notice.organization == 'Bürgergemeinde Zug'
    assert notice.category_id == '20'
    assert notice.category == 'Handelsregister'
    assert notice.issues == {'2017-47': None, '2017-48': None}
    assert notice.issue_date == standardize_date(
        datetime(2017, 11, 24), 'Europe/Zurich'
    )
    assert notice.user == user
    assert notice.changes.one().event == 'created'
    assert notice.changes.one().user == user


def test_notice_collection_count_by_organization(session):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_organization() == []

    principal = Principal(organizations=[{'1': 'A'}, {'2': 'B'}, {'3': 'C'}])
    for organization, count in (('1', 2), ('2', 4), ('3', 10)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=organization,
                category_id='',
                issues=[],
                user_id=None,
                principal=principal
            )
    assert collection.count_by_organization() == [
        ('A', 2), ('B', 4), ('C', 10),
    ]

    assert collection.count_by_organization() == \
        collection.for_state('drafted').count_by_organization()


def test_notice_collection_count_by_category(session):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_category() == []

    principal = Principal(categories=[{'1': 'A'}, {'2': 'B'}, {'3': 'C'}])
    for category, count in (('1', 2), ('2', 4), ('3', 1)):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id=None,
                category_id=category,
                issues=[],
                user_id=None,
                principal=principal
            )
    assert collection.count_by_category() == [('A', 2), ('B', 4), ('C', 1)]

    assert collection.count_by_category() == \
        collection.for_state('drafted').count_by_category()


def test_notice_collection_count_by_user(session, principal):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_user() == []

    users = UserCollection(session)
    users.add('a@example.org', 'pw', 'editor')
    users.add('b@example.org', 'pw', 'editor')
    users.add('c@example.org', 'pw', 'admin')
    users.add('d@example.org', 'pw', 'publisher')
    users = {user.username: str(user.id) for user in users.query().all()}
    assert collection.count_by_user() == []

    for user, count in (
        ('a@example.org', 2),
        ('b@example.org', 4),
        ('c@example.org', 1),
        ('d@example.org', 1),
    ):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id='',
                category_id='',
                issues=[],
                user_id=users[user],
                principal=principal
            )
    assert sorted(collection.count_by_user()) == sorted([
        (users['a@example.org'], 2),
        (users['b@example.org'], 4),
        (users['c@example.org'], 1),
        (users['d@example.org'], 1),
    ])

    assert collection.count_by_user() == \
        collection.for_state('drafted').count_by_user()


def test_notice_collection_count_by_group(session, principal):
    collection = GazetteNoticeCollection(session)
    assert collection.count_by_group() == []

    groups = UserGroupCollection(session)
    groups.add(name='A')
    groups.add(name='C')
    groups.add(name='B')
    groups = {group.name: str(group.id) for group in groups.query().all()}
    assert collection.count_by_group() == [['A', 0], ['B', 0], ['C', 0]]

    users = UserCollection(session)
    users.add('a@example.org', 'pw', 'editor', data={'group': groups['A']})
    users.add('b@example.org', 'pw', 'editor', data={'group': groups['A']})
    users.add('c@example.org', 'pw', 'admin')
    users.add('d@example.org', 'pw', 'publisher')
    users.add('e@example.org', 'pw', 'publisher', data={'group': groups['B']})
    users.add('f@example.org', 'pw', 'publisher', data={})
    users.add('g@example.org', 'pw', 'publisher', data={'group': 'X'})
    users.add('h@example.org', 'pw', 'publisher', data={'group': None})
    users = {user.username: str(user.id) for user in users.query().all()}
    assert collection.count_by_group() == [['A', 0], ['B', 0], ['C', 0]]

    for user, count in (
        ('a@example.org', 2),
        ('b@example.org', 4),
        ('c@example.org', 1),
        ('d@example.org', 7),
        ('e@example.org', 2),
        ('f@example.org', 3),
        ('g@example.org', 6),
        ('h@example.org', 2),
    ):
        for x in range(count):
            collection.add(
                title='',
                text='',
                organization_id='',
                category_id='',
                issues=[],
                user_id=users[user],
                principal=principal
            )

    assert collection.count_by_group() == [
        ['', 19], ['A', 6], ['B', 2], ['C', 0]
    ]

    assert sum(x[1] for x in collection.count_by_group()) == \
        collection.query().count()

    assert collection.count_by_group() == \
        collection.for_state('drafted').count_by_group()
