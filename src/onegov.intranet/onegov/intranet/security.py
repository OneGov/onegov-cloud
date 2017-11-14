from onegov.core.security import Public, Private, Personal, Secret
from onegov.core.static import StaticFile
from onegov.core.theme import ThemeFile
from onegov.intranet.app import IntranetApp
from onegov.user import Auth


@IntranetApp.setting_section(section="roles")
def get_roles_setting():
    """ Returns the default roles available to onegov.core applications.

    Applications building on onegov.core may add more roles and permissions,
    or replace the existing ones entirely, though it's not something that
    one should do carelessly.

    The default roles are:

    **admin**
        Has access to everything

    **editor**
        Has access to most things

    **member**
        Has access their own data. Be careful though, core doesn't know about
        personal data, so this is just a role to implement registered users.
        As with all permissions, making sure the right information is shown
        is up to the applications.

    **anonymous**
        Has access to public things

    """
    return {
        # the admin role has access to everything
        'admin': set((
            Public,
            Private,
            Personal,
            Secret
        )),
        # the editor can do most things
        'editor': set((
            Public,
            Private,
            Personal,
        )),
        # registered users can do a few things
        'member': set((
            Public,
            Personal,
        )),
        # the public has no access whatsoever
        'anonymous': set()
    }


@IntranetApp.permission_rule(
    model=StaticFile,
    permission=Public,
    identity=None)
def may_view_static_files_not_logged_in(app, identity, model, permission):
    """ Always allow to view static files.

    Those files are public anyway, since we are open-source.

    """
    return True


@IntranetApp.permission_rule(
    model=ThemeFile,
    permission=Public,
    identity=None)
def may_view_theme_files_not_logged_in(app, identity, model, permission):
    """ Always allow to view theme files.

    Those files are public anyway, since we are open-source.

    """
    return True


@IntranetApp.permission_rule(
    model=Auth,
    permission=Public,
    identity=None)
def may_view_auth_not_logged_in(app, identity, model, permission):
    """ Anonymous needs to be able to log in. """
    return True
