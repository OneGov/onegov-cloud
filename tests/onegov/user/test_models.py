from freezegun import freeze_time
from onegov.user import User
from onegov.user import UserGroup
from unittest.mock import call
from unittest.mock import patch


class DummyBrowserSession():
    def __init__(self, token):
        self._token = token

    def flush(self):
        pass


class DummyRequest():
    def __init__(self, token):
        self.client_addr = '127.0.0.1'
        self.user_agent = 'Mozilla/5.0'
        self.browser_session = DummyBrowserSession(token)
        self.app = None


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


def test_user_save_session():
    user = User()
    assert not user.sessions

    with patch('onegov.user.models.user.remembered') as remembered:
        remembered.return_value = True

        with freeze_time('2016-09-01 12:00'):
            user.save_current_session(DummyRequest('xxx'))

        with freeze_time('2016-10-01 12:00'):
            user.save_current_session(DummyRequest('yyy'))

        assert user.sessions == {
            'xxx': {
                'address': '127.0.0.1',
                'timestamp': '2016-09-01T12:00:00',
                'agent': 'Mozilla/5.0'
            },
            'yyy': {
                'address': '127.0.0.1',
                'timestamp': '2016-10-01T12:00:00',
                'agent': 'Mozilla/5.0'
            }
        }


def test_user_remove_session():
    user = User()
    assert not user.sessions

    with patch('onegov.user.models.user.remembered') as remembered:
        remembered.return_value = True

        user.save_current_session(DummyRequest('xxx'))
        user.save_current_session(DummyRequest('yyy'))
        assert 'xxx' in user.sessions
        assert 'yyy' in user.sessions

        user.remove_current_session(DummyRequest('xxx'))
        assert 'xxx' not in user.sessions
        assert 'yyy' in user.sessions


def test_user_logout_all_sessions():
    user = User()
    assert not user.sessions

    with patch('onegov.user.models.user.remembered') as remembered:
        with patch('onegov.user.models.user.forget') as forget:
            remembered.return_value = True

            user.save_current_session(DummyRequest('xxx'))
            user.save_current_session(DummyRequest('yyy'))
            assert 'xxx' in user.sessions
            assert 'yyy' in user.sessions

            user.logout_all_sessions(DummyRequest('zzz'))
            assert call(None, 'xxx') in forget.mock_calls
            assert call(None, 'yyy') in forget.mock_calls


def test_user_cleanup_sessions():
    user = User()
    assert not user.sessions

    with patch('onegov.user.models.user.remembered') as remembered:
        with patch('onegov.user.models.user.forget'):
            # ... implicit
            remembered.return_value = True
            user.save_current_session(DummyRequest('xxx'))
            assert 'xxx' in user.sessions

            remembered.return_value = False
            user.cleanup_sessions(DummyRequest('zzz'))
            assert 'xxx' not in user.sessions

            # ... while adding
            remembered.return_value = True
            user.save_current_session(DummyRequest('xxx'))
            assert 'xxx' in user.sessions

            remembered.return_value = False
            user.save_current_session(DummyRequest('yyy'))
            assert 'xxx' not in user.sessions
            assert 'yyy' not in user.sessions

            # ... while removing
            remembered.return_value = True
            user.save_current_session(DummyRequest('xxx'))
            user.save_current_session(DummyRequest('yyy'))
            assert 'xxx' in user.sessions
            assert 'yyy' in user.sessions

            remembered.return_value = False
            user.remove_current_session(DummyRequest('xxx'))
            assert 'xxx' not in user.sessions
            assert 'yyy' not in user.sessions

            # ... while logging out
            remembered.return_value = True
            user.save_current_session(DummyRequest('xxx'))
            user.save_current_session(DummyRequest('yyy'))
            assert 'xxx' in user.sessions
            assert 'yyy' in user.sessions

            remembered.return_value = False
            user.logout_all_sessions(DummyRequest('zzz'))
            assert 'xxx' not in user.sessions
            assert 'yyy' not in user.sessions
