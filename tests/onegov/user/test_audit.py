from unittest.mock import Mock
from uuid import uuid4

import pytest

from onegov.core.orm.audit import AuditEntry, register_audit_handlers
from onegov.user import (
    RoleMapping,
    User,
    UserCollection,
    UserGroupCollection,
)
from onegov.user.audit import register_user_auditing, USER_AUDIT_FIELDS
from onegov.user.auth.provider import ensure_user, RolesMapping
from sedate import utcnow


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.orm import SessionManager
    from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def audit_handlers(session_manager: SessionManager) -> Iterator[None]:
    register_user_auditing()
    register_audit_handlers(session_manager)
    with session_manager.set_current_user(None, 'admin@example.org'):
        yield


@pytest.mark.parametrize('bulk', [False, True])
def test_user_audit_lifecycle(
    session: Session,
    session_manager: SessionManager,
    bulk: bool,
) -> None:
    actor_id = uuid4().hex
    with session_manager.set_current_user(actor_id, 'admin@example.org'):
        users = UserCollection(session)
        user = users.add('michael@example.org', 'password', 'admin')
        session.flush()
        user_id = user.id
        query = session.query(User).filter_by(id=user_id)
        if bulk:
            query.update({'role': 'member', 'active': False})
            query.delete()
        else:
            user.role = 'member'
            user.active = False
            session.flush()
            users.delete(user.username)

    entries = session.query(AuditEntry).order_by(AuditEntry.created).all()
    assert [entry.operation for entry in entries] == [
        'insert',
        'update',
        'delete',
    ]
    assert all(entry.target_id == str(user_id) for entry in entries)
    assert all(entry.target_table == 'users' for entry in entries)
    assert all(entry.user_id == actor_id for entry in entries)
    assert all(entry.username == 'admin@example.org' for entry in entries)
    assert entries[1].previous_snapshot['role'] == 'admin'
    assert entries[1].snapshot['role'] == 'member'
    assert entries[1].previous_snapshot['active'] is True
    assert entries[1].snapshot['active'] is False
    assert entries[2].snapshot['username'] == 'michael@example.org'
    assert entries[2].snapshot['role'] == 'member'
    assert all(
        set(entry.snapshot) == set(USER_AUDIT_FIELDS) for entry in entries
    )


@pytest.mark.parametrize('expired', [False, True])
def test_user_audit_existing_user(
    session: Session,
    session_manager: SessionManager,
    expired: bool,
) -> None:
    user = UserCollection(session).add(
        'andrea@example.org', 'password', 'editor'
    )
    session.flush()
    session.query(AuditEntry).delete()
    if expired:
        session.expire(user)
    with session_manager.set_current_user(None, 'cli:operator'):
        user.role = 'member'
        user.source = 'msal'
        session.flush()

    entry = session.query(AuditEntry).one()
    assert entry.previous_snapshot['role'] == 'editor'
    assert entry.previous_snapshot['source'] is None
    assert entry.snapshot['role'] == 'member'
    assert entry.snapshot['source'] == 'msal'
    assert entry.username == 'cli:operator'
    assert entry.user_id is None


def test_user_audit_ignores_credentials_and_login(
    session: Session,
) -> None:
    user = UserCollection(session).add(
        'andrea@example.org', 'password', 'editor'
    )
    session.flush()
    user.password = 'new-password'
    user.last_login = utcnow()
    user.signup_token = 'secret-token'
    user.second_factor = {'type': 'totp', 'data': 'secret'}
    session.flush()
    session.query(User).filter_by(id=user.id).update({'last_login': utcnow()})

    entry = session.query(AuditEntry).one()
    assert entry.operation == 'insert'
    assert set(entry.snapshot) == set(USER_AUDIT_FIELDS)


def test_user_audit_bulk_delete_without_previous_entry(
    session: Session,
) -> None:
    user = UserCollection(session).add(
        'andrea@example.org',
        'password',
        'editor',
        signup_token='secret-token',
        second_factor={'type': 'totp', 'data': 'secret'},
    )
    session.flush()
    session.query(AuditEntry).delete()
    session.query(User).filter_by(id=user.id).delete()

    entry = session.query(AuditEntry).one()
    assert entry.operation == 'delete'
    assert set(entry.snapshot) == set(USER_AUDIT_FIELDS)
    assert entry.snapshot['username'] == 'andrea@example.org'


