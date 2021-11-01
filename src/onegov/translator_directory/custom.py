from onegov.core.elements import Link
from onegov.org.models import GeneralFileCollection
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection

from onegov.translator_directory.layout import DefaultLayout
from onegov.translator_directory import _
from onegov.org.elements import LinkGroup
from onegov.org.custom import logout_path
from onegov.user import Auth


def get_base_tools(request):

    if request.is_logged_in:

        profile_links = (
            Link(
                _("Logout"), request.link(
                    Auth.from_request(
                        request, to=logout_path(request)), name='logout'
                ), attrs={'class': 'logout'}
            ),
        )

        yield LinkGroup(
            request.current_username, classes=('user',), links=profile_links)

        links = []

        if request.is_admin:
            links.append(
                Link(
                    _("Files"), request.class_link(GeneralFileCollection),
                    attrs={'class': 'files'}
                )
            )
            links.append(
                Link(
                    _("Settings"), request.link(
                        request.app.org, 'settings'
                    ), attrs={'class': 'settings'}
                )
            )
            links.append(
                Link(
                    _("Settings translator directory"), request.link(
                        request.app.org, 'directory-settings'
                    ), attrs={'class': 'settings'}
                )
            )
            yield LinkGroup(_("Management"), classes=('management',),
                            links=links)

    else:
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
    yield Link(
        text=_("Translators"),
        url=request.class_link(TranslatorCollection)
    )

    if request.is_manager:
        yield Link(
            text=_('Languages'),
            url=request.class_link(LanguageCollection)
        )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation
