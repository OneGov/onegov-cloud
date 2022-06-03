from onegov.core.security import Public, Personal, Private, Secret
from onegov.file import File
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.documents import \
    TranslatorDocumentCollection
from onegov.translator_directory.models.translator import Translator

"""

The standard permission model is used and mapped as followed:
- Anonymous users can log in.
- Members can additionally view the translators and their vouchers.
- Editors can additionally editor some informations of translators.
- Admins can do everything.

Furthermore, there is a special permission `Registered` for the users linked to
a specific translator entry:
- Translators can view only their own personal informations. They don't have
  access to the translator model, only to specialized views which query the
  right translator model.

"""


class Registered:
    """ Translators are allowed to do this. """


@TranslatorDirectoryApp.setting_section(section="roles")
def get_roles_setting():

    return {
        'admin': set((
            Public,
            Registered,
            Private,
            Personal,
            Secret
        )),
        'editor': set((
            Public,
            Private,
            Personal,
        )),
        'member': set((
            Public,
            Personal,
        )),
        'translator': set((
            Public,
            Registered
        )),
        'anonymous': set((
            Public,
        ))
    }


@TranslatorDirectoryApp.permission_rule(model=Translator, permission=object)
def restrict_translator_access(app, identity, model, permission):
    if model.for_admins_only and identity.role != 'admin':
        return False
    return permission in getattr(app.settings.roles, identity.role)


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFileCollection, permission=object)
def restrict_general_file_collection_access(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFile, permission=object)
def restrict_general_file_access(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=File, permission=object)
def restrict_file_access(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=TranslatorDocumentCollection, permission=object)
def restrict_translator_docs_coll_access(app, identity, model, permission):
    return identity.role == 'admin'
