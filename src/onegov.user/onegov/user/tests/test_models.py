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


def test_polymorphism_user(session):

    class MyUser(User):
        __mapper_args__ = {'polymorphic_identity': 'my'}

    class MyOtherUser(User):
        __mapper_args__ = {'polymorphic_identity': 'other'}

    session.add(User(username='default', password='pwd', role='editor'))
    session.add(MyUser(username='my', password='pwd', role='editor'))
    session.add(MyOtherUser(username='other', password='pwd', role='editor'))
    session.flush()

    assert session.query(User).count() == 3
    assert session.query(MyUser).one().username == 'my'
    assert session.query(MyOtherUser).one().username == 'other'


def test_polymorphism_group(session):

    class MyGroup(UserGroup):
        __mapper_args__ = {'polymorphic_identity': 'my'}

    class MyOtherGroup(UserGroup):
        __mapper_args__ = {'polymorphic_identity': 'other'}

    session.add(UserGroup(name='original'))
    session.add(MyGroup(name='my'))
    session.add(MyOtherGroup(name='other'))
    session.flush()

    assert session.query(UserGroup).count() == 3
    assert session.query(MyGroup).one().name == 'my'
    assert session.query(MyOtherGroup).one().name == 'other'
