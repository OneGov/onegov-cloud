from __future__ import annotations

from onegov.core.framework import Framework
from onegov.core.security import Public, Personal, Private, Secret


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .permissions import Intent


@Framework.setting_section(section='roles')
def get_roles_setting() -> dict[str, set[type[Intent]]]:
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
        'admin': {
            Public,
            Private,
            Personal,
            Secret
        },
        # the editor can do most things
        'editor': {
            Public,
            Private,
            Personal,
        },
        # registered users can do a few things
        'member': {
            Public,
            Personal,
        },
        # the public has some access
        'anonymous': {
            Public,
        }
    }