def test_user_audit_without_identity(
    session: Session,
    session_manager: SessionManager,
) -> None:
    with session_manager.set_current_user(None, None):
        users = UserCollection(session)
        user = users.add('anonymous@example.org', 'password', 'admin')
        user.role = 'member'
        session.flush()
        users.delete(user.username)

    entries = session.query(AuditEntry).order_by(AuditEntry.created).all()
    assert [entry.operation for entry in entries] == [
        'insert',
        'update',
        'delete',
    ]
    assert all(entry.username == 'unknown' for entry in entries)
    assert all(entry.user_id is None for entry in entries)
    assert entries[1].previous_snapshot['role'] == 'admin'
    assert entries[1].snapshot['role'] == 'member'


def test_provider_role_change_audit(
    session: Session,
    session_manager: SessionManager,
) -> None:
    user = UserCollection(session).add(
        'michael@example.org', 'password', 'admin'
    )
    request = Mock(session=session)
    request.app.session_manager = session_manager
    request.app.settings.user.ensure_user_callback.return_value = True
    request.app.settings.user.change_username_roles = ()
    role = RolesMapping({}).match({'members': 'staff'}, ['staff'])
    assert role == 'member'

    with session_manager.set_current_user(None, None):
        result = ensure_user(
            request,
            source='ldap',
            source_id='external-id',
            username=user.username,
            role=role,
        )
        assert result is user
        assert session_manager.current_username is None
        entry = session.query(AuditEntry).filter_by(operation='update').one()
        assert entry.username == 'unknown'
        assert entry.user_id is None
        assert entry.previous_snapshot['role'] == 'admin'
        assert entry.snapshot['role'] == 'member'
        assert entry.snapshot['source'] == 'ldap'

        user.active = False
        session.flush()
        latest = (
            session.query(AuditEntry)
            .order_by(AuditEntry.created.desc())
            .first()
        )
        assert latest is not None
        assert latest.username == 'unknown'


def test_group_membership_audit(
    session: Session,
    session_manager: SessionManager,
) -> None:
    user = UserCollection(session).add(
        'member@example.org', 'password', 'member'
    )
    group = UserGroupCollection(session).add(name='Editors')
    session.flush()
    session.query(AuditEntry).filter_by(target_table='groups').delete()

    with session_manager.set_current_user(None, None):
        group.users = [user]
        session.flush()
        user.groups.remove(group)
        session.flush()
        user.groups.append(group)
        session.flush()
        session.delete(group)
        session.flush()

    entries = (
        session.query(AuditEntry)
        .filter_by(target_table='groups')
        .order_by(AuditEntry.created)
        .all()
    )
    assert [entry.operation for entry in entries] == [
        'update',
        'update',
        'update',
        'delete',
    ]
    assert entries[0].previous_snapshot['user_ids'] == []
    assert entries[0].snapshot['user_ids'] == [str(user.id)]
    assert entries[1].previous_snapshot['user_ids'] == [str(user.id)]
    assert entries[1].snapshot['user_ids'] == []
    assert entries[2].snapshot['user_ids'] == [str(user.id)]
    assert entries[3].snapshot['user_ids'] == [str(user.id)]
    assert all(entry.username == 'unknown' for entry in entries)


def test_role_mapping_audit(
    session: Session,
    session_manager: SessionManager,
) -> None:
    user = UserCollection(session).add(
        'member@example.org', 'password', 'member'
    )
    group = UserGroupCollection(session).add(name='Editors')
    session.flush()
    with session_manager.set_current_user(None, None):
        mapping = RoleMapping(
            username=user.username,
            role='editor',
            content_type='pages',
            content_id='42',
        )
        session.add(mapping)
        session.flush()
        mapping.role = 'member'
        mapping.username = None
        mapping.group_id = group.id
        session.flush()
        session.query(RoleMapping).filter_by(id=mapping.id).delete()

    entries = (
        session.query(AuditEntry)
        .filter_by(target_table='role_mappings')
        .order_by(AuditEntry.created)
        .all()
    )
    assert [entry.operation for entry in entries] == [
        'insert',
        'update',
        'delete',
    ]
    assert entries[1].previous_snapshot['role'] == 'editor'
    assert entries[1].previous_snapshot['username'] == user.username
    assert entries[1].snapshot['role'] == 'member'
    assert entries[1].snapshot['username'] is None
    assert entries[1].snapshot['group_id'] == str(group.id)
    assert entries[2].snapshot == entries[1].snapshot
    assert entries[2].snapshot['content_id'] == '42'
    assert all(entry.username == 'unknown' for entry in entries)
