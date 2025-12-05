from __future__ import annotations

from onegov.translator_directory.models.ticket import TimeReportTicket

from onegov.core.security import Public, Personal
from onegov.core.security.roles import (
    get_roles_setting as get_roles_setting_base)
from onegov.user import UserGroup
from onegov.file import File
from onegov.org.models import GeneralFileCollection, GeneralFile
from onegov.ticket import Ticket, TicketCollection
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.documents import (
    TranslatorDocumentCollection)
from onegov.translator_directory.models.translator import Translator
from onegov.translator_directory.models.ticket import AccreditationTicket
from onegov.translator_directory.models.ticket import TranslatorMutationTicket
from onegov.user import Auth


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity, NoIdentity
    from onegov.core.security.roles import Intent

"""

The standard permission model is used and mapped as followed:
- Anonymous users can log in.
- Translators can view their own personal information and report changes.
- Members can additionally view the translators and their vouchers.
- Supporters can additionally view, receive and handle tickets.
- Editors can additionally edit some information of translators.
- Admins can do everything.

"""


@TranslatorDirectoryApp.replace_setting_section(section='roles')
def get_roles_setting() -> dict[str, set[type[Intent]]]:
    # NOTE: Without a supporter role for now
    result = get_roles_setting_base()
    result['translator'] = {Public}
    return result


@TranslatorDirectoryApp.permission_rule(model=object, permission=object)
def has_permission_logged_in(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: object,
    permission: object
) -> bool:
    if getattr(model, 'access', None) == 'private':
        if identity.role not in ('admin', 'editor'):
            return False

    if getattr(model, 'access', None) == 'member':
        if identity.role not in ('admin', 'editor', 'member', 'translator'):
            return False

    return permission in getattr(app.settings.roles, identity.role)


@TranslatorDirectoryApp.permission_rule(model=Auth, permission=object)
def restrict_auth_access(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: Auth,
    permission: object
) -> bool:
    if permission == Personal and identity.role == 'translator':
        return True

    return permission in getattr(app.settings.roles, identity.role)


@TranslatorDirectoryApp.permission_rule(model=Translator, permission=object)
def restrict_translator_access(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: Translator,
    permission: object
) -> bool:
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
def restrict_translator_access_anon(
    app: TranslatorDirectoryApp,
    identity: NoIdentity,
    model: Translator,
    permission: object
) -> bool:
    if model.for_admins_only:
        return False

    return permission in app.settings.roles.anonymous


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFileCollection, permission=object)
def restrict_general_file_coll_access(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: GeneralFileCollection,
    permission: object
) -> bool:
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFileCollection, permission=object, identity=None)
def restrict_general_file_coll_access_anon(
    app: TranslatorDirectoryApp,
    identity: NoIdentity,
    model: GeneralFileCollection,
    permission: object
) -> bool:
    return False


@TranslatorDirectoryApp.permission_rule(
    model=File, permission=object)
def restrict_file_access(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: File,
    permission: object
) -> bool:
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=File, permission=object, identity=None)
def restrict_file_access_anon(
    app: TranslatorDirectoryApp,
    identity: NoIdentity,
    model: File,
    permission: object
) -> bool:
    return False


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFile, permission=object)
def restrict_general_file_access(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: GeneralFile,
    permission: object
) -> bool:
    if not model.published:
        if identity.role not in ('admin', 'editor', 'member', 'translator'):
            return False

    return permission in getattr(app.settings.roles, identity.role)


@TranslatorDirectoryApp.permission_rule(
    model=GeneralFile, permission=object, identity=None)
def restrict_general_file_access_anon(
    app: TranslatorDirectoryApp,
    identity: NoIdentity,
    model: GeneralFile,
    permission: object
) -> bool:
    if not model.published:
        return False

    return permission == Public


@TranslatorDirectoryApp.permission_rule(
    model=TranslatorDocumentCollection, permission=object)
def restrict_translator_docs_coll_access(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: TranslatorDocumentCollection,
    permission: object
) -> bool:
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=TranslatorDocumentCollection, permission=object, identity=None)
def disable_translator_docs_coll_access_anon(
    app: TranslatorDirectoryApp,
    identity: NoIdentity,
    model: TranslatorDocumentCollection,
    permission: object
) -> bool:
    return False


@TranslatorDirectoryApp.permission_rule(
    model=TicketCollection, permission=object)
def restricts_ticket(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: TicketCollection,
    permission: object
) -> bool:
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=TicketCollection, permission=object, identity=None)
def restricts_ticket_anon(
    app: TranslatorDirectoryApp,
    identity: NoIdentity,
    model: TicketCollection,
    permission: object
) -> bool:
    return False


@TranslatorDirectoryApp.permission_rule(model=Ticket, permission=object)
def restrict_ticket(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: Ticket,
    permission: object
) -> bool:
    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=Ticket, permission=object, identity=None)
def restrict_ticket_anon(
    app: TranslatorDirectoryApp,
    identity: NoIdentity,
    model: Ticket,
    permission: object
) -> bool:
    return False


@TranslatorDirectoryApp.permission_rule(
    model=AccreditationTicket, permission=object, identity=None)
def restrict_accreditation_ticket_anon(
    app: TranslatorDirectoryApp,
    identity: NoIdentity,
    model: AccreditationTicket,
    permission: object
) -> bool:
    return permission == Public


@TranslatorDirectoryApp.permission_rule(
    model=AccreditationTicket, permission=object)
def restrict_accreditation_ticket(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: AccreditationTicket,
    permission: object
) -> bool:
    if permission == Public:
        return True

    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=TranslatorMutationTicket, permission=object)
def restrict_translator_mutation_ticket(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: TranslatorMutationTicket,
    permission: object
) -> bool:
    if (
        permission == Public
        and identity.role in ('editor', 'member', 'translator')
        and model.handler
    ):
        return model.handler.email == identity.userid

    return identity.role == 'admin'


@TranslatorDirectoryApp.permission_rule(
    model=TimeReportTicket, permission=object)
def restrict_translator_time_report_ticket(
    app: TranslatorDirectoryApp,
    identity: Identity,
    model: TimeReportTicket,
    permission: object
) -> bool:
    if (
        identity.role in ('member', 'translator')
        and model.handler
    ):
        if model.handler.email == identity.userid:
            return True

        if identity.role == 'editor':
            time_report = model.handler.time_report  # type: ignore[attr-defined]
            if time_report and time_report.finanzstelle:
                user_groups = (
                    app.session()
                    .query(UserGroup)
                    .all()
                )
                for group in user_groups:
                    group_finanzstelle = (
                        group.meta.get('finanzstelle') if group.meta else None
                    )
                    if group_finanzstelle == time_report.finanzstelle:
                        return True

        return False

    return identity.role in {'editor', 'admin'}
