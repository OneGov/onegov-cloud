from onegov.core.elements import Link
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.pas import _
from onegov.pas.collections import LegislativePeriodCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.collections import ParliamentaryGroupCollection
from onegov.pas.collections import PartyCollection
from onegov.user import Auth
from onegov.user import UserCollection


def get_global_tools(request):

    if request.is_logged_in:

        # Logout
        yield LinkGroup(
            request.current_username, classes=('user',),
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
                        _("Parlamentarians"),
                        request.class_link(ParliamentarianCollection),
                        attrs={'class': 'user'}  # todo:
                    ),
                    Link(
                        _("Legislative Periods"),
                        request.class_link(LegislativePeriodCollection),
                        attrs={'class': 'user'}  # todo:
                    ),
                    Link(
                        _("Parliamentary Groups"),
                        request.class_link(ParliamentaryGroupCollection),
                        attrs={'class': 'user'}  # todo:
                    ),
                    Link(
                        _("Parties"),
                        request.class_link(PartyCollection),
                        attrs={'class': 'user'}  # todo:
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


def get_top_navigation(request):
    return []
