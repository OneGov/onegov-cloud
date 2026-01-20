from __future__ import annotations

from onegov.core.security import Private
from onegov.core.security import Public
from onegov.core.security.permissions import Intent
from onegov.core.security.rules import has_permission_logged_in
from onegov.core.security.rules import has_permission_not_logged_in
from onegov.election_day import ElectionDayApp

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity


class MaybePublic(Intent):
    """ The general public is allowed to do this, if not otherwise defined
    in the principal. """


@ElectionDayApp.permission_rule(
    model=object,
    permission=MaybePublic,
    identity=None
)
def has_permission_maybe_public_not_logged_in(
    app: ElectionDayApp,
    identity: None,
    model: object,
    permission: object
) -> bool:

    if getattr(app.principal, 'private', False):
        return has_permission_not_logged_in(app, identity, model, Private)

    return has_permission_not_logged_in(app, identity, model, Public)


@ElectionDayApp.permission_rule(
    model=object,
    permission=MaybePublic
)
def has_permission_maybe_public_logged_in(
    app: ElectionDayApp,
    identity: Identity,
    model: object,
    permission: MaybePublic
) -> bool:

    if getattr(app.principal, 'private', False):
        return has_permission_logged_in(app, identity, model, Private)

    return has_permission_logged_in(app, identity, model, Public)
