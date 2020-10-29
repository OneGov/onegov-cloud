from onegov.core.security import Personal
from onegov.file import File
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.documents import \
    TranslatorDocumentCollection
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


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFileCollection, permission=object)
def restrict_general_file_access(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFile, permission=object)
def restrict_general_file_access(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=File, permission=object)
def restrict_general_file_access(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=TranslatorDocumentCollection, permission=object)
def restrict_general_file_access(app, identity, model, permission):
    return identity.role == 'admin'
