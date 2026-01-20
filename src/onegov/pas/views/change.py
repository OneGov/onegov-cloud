from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import PasApp
from onegov.pas.collections import ChangeCollection
from onegov.pas.layouts import ChangeCollectionLayout
from onegov.pas.layouts import ChangeLayout
from onegov.pas.models import Change
from onegov.pas.models.commission import PASCommission
from onegov.pas.models.parliamentarian import PASParliamentarian


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@PasApp.html(
    model=ChangeCollection,
    template='changes.pt',
    permission=Private
)
def view_changes(
    self: ChangeCollection,
    request: TownRequest
) -> RenderData:

    layout = ChangeCollectionLayout(self, request)
    changes = self.query().all()

    parliamentarian_ids = {
        pid for change in changes
        if change.changes and (pid := change.changes.get('parliamentarian_id'))
    }
    parliamentarians = {}
    if parliamentarian_ids:
        query = request.session.query(PASParliamentarian).filter(
            PASParliamentarian.id.in_(parliamentarian_ids)
        )
        parliamentarians = {str(p.id): p for p in query}

    commission_ids = {
        cid for change in changes
        if change.changes and (cid := change.changes.get('commission_id'))
    }
    commissions = {}
    if commission_ids:
        commission_query = request.session.query(PASCommission).filter(
            PASCommission.id.in_(commission_ids)
        )
        commissions = {str(c.id): c for c in commission_query}

    return {
        'layout': layout,
        'changes': changes,
        'title': layout.title,
        'parliamentarians': parliamentarians,
        'commissions': commissions,
    }


@PasApp.html(
    model=Change,
    template='change.pt',
    permission=Private
)
def view_change(
    self: Change,
    request: TownRequest
) -> RenderData:

    layout = ChangeLayout(self, request)

    return {
        'layout': layout,
        'change': self,
        'title': layout.title,
    }
