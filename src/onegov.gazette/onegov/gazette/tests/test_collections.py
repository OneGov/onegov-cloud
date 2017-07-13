from onegov.gazette.collections import UserGroupCollection
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.user import UserCollection


def test_user_group_collection(session):
    collection = UserGroupCollection(session)
    collection.add(name='A')
    collection.add(name='C')
    collection.add(name='B')
    assert [group.name for group in collection.query()] == ['A', 'B', 'C']


def test_notice_collection(session):
    user = UserCollection(session).add(
        username='a@a.a', password='a', role='admin'
    )

    collection = GazetteNoticeCollection(session)
    collection.add(
        title='Notice A',
        text='An <strong>important</strong> Notice!',
        category='important',
        issues=['2017-1', '2017-4'],
        user_id=user.id
    )
    collection.add(
        title='Notice B',
        text='Another Notice',
        category='not so important',
        issues={'2017-2', '2017-4'},
        user_id=user.id
    )

    notice = collection.query().filter_by(title='Notice A').one()
    assert notice.title == 'Notice A'
    assert notice.text == 'An <strong>important</strong> Notice!'
    assert notice.category == 'important'
    assert notice.issues == {'2017-1': None, '2017-4': None}
    assert notice.user == user
    assert notice.changes.one().text == 'created'
    assert notice.changes.one().user == user

    notice = collection.query().filter_by(title='Notice B').one()
    assert notice.title == 'Notice B'
    assert notice.text == 'Another Notice'
    assert notice.category == 'not so important'
    assert notice.issues == {'2017-2': None, '2017-4': None}
    assert notice.user == user
    assert notice.changes.one().text == 'created'
    assert notice.changes.one().user == user
