from __future__ import annotations

from onegov.core.security import Public, Personal, Private
from onegov.core.security.roles import (
    get_roles_setting as get_roles_setting_base)
from onegov.org.app import OrgApp
from onegov.org.models import Export, TicketNote
from onegov.org.views.directory import DirectorySubmissionAction
from onegov.pay import Payment, PaymentCollection
from onegov.ticket import Ticket, TicketCollection
from onegov.ticket import TicketInvoice, TicketInvoiceCollection
from onegov.ticket.collection import ArchivedTicketCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from morepath.authentication import Identity
    from onegov.core.security.roles import Intent


@OrgApp.replace_setting_section(section='roles')
def get_roles_setting() -> dict[str, set[type[Intent]]]:
    """ Returns the default roles available to onegov.org applications.

    Applications building on onegov.org may add more roles and permissions,
    or replace the existing ones entirely, though it's not something that
    one should do carelessly.

    The default roles are:

    **admin**
        Has access to everything

    **editor**
        Has access to most things

    **supporter**
        Has access to the ticket (and payment) system

    **member**
        Has access their own data

    **anonymous**
        Has access to public things

    """
    result = get_roles_setting_base()
    result['supporter'] = {Public, Personal}
    return result


@OrgApp.permission_rule(model=Export, permission=object, identity=None)
def has_export_permission_not_logged_in(
    app: OrgApp,
    identity: None,
    model: Export,
    permission: object
) -> bool:
    return model.permission in app.settings.roles.anonymous


@OrgApp.permission_rule(model=Export, permission=object)
def has_export_permissions_logged_in(
    app: OrgApp,
    identity: Identity,
    model: Export,
    permission: object
) -> bool:
    return model.permission in getattr(app.settings.roles, identity.role)


@OrgApp.permission_rule(model=Ticket, permission=object)
def has_permission_ticket(
    app: OrgApp,
    identity: Identity,
    model: Ticket,
    permission: object
) -> bool:

    role = identity.role

    # Downgrade the role
    if role not in ('admin', 'anonymous'):
        groups = app.ticket_permissions.get(model.handler_code, {})
        if model.group in groups:
            if identity.groupids.isdisjoint(groups[model.group]):
                role = 'member'
        elif None in groups:
            if identity.groupids.isdisjoint(groups[None]):
                role = 'member'

    if role == 'member':
        if getattr(model, 'access', None) == 'private':
            return False

    # Supporter has elevated permissions for tickets
    if role == 'supporter':
        return permission in {Public, Private, Personal}

    return permission in getattr(app.settings.roles, role)


@OrgApp.permission_rule(model=DirectorySubmissionAction, permission=object)
@OrgApp.permission_rule(model=Payment, permission=object)
@OrgApp.permission_rule(model=TicketInvoice, permission=object)
@OrgApp.permission_rule(model=TicketNote, permission=object)
def has_permission_ticket_related_model(
    app: OrgApp,
    identity: Identity,
    model: DirectorySubmissionAction,
    permission: object
) -> bool:

    if model.ticket is None:
        return permission in getattr(app.settings.roles, identity.role)

    return has_permission_ticket(app, identity, model.ticket, permission)


@OrgApp.permission_rule(model=TicketCollection, permission=object)
@OrgApp.permission_rule(model=ArchivedTicketCollection, permission=object)
def has_permission_ticket_collection(
    app: OrgApp,
    identity: Identity,
    model: TicketCollection | ArchivedTicketCollection,
    permission: object
) -> bool:

    # Supporter has elevated permissions for tickets
    if identity.role == 'supporter':
        return permission in {Public, Private, Personal}

    return permission in getattr(app.settings.roles, identity.role)


@OrgApp.permission_rule(model=PaymentCollection, permission=object)
@OrgApp.permission_rule(model=TicketInvoiceCollection, permission=object)
def has_permission_payment_collection(
    app: OrgApp,
    identity: Identity,
    model: PaymentCollection | TicketInvoiceCollection,
    permission: object
) -> bool:

    # Supporter has elevated permissions for payments/invoices
    if identity.role == 'supporter':
        return permission in {Public, Private, Personal}

    return permission in getattr(app.settings.roles, identity.role)
