from __future__ import annotations

import logging
from datetime import date
from onegov.core.utils import toggle
from onegov.core.crypto import random_password
from onegov.parliament.collections import ParliamentarianCollection
from onegov.pas.models import PASParliamentarian
from onegov.user import UserCollection
from sqlalchemy.orm import selectinload

log = logging.getLogger('onegov.pas.collections.parliamentarian')


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Any, Self
    from onegov.core import Framework


class PASParliamentarianCollection(
    ParliamentarianCollection[PASParliamentarian]
):

    def __init__(self, app: Framework, **kwargs: Any) -> None:
        super().__init__(app.session(), **kwargs)
        self.app = app

    def for_filter(
        self,
        active: bool | None = None,
        party: str | None = None,
    ) -> Self:
        active_ = toggle(self.active, active)
        party_ = toggle(self.party, party)

        return self.__class__(
            self.app,
            active=active_,
            party=party_
        )

    @property
    def model_class(self) -> type[PASParliamentarian]:
        return PASParliamentarian

    def add(self, **kwargs: Any) -> PASParliamentarian:
        item = super().add(**kwargs)
        if item.zg_username:
            self.update_user(item, item.zg_username)
        self.session.flush()
        return item

    def delete(self, item: PASParliamentarian) -> None:
        self.update_user(item, None)
        self.session.delete(item)
        self.session.flush()

    def _is_current_commission_president(
        self,
        item: PASParliamentarian
    ) -> bool:
        """Check if the parliamentarian is currently a president of any
        commission."""
        today = date.today()
        return any(
            membership.role == 'president' and
            (membership.start is None or membership.start <= today) and
            (membership.end is None or membership.end >= today)
            for membership in item.commission_memberships
        )

    def _representatives_by_zg_username(
        self,
        parliamentarians: list[PASParliamentarian],
    ) -> dict[str, PASParliamentarian]:
        """Pick one parliamentarian per unique zg_username,
        prioritizing commission presidents."""

        by_username: dict[str, PASParliamentarian] = {}
        for parl in parliamentarians:
            if not parl.zg_username:
                continue
            key = parl.zg_username.lower()
            existing = by_username.get(key)
            if existing is None or (
                self._is_current_commission_president(parl)
                and not self._is_current_commission_president(existing)
            ):
                by_username[key] = parl
        return by_username

    def update_user(
        self,
        item: PASParliamentarian,
        new_username: str | None,
        users_cache: dict[str, Any] | None = None,
    ) -> None:
        """Keep the parliamentarian and its user account in sync.

        Uses zg_username as the User.username identifier.

        * Creates a new user if zg_username is set.
        * Disables user if zg_username has been removed.
        * Changes usernames if zg_username changed.
        * Ensures correct role and active state.

        Optional users_cache pre-fetches users to avoid
        N+1 queries.
        """

        old_username = item.zg_username
        users = UserCollection(self.session)

        if users_cache is not None:
            old_user = (
                users_cache.get(old_username.lower()) if old_username else None
            )
            new_user = (
                users_cache.get(new_username.lower()) if new_username else None
            )
        else:
            old_user = (
                users.by_username(old_username) if old_username else None
            )
            new_user = (
                users.by_username(new_username) if new_username else None
            )

        create = False
        enable = None
        disable = []

        if not new_username:
            disable.extend([old_user, new_user])
        else:
            if new_username == old_username:
                if not old_user:
                    create = True
                else:
                    enable = old_user
            else:
                if old_user and new_user:
                    disable.append(old_user)
                    enable = new_user
                elif not old_user and not new_user:
                    create = True
                else:
                    enable = old_user or new_user

        if create:
            assert new_username is not None
            role = (
                'commission_president'
                if self._is_current_commission_president(item)
                else 'parliamentarian'
            )
            log.info(f'Creating user {new_username} with role {role}')
            new_user_obj = users.add(
                new_username,
                random_password(16),
                role=role,
                realname=item.title,
                active=False,
            )
            if users_cache is not None:
                users_cache[new_username.lower()] = new_user_obj

        if enable:
            if enable.role == 'admin':
                return
            role = (
                'commission_president'
                if self._is_current_commission_president(item)
                else 'parliamentarian'
            )
            saml_sources = {'saml2', 'ldap'}
            corrections = {
                'username': new_username,
                'role': role,
                'active': True,
                **(
                    {}
                    if enable.source in saml_sources
                    else {
                        'source': None,
                        'source_id': None,
                    }
                ),
            }
            corrections = {
                attribute: value
                for attribute, value in corrections.items()
                if getattr(enable, attribute) != value
            }
            if corrections:
                log.info(
                    f'Correcting user {enable.username} to {corrections}'
                )
                for attribute, value in corrections.items():
                    setattr(enable, attribute, value)
                enable.logout_all_sessions(self.app)

        for user in disable:
            if user:
                log.info(f'Deactivating user {user.username}')
                user.active = False
                user.logout_all_sessions(self.app)

    def sync_user_accounts(self) -> dict[str, Any]:
        """Sync user accounts for all parliamentarians.

        Groups by zg_username, picks one representative per
        username to avoid role conflicts. Prioritizes
        commission presidents.

        Returns dict with 'synced', 'skipped', and
        'created' (list of new usernames).
        """

        parliamentarians = (
            self.query()
            .options(selectinload(self.model_class.commission_memberships))
            .all()
        )

        users_cache = {
            user.username.lower(): user
            for user in UserCollection(self.session).query()
        }

        representatives = self._representatives_by_zg_username(
            parliamentarians
        )

        synced = 0
        skipped = 0
        created: list[str] = []
        for parl in representatives.values():
            username = parl.zg_username
            assert username is not None

            is_new = username.lower() not in users_cache
            self.update_user(parl, username, users_cache)
            if is_new:
                created.append(username)
            synced += 1

        self.session.flush()
        return {
            'synced': synced,
            'skipped': skipped,
            'created': created,
        }
