import pytest

from onegov.user import UserCollection
from onegov.user.errors import UnknownUserError


def test_user_add(session):

    users = UserCollection(session)
    user = users.add('dmr@example.org', 'p@ssw0rd', 'root')

    assert users.by_username(user.username).username == 'dmr@example.org'


def test_user_exists(session):

    users = UserCollection(session)

    assert not users.exists('dmr@example.org')
    users.add('dmr@example.org', 'p@ssw0rd', 'root')
    assert users.exists('dmr@example.org')


def test_user_data(session):

    users = UserCollection(session)

    user = users.add('dmr@example.org', 'p@ssw0rd', 'root', data={
        'firstname': 'Dennis',
        'lastname': 'Ritchie'
    })

    assert user.data['firstname'] == 'Dennis'
    assert user.data['lastname'] == 'Ritchie'


def test_user_delete(session):

    users = UserCollection(session)
    users.add('dmr@example.org', 'p@ssw0rd', 'root')

    assert users.exists('dmr@example.org')
    users.delete('dmr@example.org')
    assert not users.exists('dmr@example.org')

    with pytest.raises(UnknownUserError):
        users.delete('dmr@example.org')


def test_user_password(session):

    users = UserCollection(session)
    user = users.add('AzureDiamond', 'hunter2', 'irc-user')
    assert user.password.startswith('$bcrypt-sha256$2a')
    assert user.password_hash.startswith('$bcrypt-sha256$2a')

    def may_login(username, password):
        return bool(users.by_username_and_password(username, password))

    assert may_login('AzureDiamond', 'hunter2')
    assert not may_login('AzureDiamond', 'hunter3')
    assert not may_login('AzureDiamon', 'hunter2')

    user.password = 'test'
    assert user.password.startswith('$bcrypt-sha256$2a')
    assert user.password_hash.startswith('$bcrypt-sha256$2a')
    assert may_login('AzureDiamond', 'test')

    # this is an exception, we allow for empty passwords, but we will not
    # query for them by default, see usercollection class
    user.password = ''
    assert user.password.startswith('$bcrypt-sha256$2a')
    assert user.password_hash.startswith('$bcrypt-sha256$2a')
    assert not may_login('AzureDiamon', '')
