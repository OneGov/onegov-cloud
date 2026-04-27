from __future__ import annotations

import logging
from datetime import date
from email_validator import EmailNotValidError, validate_email
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

    def _representatives_by_email(
        self,
        parliamentarians: list[PASParliamentarian],
    ) -> dict[str, PASParliamentarian]:
        """Pick one parliamentarian per unique email,
        prioritizing commission presidents."""

        by_email: dict[str, PASParliamentarian] = {}
        for parl in parliamentarians:
            if not parl.email_primary:
                continue
            key = parl.email_primary.lower()
            existing = by_email.get(key)
            if existing is None or (
                self._is_current_commission_president(parl)
                and not self._is_current_commission_president(existing)
            ):
                by_email[key] = parl
        return by_email

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
            # NOTE: Explicitly mark them as inactive *first*. Only in the SSO
            # login via on_ensure_user callback we finally set active to True.
            new_user_obj = users.add(
                new_email, random_password(16), role=role,
                realname=item.title,
                active=False,
            )
            if users_cache is not None:
                users_cache[new_email.lower()] = new_user_obj

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
                'username': new_email,
                'role': role,
                'active': True,
                **(
                    {}
                    if enable.source in saml_sources
                    else {'source': None, 'source_id': None}
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

        Groups by email, picks one representative per email
        to avoid role conflicts. Prioritizes commission
        presidents.

        Returns dict with 'synced', 'skipped', and
        'created' (list of new user emails).
        """

        parliamentarians = (
            self.query()
            .options(selectinload(self.model_class.commission_memberships))
            .all()
        )

        # We use username.lower() to avoid potential
        # onegov.user.errors.ExistingUserError
        users_cache = {
            user.username.lower(): user
            for user in UserCollection(self.session).query()
        }

        representatives = self._representatives_by_email(parliamentarians)

        synced = 0
        skipped = 0
        created: list[str] = []
        for parl in representatives.values():
            email = parl.email_primary
            assert email is not None
            try:
                validate_email(email, check_deliverability=False)
            except EmailNotValidError as e:
                log.warning(
                    f'Skipping {parl.title} '
                    f'with invalid email {email}: {e}'
                )
                skipped += 1
                continue

            is_new = email.lower() not in users_cache
            self.update_user(parl, email, users_cache)
            if is_new:
                created.append(email)
            synced += 1

        self.session.flush()
        return {
            'synced': synced,
            'skipped': skipped,
            'created': created,
        }
