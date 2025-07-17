from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import PasApp
from onegov.pas.collections import ChangeCollection
from onegov.pas.layouts import ChangeCollectionLayout
from onegov.pas.layouts import ChangeLayout
from onegov.pas.models import Change

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

    return {
        'layout': layout,
        'changes': self.query().all(),
        'title': layout.title,
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
