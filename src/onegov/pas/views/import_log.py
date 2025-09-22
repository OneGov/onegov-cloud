from __future__ import annotations

import json
from onegov.core.security import Private
from morepath import redirect
from onegov.pas import PasApp, _
from onegov.pas.collections import ImportLogCollection
from onegov.pas.cronjobs import trigger_kub_data_import
from onegov.pas.layouts.default import DefaultLayout
from onegov.pas.models import ImportLog
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from onegov.town6.request import TownRequest
    from onegov.core.types import RenderData
    from webob import Response


def translate_import_type(import_type: str, request: TownRequest) -> str:
    """Translate import_type values to German."""
    translations = {
        'cli': 'Manuell auf dem Server',
        'automatic': 'Automatisch',
        'upload': 'Auf App hochgeladen'
    }
    return translations.get(import_type, import_type)


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
        'logs': self.query().limit(50).all(),
        'translate_import_type': lambda import_type: translate_import_type(
            import_type, request
        ),
        'kub_token_configured': bool(getattr(request.app, 'kub_token', None))
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


@PasApp.view(
    model=ImportLogCollection,
    name='trigger-import',
    permission=Private,
    request_method='POST'
)
def trigger_import_view(
    self: ImportLogCollection, request: TownRequest
) -> Response:
    """Trigger manual KUB data import."""
    try:
        trigger_kub_data_import(request)
        request.success(_('Import triggered successfully'))
    except ValueError as e:
        request.alert(str(e))
    except Exception as e:
        request.alert(_('Import failed: ${error}', mapping={'error': str(e)}))

    return redirect(request.link(self))
