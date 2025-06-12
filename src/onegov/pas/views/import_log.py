from __future__ import annotations

import json
from onegov.core.security import Private
from onegov.pas import PasApp, _
from onegov.pas.collections import ImportLogCollection
from onegov.pas.layouts.default import DefaultLayout
from onegov.pas.models import ImportLog
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from onegov.town6.request import TownRequest
    from onegov.core.types import RenderData


@PasApp.html(
    model=ImportLogCollection,
    template='import_logs.pt',
    permission=Private
)
def view_import_logs(
    self: ImportLogCollection, request: TownRequest
) -> RenderData:

    layout = DefaultLayout(self, request)

    return {
        'layout': layout,
        'title': _('Import History'),
        'logs': self.query().limit(50).all()
    }


@PasApp.html(
    model=ImportLog,
    template='import_log.pt',
    permission=Private
)
def view_import_log(
    self: ImportLog, request: TownRequest
) -> RenderData:

    layout = DefaultLayout(self, request)
    details_formatted = json.dumps(
        self.details, indent=2, sort_keys=True, ensure_ascii=False
    )
    return {
        'layout': layout,
        'title': _('Import Log Details'),
        'log': self,
        'details_formatted': details_formatted,
    }
