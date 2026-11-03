from onegov.core.orm.audit import register_audit_model
from onegov.user.models import RoleMapping, User, UserGroup
from onegov.user.models.group import group_association_table
from sqlalchemy import inspect, select
from sqlalchemy.orm import object_session


from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


USER_AUDIT_FIELDS: tuple[str, ...] = (
    'username',
    'realname',
    'role',
    'active',
    'source',
    'source_id',
)


ROLE_MAPPING_AUDIT_FIELDS: tuple[str, ...] = (
    'role',
    'username',
    'group_id',
    'content_type',
    'content_id',
)


def user_snapshot(user: User) -> dict[str, Any]:
    return {field: getattr(user, field) for field in USER_AUDIT_FIELDS}


def user_previous_snapshot(
    _session: Session,
    user: User,
) -> dict[str, Any] | None:
    state = inspect(user)
    if not any(
        state.attrs[field].history.has_changes() for field in USER_AUDIT_FIELDS
    ):
        return None

    data: dict[str, Any] = {}
    for field in USER_AUDIT_FIELDS:
        history = state.attrs[field].history
        if history.deleted:
            data[field] = history.deleted[0]
        elif history.added:
            data[field] = None
        else:
            data[field] = getattr(user, field)
    return data


def user_changed(_session: Session, user: User) -> bool:
    state = inspect(user)
    return any(
        state.attrs[field].history.has_changes() for field in USER_AUDIT_FIELDS
    )


def group_snapshot(group: UserGroup) -> dict[str, Any]:
    session = object_session(group)
    assert session is not None
    user_ids = session.scalars(
        select(group_association_table.c.user_id).where(
            group_association_table.c.group_id == group.id
        )
    )
    return {
        'name': group.name,
        'user_ids': sorted(str(user_id) for user_id in user_ids),
    }


def group_previous_snapshot(
    _session: Session,
    group: UserGroup,
) -> dict[str, Any] | None:
    state = inspect(group)
    names = state.attrs.name.history
    members = state.attrs.users.history
    if not names.has_changes() and not members.has_changes():
        return None
    user_ids = set(group_snapshot(group)['user_ids'])
    user_ids.difference_update(str(user.id) for user in members.added)
    user_ids.update(str(user.id) for user in members.deleted)
    return {
        'name': names.deleted[0] if names.deleted else group.name,
        'user_ids': sorted(user_ids),
    }


def group_changed(_session: Session, group: UserGroup) -> bool:
    state = inspect(group)
    return (
        state.attrs.name.history.has_changes()
        or state.attrs.users.history.has_changes()
    )


def group_delete_snapshot(
    _session: Session,
    group: UserGroup,
) -> dict[str, Any]:
    return group_snapshot(group)


def role_mapping_snapshot(mapping: RoleMapping) -> dict[str, Any]:
    data = {
        field: getattr(mapping, field) for field in ROLE_MAPPING_AUDIT_FIELDS
    }
    if data['group_id'] is not None:
        data['group_id'] = str(data['group_id'])
    return data


def role_mapping_previous_snapshot(
    _session: Session,
    mapping: RoleMapping,
) -> dict[str, Any] | None:
    state = inspect(mapping)
    data: dict[str, Any] = {}
    changed = False
    for field in ROLE_MAPPING_AUDIT_FIELDS:
        history = state.attrs[field].history
        changed |= history.has_changes()
        if history.deleted:
            data[field] = history.deleted[0]
        elif history.added:
            data[field] = None
        else:
            data[field] = getattr(mapping, field)
    if data['group_id'] is not None:
        data['group_id'] = str(data['group_id'])
    return data if changed else None


def role_mapping_changed(_session: Session, mapping: RoleMapping) -> bool:
    state = inspect(mapping)
    return any(
        state.attrs[field].history.has_changes()
        for field in ROLE_MAPPING_AUDIT_FIELDS
    )


def register_user_auditing() -> None:
    register_audit_model(
        User,
        snapshot=user_snapshot,
        previous_snapshot=user_previous_snapshot,
        changed=user_changed,
    )
    register_audit_model(
        UserGroup,
        snapshot=group_snapshot,
        previous_snapshot=group_previous_snapshot,
        changed=group_changed,
        delete_snapshot=group_delete_snapshot,
        capture_before_delete=True,
    )
    register_audit_model(
        RoleMapping,
        snapshot=role_mapping_snapshot,
        previous_snapshot=role_mapping_previous_snapshot,
        changed=role_mapping_changed,
    )
