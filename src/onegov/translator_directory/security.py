from onegov.core.security import Personal
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.models.translator import Translator

"""
The idea for permission is the following:

Personal: beeing logged in by default, can be overwritten model wise
Private: also editor can access it
Secret: admins

"""


@TranslatorDirectoryApp.permission_rule(model=object, permission=Personal)
def local_is_logged_in(app, identity, model, permission):
    return identity.role in ('admin', 'editor', 'member')


@TranslatorDirectoryApp.permission_rule(model=Translator, permission=object)
def hide_translator_for_non_admins(app, identity, model, permission):
    if model.for_admins_only and identity.role != 'admin':
        return False
    return local_is_logged_in(app, identity, model, permission)
