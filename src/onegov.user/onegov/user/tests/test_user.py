from onegov.user import User


def test_user_initials():
    user = User(username='admin')
    assert user.initials == 'A'

    user = User(username='nathan.drake@example.org')
    assert user.initials == 'ND'

    user = User(username='a.b.c.d.e.f')
    assert user.initials == 'AB'


def test_user_title():
    user = User(username='admin')
    assert user.title == 'Admin'

    user = User(username='nathan.drake@example.org')
    assert user.title == 'Nathan Drake'

    user = User(username='a.b.c.d.e.f')
    assert user.title == 'A B'
