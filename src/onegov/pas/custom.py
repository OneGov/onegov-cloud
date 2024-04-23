from onegov.core.elements import Link
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.pas import _
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import ChangeCollection
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.collections import SettlementRunCollection
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
                        _("Attendences"),
                        request.class_link(AttendenceCollection),
                        attrs={'class': 'attendences'}
                    ),
                    Link(
                        _("Settlement runs"),
                        request.class_link(SettlementRunCollection),
                        attrs={'class': 'settlement-runs'}
                    ),
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
                        _("Users"),
                        request.class_link(UserCollection),
                        attrs={'class': 'user'}
                    ),
                    Link(
                        _("PAS settings"),
                        request.link(request.app.org, 'pas-settings'),
                        attrs={'class': 'pas-settings'}
                    ),
                    Link(
                        _("More settings"),
                        request.link(request.app.org, 'settings'),
                        attrs={'class': 'settings'}
                    ),
                    Link(
                        _("Changes"),
                        request.class_link(ChangeCollection),
                        attrs={'class': 'changes'}
                    ),
                )
            )


def get_top_navigation(request: 'TownRequest') -> 'list[Link]':
    return []
