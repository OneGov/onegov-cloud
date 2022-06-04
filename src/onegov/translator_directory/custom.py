from onegov.core.elements import Link
from onegov.org.custom import logout_path
from onegov.org.elements import LinkGroup
from onegov.org.models import GeneralFileCollection
from onegov.ticket import TicketCollection
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory import _
from onegov.translator_directory.layout import DefaultLayout
from onegov.user import Auth
from onegov.user import UserCollection


def get_base_tools(request):

    if request.is_logged_in:

        # Logout
        yield LinkGroup(
            request.current_username, classes=('user',),
            links=(
                Link(
                    _("Logout"), request.link(
                        Auth.from_request(
                            request, to=logout_path(request)), name='logout'
                    ), attrs={'class': 'logout'}
                ),
            )
        )

        # Management Dropdown
        if request.is_admin:
            yield LinkGroup(
                _("Management"), classes=('management',),
                links=(
                    Link(
                        _("Files"), request.class_link(GeneralFileCollection),
                        attrs={'class': 'files'}
                    ),
                    Link(
                        _("Settings"), request.link(
                            request.app.org, 'settings'
                        ), attrs={'class': 'settings'}
                    ),
                    Link(
                        _("Settings translator directory"), request.link(
                            request.app.org, 'directory-settings'
                        ), attrs={'class': 'settings'}
                    ),
                    Link(
                        _("Users"), request.class_link(UserCollection),
                        attrs={'class': 'user'}
                    )
                )
            )

        # Tickets
        if request.is_admin:
            # Tickets
            ticket_count = request.app.ticket_count
            screen_count = ticket_count.open or ticket_count.pending
            if screen_count:
                css = ticket_count.open and 'alert' or 'info'
            else:
                css = 'no-tickets'

            yield LinkGroup(
                screen_count == 1 and _("Ticket") or _("Tickets"),
                classes=('with-count', css),
                attributes={'data-count': str(screen_count)},
                links=(
                    Link(
                        _("My Tickets"),
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
                        _("Open Tickets"),
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
                        _("Pending Tickets"),
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
                        _("Closed Tickets"),
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
            _("Login"), request.link(
                Auth.from_request_path(request), name='login'
            ), attrs={'class': 'login'}
        )


def get_global_tools(request):
    yield from get_base_tools(request)


@TranslatorDirectoryApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request)),
        'hide_search_header': not request.is_logged_in
    }


def get_top_navigation(request):

    # inject an activites link in front of all top navigation links
    if request.is_manager or request.is_member:
        yield Link(
            text=_("Translators"),
            url=request.class_link(TranslatorCollection)
        )

    if request.is_translator:
        yield Link(
            text=_("Personal Information"),
            url=request.class_link(TranslatorCollection, name='self')
        )

    if request.is_manager:
        yield Link(
            text=_('Languages'),
            url=request.class_link(LanguageCollection)
        )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation
