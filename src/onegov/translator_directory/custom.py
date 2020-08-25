from onegov.core.elements import Link
from onegov.translator_directory import TranslatorDirectoryApp

from onegov.translator_directory.layout import DefaultLayout
from onegov.translator_directory import _
from onegov.org.elements import LinkGroup
from onegov.org.custom import logout_path
from onegov.user import Auth, UserCollection


def get_base_tools(request):

    if request.is_logged_in:

        usr = request.current_username

        profile_links = [
            Link(
                _("Profile"), request.link(usr),
                attrs={'class': 'profile'}
            )
        ] if usr else []
        if request.is_admin:
            profile_links.append(
                Link(
                    _("User Profile"),
                    request.link(request.app.org, name='userprofile'),
                    attrs={'class': 'profile'}
                )
            )

        profile_links.append(
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
                    _("Settings"), request.link(
                        request.app.org, 'settings'
                    ), attrs={'class': 'settings'}
                )
            )

            links.append(
                Link(
                    _("Users"), request.class_link(UserCollection),
                    attrs={'class': 'users'}
                )
            )
        if request.is_manager:
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
        text=_("Some Link"),
        url=''
    )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation
