from __future__ import annotations

from onegov.activity import Activity, ActivityCollection, Booking, Occasion
from onegov.core.security import Public, Private, Personal
from onegov.core.security.roles import (
    get_roles_setting as get_roles_setting_base)
from onegov.core.security.rules import has_permission_logged_in
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.const import VISIBLE_ACTIVITY_STATES
from onegov.feriennet.const import OWNER_EDITABLE_STATES
from onegov.feriennet.models import NotificationTemplate
from onegov.org.models import ImageFileCollection, SiteCollection, TicketNote
from onegov.ticket import Ticket


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity, NoIdentity
    from onegov.core.security.roles import Intent


@FeriennetApp.replace_setting_section(section='roles')
def get_roles_setting() -> dict[str, set[type[Intent]]]:
    # NOTE: Without a supporter role for now
    return get_roles_setting_base()


def is_owner(username: str, activity: Activity) -> bool:
    """ Returns true if the given username is the owner of the given
    activity.

    """
    if not username:
        return False

    return username == activity.username


@FeriennetApp.permission_rule(model=object, permission=object)
def local_has_permission_logged_in(
    app: FeriennetApp,
    identity: Identity,
    model: object,
    permission: object
) -> bool:

    # access is stricter in feriennet, only admins see non-public models
    if identity.role != 'admin':
        if getattr(model, 'access', None) == 'private':
            return False

    return has_permission_logged_in(app, identity, model, permission)


@FeriennetApp.permission_rule(model=object, permission=Private)
def has_private_permission_logged_in(
    app: FeriennetApp,
    identity: Identity,
    model: object,
    permission: type[Private]
) -> bool:
    """ Take away private permission for editors. For exceptions see
    the permission rules below.

    """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return False


@FeriennetApp.permission_rule(model=SiteCollection, permission=Private)
def has_private_permission_site_collection(
    app: FeriennetApp,
    identity: Identity,
    model: SiteCollection,
    permission: type[Private]
) -> bool:
    """ Give editors the ability to access the site collection. """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=ImageFileCollection, permission=Private)
def has_private_permission_image_collection(
    app: FeriennetApp,
    identity: Identity,
    model: ImageFileCollection,
    permission: type[Private]
) -> bool:
    """ Give editors the ability to access the image file collection (but not
    the file collection!).

    """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=ActivityCollection, permission=Private)
def has_private_permission_activity_collections(
    app: FeriennetApp,
    identity: Identity,
    model: ActivityCollection[Any],
    permission: type[Private]
) -> bool:
    """ Give the editor private permission for activity collections (needed
    to create new activites).

    """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=Activity, permission=Private)
def has_private_permission_activities(
    app: FeriennetApp,
    identity: Identity,
    model: Activity,
    permission: type[Private]
) -> bool:
    """ Give the editor private permission for activities. """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return (
        is_owner(identity.userid, model)
        and model.state in OWNER_EDITABLE_STATES
    )


@FeriennetApp.permission_rule(model=Occasion, permission=Private)
def has_private_permission_occasions(
    app: FeriennetApp,
    identity: Identity,
    model: Occasion,
    permission: type[Private]
) -> bool:
    """ Give the editor private permission for occasions. """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return (
        is_owner(identity.userid, model.activity)
        and model.activity.state in OWNER_EDITABLE_STATES
    )


@FeriennetApp.permission_rule(
    model=NotificationTemplateCollection,
    permission=Private
)
def has_private_permission_notifications(
    app: FeriennetApp,
    identity: Identity,
    model: NotificationTemplateCollection,
    permission: type[Private]
) -> bool:
    """ Give the editor private permission for notification templates. """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=NotificationTemplate, permission=Private)
def has_private_permission_notification(
    app: FeriennetApp,
    identity: Identity,
    model: NotificationTemplate,
    permission: type[Private]
) -> bool:
    """ Give the editor private permission for notification templates. """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=Activity, permission=Public, identity=None)
def has_public_permission_not_logged_in(
    app: FeriennetApp,
    identity: NoIdentity | None,
    model: Activity,
    permission: type[Public]
) -> bool:
    """ Only make activites anonymously accessible with certain states. """

    return model.state in VISIBLE_ACTIVITY_STATES['anonymous']


@FeriennetApp.permission_rule(model=Activity, permission=Public)
def has_public_permission_logged_in(
    app: FeriennetApp,
    identity: Identity,
    model: Activity,
    permission: type[Public]
) -> bool:
    """ Only make activites accessible with certain states (or if owner). """

    # roles other than admin/editor are basically treated as anonymous,
    # so fallback in this case
    if identity.role not in ('admin', 'editor'):
        return has_public_permission_not_logged_in(
            app, None, model, permission)

    return (
        is_owner(identity.userid, model)
        or model.state in VISIBLE_ACTIVITY_STATES[identity.role]
    )


@FeriennetApp.permission_rule(model=Booking, permission=Personal)
def has_personal_permission_booking(
    app: FeriennetApp,
    identity: Identity,
    model: Booking,
    permission: type[Personal]
) -> bool:
    """ Ensure that logged in users may only change their own bookings. """

    if identity.role == 'admin':
        return True

    return model.username == identity.userid


@FeriennetApp.permission_rule(
    model=OccasionAttendeeCollection,
    permission=Private
)
def has_private_permission_occasion_attendee_collection(
    app: FeriennetApp,
    identity: Identity,
    model: OccasionAttendeeCollection,
    permission: type[Private]
) -> bool:
    """ Ensure that organisators have access to the attendee collection. """

    if identity.role in ('admin', 'editor'):
        return True

    return local_has_permission_logged_in(app, identity, model, permission)


@FeriennetApp.permission_rule(model=Ticket, permission=Personal)
@FeriennetApp.permission_rule(model=TicketNote, permission=Personal)
def restrict_personal_ticket_views(
    app: FeriennetApp,
    identity: Identity,
    model: Ticket | TicketNote,
    permission: type[Personal]
) -> bool:
    """
    Ensure that only managers may view ticket details.

    Since members in feriennet are customers which shouldn't be able to
    view other customer's private information.
    """

    return identity.role in ('admin', 'editor')
