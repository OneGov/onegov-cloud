from __future__ import annotations

from functools import cached_property
from onegov.org.request import OrgRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.agency.app import AgencyApp


class AgencyRequest(OrgRequest):

    app: AgencyApp

    @cached_property
    def current_role(self) -> str | None:
        """ Onegov Agency allows to additionally elevate the member role to the
        editor role by defining group role mappings.

        """
        from onegov.agency.security import get_current_role
        return get_current_role(self.session, self.identity)
