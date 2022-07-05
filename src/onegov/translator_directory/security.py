from onegov.core.security import Public, Personal
from onegov.core.security.roles import get_roles_setting as \
    get_roles_setting_base
from onegov.file import File
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.ticket import Ticket, TicketCollection
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.documents import \
    TranslatorDocumentCollection
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.models.ticket import TranslatorMutationTicket
from onegov.user import Auth

"""

The standard permission model is used and mapped as followed:
- Anonymous users can log in.
- Translators can view their own personal information and report changes.
- Members can additionally view the translators and their vouchers.
- Editors can additionally editor some informations of translators.
- Admins can do everything.

"""


@TranslatorDirectoryApp.setting_section(section="roles")
def get_roles_setting():
    result = get_roles_setting_base()
    result['translator'] = {Public}
    return result


@TranslatorDirectoryApp.permission_rule(model=Auth, permission=object)
def restrict_auth_access(app, identity, model, permission):
    if permission == Personal and identity.role == 'translator':
        return True

    return permission in getattr(app.settings.roles, identity.role)


@TranslatorDirectoryApp.permission_rule(model=Translator, permission=object)
def restrict_translator_access(app, identity, model, permission):
    if model.for_admins_only and identity.role not in ('admin', 'translator'):
        return False

    if (
        identity.role == 'translator'
        and identity.userid == model.email
        and permission == Personal
    ):
        return True

    return permission in getattr(app.settings.roles, identity.role)


@TranslatorDirectoryApp.permission_rule(
    model=Translator, permission=object, identity=None)
def restrict_translator_access_anon(app, identity, model, permission):
    if model.for_admins_only:
        return False

    return permission in app.settings.roles.anonymous


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFileCollection, permission=object)
def restrict_general_file_coll_access(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFileCollection, permission=object, identity=None)
def restrict_general_file_coll_access_anon(app, identity, model, permission):
    return False


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


@TranslatorDirectoryApp.permission_rule(
    model=TranslatorDocumentCollection, permission=object, identity=None)
def disable_translator_docs_coll_access_anon(app, identity, model, permission):
    return False


@TranslatorDirectoryApp.permission_rule(
    model=TicketCollection, permission=object)
def restricts_ticket(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=TicketCollection, permission=object, identity=None)
def restricts_ticket_anon(app, identity, model, permission):
    return False


@TranslatorDirectoryApp.permission_rule(model=Ticket, permission=object)
def restrict_ticket(app, identity, model, permission):
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=Ticket, permission=object, identity=None)
def restrict_ticket_anon(app, identity, model, permission):
    return False


@TranslatorDirectoryApp.permission_rule(
    model=TranslatorMutationTicket, permission=object)
def restrict_translator_mutation_ticket(app, identity, model, permission):
    if (
        permission == Public
        and identity.role in ('editor', 'member', 'translator')
        and model.handler
    ):
        return model.handler.email == identity.userid

    return identity.role == 'admin'
