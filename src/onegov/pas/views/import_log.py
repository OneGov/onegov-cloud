from __future__ import annotations

import json
from onegov.core.security import Private
from morepath import redirect
from onegov.pas import PasApp, _
from onegov.pas.collections import ImportLogCollection
from onegov.pas.cronjobs import trigger_kub_data_import
from onegov.pas.layouts.default import DefaultLayout
from onegov.pas.models import ImportLog
from webob import Response
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


@PasApp.view(
    model=ImportLog,
    name='download-source',
    permission=Private
)
def download_source_data(
    self: ImportLog, request: TownRequest
) -> Response:
    """Download source JSON data based on type parameter."""
    source_type = request.params.get('type')

    if source_type == 'people':
        if not self.people_source:
            return Response(
                status=404, text='No people source data available'
            )
        json_data = json.dumps(
            self.people_source, indent=2, ensure_ascii=False
        )
        filename = f'import-log-{self.id}-people-source.json'
    elif source_type == 'organizations':
        if not self.organizations_source:
            return Response(
                status=404, text='No organizations source data available'
            )
        json_data = json.dumps(
            self.organizations_source, indent=2, ensure_ascii=False
        )
        filename = f'import-log-{self.id}-organizations-source.json'
    elif source_type == 'memberships':
        if not self.memberships_source:
            return Response(
                status=404, text='No memberships source data available'
            )
        json_data = json.dumps(
            self.memberships_source, indent=2, ensure_ascii=False
        )
        filename = f'import-log-{self.id}-memberships-source.json'
    else:
        return Response(status=400, text='Invalid source type')

    return Response(
        body=json_data.encode('utf-8'),
        content_type='application/json; charset=utf-8',
        content_disposition=f'attachment; filename="{filename}"'
    )
