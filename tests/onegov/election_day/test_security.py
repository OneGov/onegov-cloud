from __future__ import annotations

from morepath import Identity
from morepath.authentication import NoIdentity
from onegov.election_day.security import MaybePublic
from onegov.user.models import User


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestApp


def test_security_permissions(election_day_app_zg: TestApp) -> None:
    session = election_day_app_zg.session()

    # Remove existing users
    session.query(User).delete()

    # Add one user per role
    users = {}
    for role in ('admin', 'editor', 'member', 'anonymous'):
        user = User(
            realname=role,
            username=f'{role}@example.org',
            password_hash='hash',
            role=role,
            groups=[]
        )
        session.add(user)
        users[role] = user

    def permits(user: User | None, model: object, permission: object) -> bool:
        identity: Identity | NoIdentity = NoIdentity()
        if user:
            identity = Identity(
                uid='',
                userid=user.username,
                groupids=frozenset(group.id.hex for group in user.groups),
                role=user.role,
                application_id=election_day_app_zg.application_id
            )
        return election_day_app_zg._permits(identity, model, permission)

    model = election_day_app_zg.principal
    assert permits(users['admin'], model, MaybePublic)
    assert permits(users['editor'], model, MaybePublic)
    assert permits(users['member'], model, MaybePublic)
    assert permits(users['anonymous'], model, MaybePublic)
    assert permits(users['anonymous'], model, MaybePublic)
    assert permits(None, model, MaybePublic)

    principal = election_day_app_zg.principal
    principal.private = True
    principal.reply_to = 'reply-to@example.org'
    election_day_app_zg.cache.set('principal', principal)

    assert permits(users['admin'], model, MaybePublic)
    assert permits(users['editor'], model, MaybePublic)
    assert not permits(users['member'], model, MaybePublic)
    assert not permits(users['anonymous'], model, MaybePublic)
    assert not permits(None, model, MaybePublic)
