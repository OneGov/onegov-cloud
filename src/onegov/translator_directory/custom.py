from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.utils import Bunch
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.org.models import GeneralFileCollection
from onegov.ticket import TicketCollection
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.time_report import (
    TimeReportCollection,
)
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.translator_directory import _
from onegov.translator_directory.layout import DefaultLayout
from onegov.user import Auth
from onegov.user import UserCollection, UserGroupCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest
    from onegov.town6.layout import NavigationEntry


def get_global_tools(
    request: TranslatorAppRequest
) -> Iterator[Link | LinkGroup]:

    if request.is_logged_in:
        assert request.current_username is not None

        # Logout
        yield LinkGroup(
            request.current_username,
            classes=('user',),
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
                _('Management'),
                classes=('management',),
                links=(
                    Link(
                        _('Files'), request.class_link(GeneralFileCollection),
                        attrs={'class': 'files'}
                    ),
                    Link(
                        _('Settings'), request.link(
                            request.app.org, 'settings'
                        ),
                        attrs={'class': 'settings'}
                    ),
                    Link(
                        _('Settings translator directory'), request.link(
                            request.app.org, 'directory-settings'
                        ),
                        attrs={'class': 'settings'}
                    ),
                    Link(
                        _('Users'), request.class_link(UserCollection),
                        attrs={'class': 'user'}
                    ),
                    Link(
                        _('User groups'),
                        request.class_link(UserGroupCollection),
                        attrs={'class': 'users'},
                    ),
                    Link(
                        _('Time Reports'),
                        request.class_link(TimeReportCollection),
                        attrs={'class': 'time-reports'},
                    ),
                ),
            )
        elif request.is_accountant:
            yield LinkGroup(
                _('Management'),
                classes=('management',),
                links=(
                    Link(
                        _('Time Reports'),
                        request.class_link(TimeReportCollection),
                        attrs={'class': 'time-reports'},
                    ),
                ),
            )

        # Tickets
        if request.is_admin or request.is_editor:
            assert request.current_user is not None
            # Tickets
            ticket_count = request.app.ticket_count
            screen_count = ticket_count.open or ticket_count.pending
            if screen_count:
                css = ticket_count.open and 'alert' or 'info'
            else:
                css = 'no-tickets'

            yield LinkGroup(
                screen_count == 1 and _('Ticket') or _('Tickets'),
                classes=('with-count', css),
                attributes={'data-count': str(screen_count)},
                links=(
                    Link(
                        _('My Tickets'),
                        request.class_link(
                            TicketCollection, {
                                'handler': 'ALL',
                                'state': 'unfinished',
                                'owner': request.current_user.id.hex
                            },
                        ),
                        attrs={
                            'class': ('my-tickets'),
                        }
                    ),
                    Link(
                        _('Open Tickets'),
                        request.class_link(
                            TicketCollection,
                            {'handler': 'ALL', 'state': 'open'}
                        ),
                        attrs={
                            'class': ('with-count', 'alert', 'open-tickets'),
                            'data-count': str(ticket_count.open)
                        }
                    ),
                    Link(
                        _('Pending Tickets'),
                        request.class_link(
                            TicketCollection,
                            {'handler': 'ALL', 'state': 'pending'}
                        ),
                        attrs={
                            'class': ('with-count', 'info', 'pending-tickets'),
                            'data-count': str(ticket_count.pending)
                        }
                    ),
                    Link(
                        _('Closed Tickets'),
                        url=request.class_link(
                            TicketCollection,
                            {'handler': 'ALL', 'state': 'closed'}
                        ),
                        attrs={
                            'class': (
                                'with-count', 'secondary', 'closed-tickets'
                            ),
                            'data-count': str(ticket_count.closed),
                        }
                    )

                )
            )

    else:
        # Login
        yield Link(
            _('Login'), request.link(
                Auth.from_request_path(request), name='login'
            ), attrs={'class': 'login'}
        )


def get_top_navigation(
        request: TranslatorAppRequest) -> Iterator[NavigationEntry]:

    # inject an activites link in front of all top navigation links
    if request.is_manager or request.is_member:
        yield (  # type:ignore[misc]
            Bunch(id=-1, access='public', published=True),
            Link(
                text=_('Translators'),
                url=request.class_link(TranslatorCollection)
            ),
            ()
        )

    if (
        request.is_translator
        and (translator := request.current_user.translator)  # type:ignore
    ):
        yield (  # type:ignore[misc]
            Bunch(id=-1, access='public', published=True),
            Link(
                text=_('Personal Information'),
                url=request.link(translator)
            ),
            ()
        )

    if request.is_manager:
        yield (  # type:ignore[misc]
            Bunch(id=-1, access='public', published=True),
            Link(
                text=_('Languages'),
                url=request.class_link(LanguageCollection)
            ),
            ()
        )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation or ()


@TranslatorDirectoryApp.template_variables()
def get_template_variables(request: TranslatorAppRequest) -> RenderData:
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request)),
        'hide_search_header': not request.is_logged_in
    }
