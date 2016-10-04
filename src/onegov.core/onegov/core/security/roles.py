from onegov.core.framework import Framework
from onegov.core.security import Public, Personal, Private, Secret


@Framework.setting_section(section="roles")
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
        # the public has some access
        'anonymous': set((
            Public,
        ))
    }
