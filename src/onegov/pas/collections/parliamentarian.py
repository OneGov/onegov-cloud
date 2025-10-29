from __future__ import annotations

import logging
from datetime import date
from onegov.core.utils import toggle
from onegov.core.crypto import random_password
from onegov.parliament.collections import ParliamentarianCollection
from onegov.pas.models import PASParliamentarian
from onegov.user import UserCollection

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
        if not item.email_primary:
            log.warning(
                f'Creating parliamentarian {item.title} without'
                'email_primary. This will prevent user account'
                'creation and may cause permission-related failures.'
            )
        self.update_user(item, item.email_primary)
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

    def update_user(
        self,
        item: PASParliamentarian,
        new_email: str | None,
        users_cache: dict[str, Any] | None = None,
    ) -> None:
        """Keep the parliamentarian and its user account in sync.

        * Creates a new user account if an email address is set (if not already
          existing).
        * Disable user accounts if an email has been deleted.
        * Change usernames if an email has changed.
        * Make sure used user accounts have the right role.
        * Make sure used user accounts are activated.
        * Make sure the password is changed if activated or disabled.

         Optional users_cache parameter allows to pre-fetch the users to avoid
         N+1 queries.

        """

        old_email = item.email_primary
        users = UserCollection(self.session)

        if users_cache is not None:
            old_user = (
                users_cache.get(old_email.lower()) if old_email
                else None
            )
            new_user = (
                users_cache.get(new_email.lower()) if new_email
                else None
            )
        else:
            old_user = users.by_username(old_email) if old_email else None
            new_user = users.by_username(new_email) if new_email else None

        create = False
        enable = None
        disable = []

        if not new_email:
            # email has been unset: disable obsolete users
            disable.extend([old_user, new_user])
        else:
            if new_email == old_email:
                # email has not changed, old_user == new_user
                if not old_user:
                    create = True
                else:
                    enable = old_user
            else:
                # email has changed: ensure user exist
                if old_user and new_user:
                    disable.append(old_user)
                    enable = new_user
                elif not old_user and not new_user:
                    create = True
                else:
                    enable = old_user if old_user else new_user

        if create:
            assert new_email is not None
            role = (
                'commission_president'
                 if self._is_current_commission_president(item)
                 else 'parliamentarian'
            )
            log.info(f'Creating user {new_email} with role {role}')
            new_user_obj = users.add(
                new_email, random_password(16), role=role,
                realname=item.title
            )
            if users_cache is not None:
                users_cache[new_email.lower()] = new_user_obj

        if enable:
            role = (
                'commission_president'
                if self._is_current_commission_president(item)
                else 'parliamentarian'
            )
            corrections = {
                'username': new_email,
                'role': role,
                'active': True,
                'source': None,
                'source_id': None
            }
            corrections = {
                attribute: value for attribute, value in corrections.items()
                if getattr(enable, attribute) != value
            }
            if corrections:
                log.info('Correcting user'
                    f' {enable.username} to {corrections}')
                for attribute, value in corrections.items():
                    setattr(enable, attribute, value)
                enable.logout_all_sessions(self.app)

        for user in disable:
            if user:
                log.info(f'Deactivating user {user.username}')
                user.active = False
                user.logout_all_sessions(self.app)
