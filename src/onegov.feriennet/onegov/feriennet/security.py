from onegov.activity import Activity, ActivityCollection, Booking, Occasion
from onegov.core.security import Public, Private, Personal
from onegov.core.security.rules import has_permission_logged_in
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import NotificationTemplateCollection
from onegov.feriennet.collections import OccasionAttendeeCollection
from onegov.feriennet.const import VISIBLE_ACTIVITY_STATES
from onegov.feriennet.const import OWNER_EDITABLE_STATES
from onegov.feriennet.models import NotificationTemplate
from onegov.org.models import ImageFileCollection, SiteCollection


def is_owner(username, activity):
    """ Returns true if the given username is the owner of the given
    activity.

    """
    if not username:
        return False

    return username == activity.username


@FeriennetApp.permission_rule(model=object, permission=object)
def local_has_permission_logged_in(app, identity, model, permission):

    # is_hidden_from_public is stricter in feriennet, only admins see it
    if identity.role != 'admin':
        if getattr(model, 'is_hidden_from_public', False):
            return False

    return has_permission_logged_in(app, identity, model, permission)


@FeriennetApp.permission_rule(model=object, permission=Private)
def has_private_permission_logged_in(app, identity, model, permission):
    """ Take away private permission for editors. For exceptions see
    the permission rules below.

    """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return False


@FeriennetApp.permission_rule(model=SiteCollection, permission=Private)
def has_private_permission_site_collection(app, identity, model, permission):
    """ Give editors the ability to access the site collection. """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=ImageFileCollection, permission=Private)
def has_private_permission_image_collection(app, identity, model, permission):
    """ Give editors the ability to access the image file collection (but not
    the file collection!).

    """

    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=ActivityCollection, permission=Private)
def has_private_permission_activity_collections(
        app, identity, model, permission):
    """ Give the editor private permission for activity collections (needed
    to create new activites).

    """

    # only overries the editor role
    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=Activity, permission=Private)
def has_private_permission_activities(app, identity, model, permission):
    """ Give the editor private permission for activities. """

    # only overries the editor role
    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return is_owner(identity.userid, model) \
        and model.state in OWNER_EDITABLE_STATES


@FeriennetApp.permission_rule(model=Occasion, permission=Private)
def has_private_permission_occasions(app, identity, model, permission):
    """ Give the editor private permission for occasions. """

    # only overries the editor role
    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return is_owner(identity.userid, model.activity) \
        and model.activity.state in OWNER_EDITABLE_STATES


@FeriennetApp.permission_rule(
    model=NotificationTemplateCollection,
    permission=Private)
def has_private_permission_notifications(app, identity, model, permission):
    """ Give the editor private permission for notification templates. """

    # only overries the editor role
    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=NotificationTemplate, permission=Private)
def has_private_permission_notification(app, identity, model, permission):
    """ Give the editor private permission for notification templates. """

    # only overries the editor role
    if identity.role != 'editor':
        return local_has_permission_logged_in(app, identity, model, permission)

    return True


@FeriennetApp.permission_rule(model=Activity, permission=Public, identity=None)
def has_public_permission_not_logged_in(app, identity, model, permission):
    """ Only make activites anonymously accessible with certain states. """

    return model.state in VISIBLE_ACTIVITY_STATES['anonymous']


@FeriennetApp.permission_rule(model=Activity, permission=Public)
def has_public_permission_logged_in(app, identity, model, permission):
    """ Only make activites accessible with certain states (or if owner). """

    # roles other than admin/editor are basically treated as anonymous,
    # so fallback in this case
    if identity.role not in ('admin', 'editor'):
        return has_public_permission_not_logged_in(
            app, None, model, permission)

    return is_owner(identity.userid, model) \
        or model.state in VISIBLE_ACTIVITY_STATES[identity.role]


@FeriennetApp.permission_rule(model=Booking, permission=Personal)
def has_personal_permission_booking(app, identity, model, permission):
    """ Ensure that logged in users may only change their own bookings. """

    if identity.role == 'admin':
        return True

    return model.username == identity.userid


@FeriennetApp.permission_rule(
    model=OccasionAttendeeCollection,
    permission=Private)
def has_private_permission_occasion_attendee_collection(
        app, identity, model, permission):
    """ Ensure that organisators have access to the attendee colleciton. """

    if identity.role in ('admin', 'editor'):
        return True

    return local_has_permission_logged_in(app, identity, model, permission)
