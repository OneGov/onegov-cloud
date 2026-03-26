from __future__ import annotations

from onegov.core.security.rules import has_permission_not_logged_in
from onegov.landsgemeinde.app import LandsgemeindeApp
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import VotumCollection
from onegov.landsgemeinde.models import Assembly, AgendaItem, Votum
from onegov.landsgemeinde.models import LandsgemeindeFile


@LandsgemeindeApp.permission_rule(
    model=Assembly,
    permission=object,
    identity=None
)
@LandsgemeindeApp.permission_rule(
    model=AgendaItem,
    permission=object,
    identity=None
)
@LandsgemeindeApp.permission_rule(
    model=Votum,
    permission=object,
    identity=None
)
def has_permission_draft_not_logged_in(
    app: LandsgemeindeApp,
    identity: None,
    model: Assembly | AgendaItem | Votum,
    permission: object
) -> bool:

    if model.state == 'draft':
        return False

    return has_permission_not_logged_in(app, identity, model, permission)


@LandsgemeindeApp.permission_rule(
    model=AgendaItemCollection,
    permission=object,
    identity=None
)
def has_permission_agenda_items_draft_not_logged_in(
    app: LandsgemeindeApp,
    identity: None,
    model: AgendaItemCollection,
    permission: object
) -> bool:

    if model.assembly and model.assembly.state == 'draft':
        return False

    return has_permission_not_logged_in(app, identity, model, permission)


@LandsgemeindeApp.permission_rule(
    model=VotumCollection,
    permission=object,
    identity=None
)
def has_permission_vota_draft_not_logged_in(
    app: LandsgemeindeApp,
    identity: None,
    model: VotumCollection,
    permission: object
) -> bool:

    parent = model.agenda_item or model.assembly
    if parent and parent.state == 'draft':
        return False

    return has_permission_not_logged_in(app, identity, model, permission)


@LandsgemeindeApp.permission_rule(
    model=LandsgemeindeFile,
    permission=object,
    identity=None
)
def has_file_permission_draft_not_logged_in(
    app: LandsgemeindeApp,
    identity: None,
    model: Assembly | AgendaItem | Votum,
    permission: object
) -> bool:

    if not model.meta.get('fts_public', False):
        return False

    return has_permission_not_logged_in(app, identity, model, permission)
