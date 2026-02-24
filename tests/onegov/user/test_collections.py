from __future__ import annotations

import pytest

from onegov.core.crypto import RANDOM_TOKEN_LENGTH
from onegov.user.collections import UserCollection
from onegov.user.collections import UserGroupCollection
from onegov.user.errors import (
    AlreadyActivatedError,
    ExistingUserError,
    InsecurePasswordError,
    InvalidActivationTokenError,
    UnknownUserError,
)


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_user_add(session: Session) -> None:

    users = UserCollection(session)
    user = users.add('dmr@example.org', 'p@ssw0rd', 'root')

    assert users.by_username(user.username).username == 'dmr@example.org'  # type: ignore[union-attr]

    groups = UserGroupCollection(session)
    group = groups.add(name='group')

    user = users.add('abc@example.org', 'p@ssw0rd', 'root', groups=[group])
    user_groups = users.by_username(user.username).groups  # type: ignore[union-attr]
    assert len(user_groups) == 1
    assert user_groups[0].name == 'group'


def test_user_add_conflict(session: Session) -> None:

    users = UserCollection(session)
    users.add('dmr@example.org', 'p@ssw0rd', 'root')

    with pytest.raises(ExistingUserError):
        users.add('dmr@example.org', 'p@ssw0rd', 'root')


def test_user_exists(session: Session) -> None:

    users = UserCollection(session)

    assert not users.exists('dmr@example.org')
    users.add('dmr@example.org', 'p@ssw0rd', 'root')
    assert users.exists('dmr@example.org')


def test_user_by_yubikey(session: Session) -> None:

    users = UserCollection(session)
    users.add('dmr@example.org', 'p@ssw0rd', 'root', second_factor={
        'type': 'yubikey',
        'data': 'cccccccdefgh'
    })

    assert users.by_yubikey('cccccccdefgh')


def test_set_yubikey(session: Session) -> None:
    users = UserCollection(session)
    user = users.add('dmr@example.org', 'p@ssw0rd', 'root')

    with pytest.raises(AssertionError):
        user.yubikey = 'xxx'


def test_user_data(session: Session) -> None:

    users = UserCollection(session)

    user = users.add('dmr@example.org', 'p@ssw0rd', 'root', data={
        'firstname': 'Dennis',
        'lastname': 'Ritchie'
    })

    assert user.data['firstname'] == 'Dennis'
    assert user.data['lastname'] == 'Ritchie'


def test_user_delete(session: Session) -> None:

    users = UserCollection(session)
    users.add('dmr@example.org', 'p@ssw0rd', 'root')

    assert users.exists('dmr@example.org')
    users.delete('dmr@example.org')
    assert not users.exists('dmr@example.org')

    with pytest.raises(UnknownUserError):
        users.delete('dmr@example.org')


def test_user_password(session: Session) -> None:

    users = UserCollection(session)
    hash_start = '$bcrypt-sha256$v=2'
    user = users.add('AzureDiamond', 'hunter2', 'irc-user')
    assert user.password.startswith(hash_start)
    assert user.password_hash.startswith(hash_start)

    def may_login(username: str, password: str) -> bool:
        return bool(users.by_username_and_password(username, password))

    assert may_login('AzureDiamond', 'hunter2')
    assert not may_login('AzureDiamond', 'hunter3')
    assert not may_login('AzureDiamon', 'hunter2')

    user.password = 'test'
    assert user.password.startswith(hash_start)
    assert user.password_hash.startswith(hash_start)
    assert may_login('AzureDiamond', 'test')

    # this is an exception, we allow for empty passwords, but we will not
    # query for them by default, see usercollection class
    user.password = ''
    assert user.password.startswith(hash_start)
    assert user.password_hash.startswith(hash_start)
    assert not may_login('AzureDiamon', '')


def test_register_user(session: Session) -> None:

    users = UserCollection(session)

    class MockRequest:
        client_addr = '127.0.0.1'

    request: Any = MockRequest()

    with pytest.raises(AssertionError):
        users.register(None, None, request)  # type: ignore[arg-type]

    with pytest.raises(InsecurePasswordError):
        users.register('user', 'short', request)

    user = users.register('user', 'p@ssw0rd12', request)
    token = user.data['activation_token']

    assert len(token) == RANDOM_TOKEN_LENGTH
    assert not user.active
    assert user.role == 'member'

    with pytest.raises(UnknownUserError):
        users.activate_with_token('waldo', 'asdf')

    with pytest.raises(InvalidActivationTokenError):
        users.activate_with_token('user', 'asdf')

    users.activate_with_token('user', token)
    # undo mypy narrowing of user.active
    user2 = user
    assert user2.active
    assert 'activation_token' not in user.data

    with pytest.raises(ExistingUserError):
        user = users.register('user', 'p@ssw0rd12', request)

    with pytest.raises(AlreadyActivatedError):
        users.activate_with_token('user', token)


def test_user_by_role(session: Session) -> None:

    users = UserCollection(session)

    assert users.by_roles('admin', 'member').count() == 0

    users.add('admin@example.org', 'p@ssw0rd', role='admin')
    users.add('member@example.org', 'p@ssw0rd', role='member')

    assert users.by_roles('admin', 'member').count() == 2
    assert users.by_roles('admin').count() == 1
    assert users.by_roles('member').count() == 1


def test_user_lowercase(session: Session) -> None:

    users = UserCollection(session)
    users.add('Admin@Foo.Bar', 'p@ssw0rd', role='admin')

    assert users.by_username('Admin@Foo.Bar').username == 'admin@foo.bar'  # type: ignore[union-attr]
    assert users.by_username('admin@foo.bar').username == 'admin@foo.bar'  # type: ignore[union-attr]

    with pytest.raises(ExistingUserError) as e:
        users.add('admin@foo.Bar', 'p@ssw0rd', role='admin')

    assert e.value.message == 'admin@foo.Bar'


def test_user_sources(session: Session) -> None:
    users = UserCollection(session)

    assert users.sources == tuple()

    users.add('a@foo.bar', 'password', role='member').source = 'ldap'
    users.add('b@foo.bar', 'password', role='member').source = 'ldap'
    users.add('c@foo.bar', 'password', role='member').source = 'msal'
    users.add('d@foo.bar', 'password', role='member')

    assert users.sources == ('ldap', 'msal')

    assert UserCollection(session, source={'ldap'}).query().count() == 2
    assert UserCollection(session, source={'ldap', ''}).query().count() == 3


def test_user_group(session: Session) -> None:
    groups = UserGroupCollection(session)

    groups.add(name='group y')
    groups.add(name='group x')
    assert [group.name for group in groups.query().all()] == [
        'group x', 'group y'
    ]
