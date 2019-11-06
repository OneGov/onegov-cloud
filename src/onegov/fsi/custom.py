from onegov.core.elements import Link
from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _
from onegov.org.elements import LinkGroup
from onegov.org.models import GeneralFileCollection, ImageFileCollection
from onegov.user import Auth, UserCollection


def get_base_tools(request):
    # Authentication / Userprofile
    if request.is_logged_in:
        yield LinkGroup(request.current_username, classes=('user',), links=(
            Link(
                _("User Profile"), request.link(
                    request.app.org, name='userprofile'
                ), attrs={'class': 'profile'}
            ),
            Link(
                _("Logout"), request.link(
                    Auth.from_request(request), name='logout'
                ), attrs={'class': 'logout'}
            ),
        ))
    else:
        yield Link(
            _("Login"), request.link(
                Auth.from_request_path(request), name='login'
            ), attrs={'class': 'login'}
        )

        if request.app.enable_user_registration:
            yield Link(
                _("Register"), request.link(
                    Auth.from_request_path(request), name='register'
                ), attrs={'class': 'register'})

    # Editors aka Sicherheitsbeaftragter
    if request.has_role('editor'):
        pass

    # Management dropdown for admin (e.g Kursverantwortlicher)
    if request.is_manager:
        links = []
        links.append(
            Link(
                _("Files"), request.class_link(GeneralFileCollection),
                attrs={'class': 'files'}
            )
        )

        links.append(
            Link(
                _("Images"), request.class_link(ImageFileCollection),
                attrs={'class': 'images'}
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
                _('Attendees'),
                request.class_link(CourseAttendeeCollection),
                attrs={'class': 'users'}
            )
        )

        if request.is_admin:
            links.append(
                Link(
                    _("Users"), request.class_link(UserCollection),
                    attrs={'class': 'users'}
                )
            )

        yield LinkGroup(_("Management"), classes=('management',), links=links)


def get_global_tools(request):
    yield from get_base_tools(request)
    # yield from get_personal_tools(request)
    # yield from get_admin_tools(request)


@FsiApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request))
    }


# def get_admin_tools(request):
#     links = []
#
#     if request.is_admin:
#         links.append(
#             Link(
#                 text=_("All Courses"),
#                 url=request.class_link(CourseCollection),
#                 attrs={'class': 'courses'}
#             )
#         )
    # if request.is_editor:
    #     links.append(
    #         Link(
    #             text=_('Manage what?'),
    #             url=request.link()
    #         )
    #     )


def get_personal_tools(request):
    # for logged-in users show their reservations
    if request.is_logged_in:
        # session = request.session
        # username = request.current_username
        yield Link(
            text=_("Own Reservations"),
            url=request.link(''),
            attrs={
                'data-count': '0',
                'class': {'with-count', 'secondary'}
            },
        )


def get_top_navigation(request):

    # inject an activites link in front of all top navigation links
    yield Link(
        text=_("Courses"),
        url=request.class_link(CourseEventCollection)
    )

    yield Link(
        text=_("Upcoming Course Events"),
        url=request.link(CourseEventCollection.latest(request.app.session()))
    )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation