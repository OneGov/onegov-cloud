from onegov.core.security import Personal
from onegov.translator_directory import TranslatorDirectoryApp

"""
The idea for permission is the following:

Personal: beeing logged in by default, can be overwritten model wise
Private: also editor can access it
Secret: admins

"""


@TranslatorDirectoryApp.permission_rule(model=object, permission=Personal)
def local_is_logged_in(app, identity, model, permission):
    return identity.role in ('admin', 'editor', 'member')


