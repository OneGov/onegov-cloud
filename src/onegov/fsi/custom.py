from onegov.core.elements import Link
from onegov.fsi import FsiApp
from onegov.fsi.collections.attendee import CourseAttendeeCollection
from onegov.fsi.collections.audit import AuditCollection
from onegov.fsi.collections.course import CourseCollection
from onegov.fsi.collections.course_event import PastCourseEventCollection
from onegov.fsi.collections.subscription import SubscriptionsCollection
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _
from onegov.org.elements import LinkGroup
from onegov.org.custom import logout_path
from onegov.org.models import GeneralFileCollection, ImageFileCollection
from onegov.user import Auth, UserCollection


def get_base_tools(request):

    if request.is_logged_in:

        usr = request.attendee
        reservation_count = 0 if not usr else usr.reservations.count()

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

        # Management dropdown for admin (e.g Kursverantwortlicher)
        links = []

        if request.is_manager:
            links.append(
                Link(
                    _('Attendees'),
                    request.link(CourseAttendeeCollection(
                        request.session, auth_attendee=usr)),
                    attrs={'class': 'attendees'}
                )
            )
            links.append(
                Link(
                    _('Event Subscriptions'),
                    request.link(SubscriptionsCollection(
                        request.session, auth_attendee=usr)),
                    attrs={'class': 'reservations'}
                )
            )

        if request.is_admin:
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
                    _("Users"), request.class_link(UserCollection),
                    attrs={'class': 'users'}
                )
            )
        if request.is_manager:
            yield LinkGroup(_("Management"), classes=('management',),
                            links=links)

        if reservation_count:
            css = 'alert open-tickets'
        else:
            css = 'no-tickets'

        yield Link(
            reservation_count == 1 and _("Event Subscription")
            or _("Event Subscriptions"),
            request.link(
                SubscriptionsCollection(
                    request.session,
                    attendee_id=request.attendee_id,
                    auth_attendee=usr
                ),
            ),
            attrs={
                'class': ('with-count', css),
                'data-count': str(reservation_count)
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
        'top_navigation': tuple(get_top_navigation(request)),
        'hide_search_header': not request.is_logged_in
    }


def get_top_navigation(request):

    # inject an activites link in front of all top navigation links
    yield Link(
        text=_("Courses"),
        url=request.class_link(CourseCollection)
    )
    if request.is_manager:
        yield Link(
            text=_("Audit"),
            url=request.class_link(AuditCollection)
        )
        yield Link(
            text=_("Attendee Check"),
            url=request.class_link(PastCourseEventCollection)
        )

    layout = DefaultLayout(request.app.org, request)
    yield from layout.top_navigation
