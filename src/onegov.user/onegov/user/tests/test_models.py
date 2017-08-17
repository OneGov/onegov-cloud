from onegov.user import User
from onegov.user import UserGroup


def test_user_initials():
    user = User(username='admin')
    assert user.initials == 'A'

    user = User(username='nathan.drake@example.org')
    assert user.initials == 'ND'

    user = User(username='a.b.c.d.e.f')
    assert user.initials == 'AB'

    user = User(username='victor', realname='Victor Sullivan')
    assert user.initials == 'VS'

    user = User(username='burns', realname='Charles Montgomery Burns')
    assert user.initials == 'CB'


def test_user_title(session):
    user = User(username='admin')
    assert user.title == 'admin'

    user = User(username='nathan', realname="Nathan Drake")
    assert user.title == "Nathan Drake"


def test_user_group(session):
    session.add(User(username='nathan', password='pwd', role='editor'))
    session.add(UserGroup(name='group'))
    session.flush()
    user = session.query(User).one()
    group = session.query(UserGroup).one()

    assert user.group is None
    assert group.users.all() == []

    user.group = group
    assert group.users.one() == user
    assert user.group == group
    assert user.group_id == group.id
