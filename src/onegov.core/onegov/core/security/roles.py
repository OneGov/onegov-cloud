from onegov.core import Framework
from onegov.core.security import Public, Private, Secret


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

    **anonymous**
        Has access to public things

    """
    return {
        # the admin role has access to everything
        'admin': set((
            Public,
            Private,
            Secret
        )),
        # the editor can do most things
        'editor': set((
            Public,
            Private
        )),
        # the public has some access
        'anonymous': set((
            Public,
        ))
    }
