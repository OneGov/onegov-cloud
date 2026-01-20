from __future__ import annotations

from functools import cached_property
from onegov.town6.request import TownRequest


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.app import FeriennetApp


class FeriennetRequest(TownRequest):

    app: FeriennetApp

    @cached_property
    def is_organiser(self) -> bool:
        """ Returns true if the current user is an organiser or better.

        """

        return self.has_role('admin', 'editor')

    @cached_property
    def is_organiser_only(self) -> bool:
        """ Returns true if the current user is an organiser, but not an admin.

        """

        return self.is_editor

    @cached_property
    def is_manager(self) -> bool:
        """ Using feriennet only admins are managers. The editors are
        organisers with a very limited set of capabilities.

        """

        return self.is_admin

    @cached_property
    def is_admin(self) -> bool:
        """ Returns true if the current user is an admin. """

        return self.has_role('admin')
