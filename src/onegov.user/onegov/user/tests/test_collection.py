import pytest

from onegov.core.crypto import RANDOM_TOKEN_LENGTH
from onegov.user import UserCollection
from onegov.user.errors import (
    AlreadyActivatedError,
    ExistingUserError,
    InsecurePasswordError,
    InvalidActivationTokenError,
    UnknownUserError,
)


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


def test_register_user(session):

    users = UserCollection(session)

    with pytest.raises(AssertionError):
        users.register(None, None)

    with pytest.raises(InsecurePasswordError):
        users.register('user', 'short')

    user = users.register('user', 'p@ssw0rd')
    token = user.data['activation_token']

    assert len(token) == RANDOM_TOKEN_LENGTH
    assert not user.active
    assert user.role == 'member'

    with pytest.raises(UnknownUserError):
        users.activate_with_token('waldo', 'asdf')

    with pytest.raises(InvalidActivationTokenError):
        users.activate_with_token('user', 'asdf')

    users.activate_with_token('user', token)
    assert user.active
    assert 'activation_token' not in user.data

    with pytest.raises(ExistingUserError):
        user = users.register('user', 'p@ssw0rd')

    with pytest.raises(AlreadyActivatedError):
        users.activate_with_token('user', token)
