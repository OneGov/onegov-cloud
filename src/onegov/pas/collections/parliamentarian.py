from __future__ import annotations

from onegov.core.utils import toggle
from onegov.core.crypto import random_password
from onegov.parliament.collections import ParliamentarianCollection
from onegov.pas.models import PASParliamentarian
from onegov.pas import log
from onegov.user import UserCollection


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
        self.update_user(item, item.email_primary)
        self.session.flush()
        return item

    def delete(self, item: PASParliamentarian) -> None:
        self.update_user(item, None)
        self.session.delete(item)
        self.session.flush()

    def update_user(
        self,
        item: PASParliamentarian,
        new_email: str | None
    ) -> None:
        """ Keep the parliamentarian and its user account in sync.

        * Creates a new user account if an email address is set (if not already
          existing).
        * Disable user accounts if an email has been deleted.
        * Change usernames if an email has changed.
        * Make sure used user accounts have the right role.
        * Make sure used user accounts are activated.
        * Make sure the password is changed if activated or disabled.

        """

        old_email = item.email_primary
        users = UserCollection(self.session)
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
            log.info(f'Creating user {new_email}')
            users.add(
                new_email, random_password(16), role='parliamentarian',
                realname=item.title
            )

        if enable:
            corrections = {
                'username': new_email,
                'role': 'parliamentarian',
                'active': True,
                'source': None,
                'source_id': None
            }
            corrections = {
                attribute: value for attribute, value in corrections.items()
                if getattr(enable, attribute) != value
            }
            if corrections:
                log.info(f'Correcting user {enable.username} to {corrections}')
                for attribute, value in corrections.items():
                    setattr(enable, attribute, value)
                enable.logout_all_sessions(self.app)

        for user in disable:
            if user:
                log.info(f'Deactivating user {user.username}')
                user.active = False
                user.logout_all_sessions(self.app)
