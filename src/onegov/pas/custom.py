from onegov.core.elements import Link
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.pas import _
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.collections import ParliamentaryGroupCollection
from onegov.pas.collections import PartyCollection
from onegov.user import Auth
from onegov.user import UserCollection

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.town6.request import TownRequest


def get_global_tools(request: 'TownRequest') -> 'Iterator[Link | LinkGroup]':

    if request.is_logged_in:

        # Logout
        yield LinkGroup(
            request.current_username or _('User'),
            classes=('user',),
            links=(
                Link(
                    _("Logout"), request.link(
                        Auth.from_request(
                            request, to=logout_path(request)), name='logout'
                    ),
                    attrs={'class': 'logout'}
                ),
            )
        )

        # Management Dropdown
        if request.is_admin:
            yield LinkGroup(
                _("Management"), classes=('management',),
                links=(
                    Link(
                        _("Parliamentarians"),
                        request.class_link(ParliamentarianCollection),
                        attrs={'class': 'parliamentarians'}
                    ),
                    Link(
                        _("Commissions"),
                        request.class_link(CommissionCollection),
                        attrs={'class': 'commissions'}
                    ),
                    Link(
                        _("Legislative periods"),
                        request.class_link(LegislativePeriodCollection),
                        attrs={'class': 'legislative-periods'}
                    ),
                    Link(
                        _("Parliamentary groups"),
                        request.class_link(ParliamentaryGroupCollection),
                        attrs={'class': 'parliamentary-groups'}
                    ),
                    Link(
                        _("Parties"),
                        request.class_link(PartyCollection),
                        attrs={'class': 'parties'}
                    ),
                    Link(
                        _("Users"),
                        request.class_link(UserCollection),
                        attrs={'class': 'user'}
                    ),
                    Link(
                        _("Settings"),
                        request.link(request.app.org, 'settings'),
                        attrs={'class': 'settings'}
                    ),
                )
            )


def get_top_navigation(request: 'TownRequest') -> 'list[Link]':
    return []
