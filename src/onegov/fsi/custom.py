from onegov.core.elements import Link
from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import CourseEventCollection
from onegov.fsi.collections.reservation import ReservationCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _
from onegov.org.elements import LinkGroup
from onegov.org.models import GeneralFileCollection, ImageFileCollection
from onegov.user import Auth, UserCollection


def get_base_tools(request):

    if request.is_logged_in:

        usr = request.current_attendee
        reservation_count = '0' if not usr else str(usr.reservations.count())

        profile_links = [
            Link(
                _("Attendee Profile"), request.link(usr),
                attrs={'class': 'profile'}
            )
        ] if usr else []
        if request.is_manager:
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
                    Auth.from_request(request), name='logout'
                ), attrs={'class': 'logout'}
            )
        )

        yield LinkGroup(
            request.current_username, classes=('user',), links=profile_links)

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
            links.append(
                Link(
                    _('Reservations'),
                    request.class_link(ReservationCollection)
                )
            )

            if request.is_admin:
                links.append(
                    Link(
                        _("Users"), request.class_link(UserCollection),
                        attrs={'class': 'users'}
                    )
                )

            yield LinkGroup(_("Management"), classes=('management',),
                            links=links)
        if reservation_count:
            css = 'alert open-tickets'
        else:
            css = 'no-tickets'

        yield Link(
            reservation_count == 1 and _("Reservation") or _("Reservations"),
            request.link(
                ReservationCollection(request.session,
                                      request.attendee_id),
            ),
            attrs={
                'class': ('with-count', css),
                'data-count': reservation_count
            }
        )
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


def get_global_tools(request):
    yield from get_base_tools(request)


@FsiApp.template_variables()
def get_template_variables(request):
    return {
        'global_tools': tuple(get_global_tools(request)),
        'top_navigation': tuple(get_top_navigation(request))
    }


def get_top_navigation(request):

    # inject an activites link in front of all top navigation links
    yield Link(
        text=_("Courses"),
        url=request.class_link(CourseCollection)
    )

    yield Link(
        text=_("Upcoming Course Events"),
        url=request.link(CourseEventCollection.latest(request.app.session()))
    )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation
