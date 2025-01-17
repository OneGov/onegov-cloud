from __future__ import annotations

from onegov.chat import TextModuleCollection
from onegov.core.elements import Link
from onegov.core.utils import Bunch
from onegov.landsgemeinde import _
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.org.models import GeneralFileCollection
from onegov.org.models import ImageFileCollection
from onegov.people import PersonCollection
from onegov.town6.layout import DefaultLayout
from onegov.user import Auth
from onegov.user import UserCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.landsgemeinde.request import LandsgemeindeRequest
    from onegov.town6.layout import NavigationEntry


def get_global_tools(
    request: LandsgemeindeRequest
) -> Iterator[Link | LinkGroup]:

    if request.is_logged_in:
        assert request.current_username is not None

        # Logout
        yield LinkGroup(
            request.current_username, classes=('user',),
            links=(
                Link(
                    _('Logout'), request.link(
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
                _('Management'), classes=('management',),
                links=(
                    Link(
                        _('Files'),
                        request.class_link(GeneralFileCollection),
                        attrs={'class': 'files'}
                    ),
                    Link(
                        _('Images'),
                        request.class_link(ImageFileCollection),
                        attrs={'class': 'images'}
                    ),
                    Link(
                        _('Text modules'),
                        request.class_link(TextModuleCollection),
                        attrs={'class': 'text-modules'}
                    ),
                    Link(
                        _('Users'), request.class_link(UserCollection),
                        attrs={'class': 'user'}
                    ),
                    Link(
                        _('Settings'),
                        request.link(request.app.org, 'settings'),
                        attrs={'class': 'settings'}
                    ),
                    Link(
                        _('People'), request.class_link(PersonCollection),
                        attrs={'class': 'people'}
                    ),
                )
            )


def get_top_navigation(
    request: LandsgemeindeRequest
) -> Iterator[NavigationEntry]:

    yield (  # type:ignore[misc]
        Bunch(id=-1, access='public', published=True),
        Link(
            text=_('Archive'),
            url=request.class_link(AssemblyCollection)
        ),
        ()
    )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation or ()
