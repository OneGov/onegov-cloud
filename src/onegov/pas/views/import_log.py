from __future__ import annotations

import json
from onegov.core.security import Private
from morepath import redirect
from onegov.pas import PasApp, _
from onegov.pas.collections import ImportLogCollection
from onegov.pas.cronjobs import trigger_kub_data_import
from onegov.pas.layouts.import_log import (
    ImportLogCollectionLayout,
    ImportLogLayout
)
from onegov.pas.models import ImportLog
from webob import Response
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from onegov.pas.request import PasRequest
    from onegov.core.types import RenderData
    from webob import Response


@PasApp.html(
    model=ImportLogCollection,
    template='import_logs.pt',
    permission=Private
)
def view_import_logs(
    self: ImportLogCollection, request: PasRequest
) -> RenderData:
    request.include('importlog')

    layout = ImportLogCollectionLayout(self, request)

    return {
        'layout': layout,
        'title': _('Import History'),
        'logs': self.for_listing().all(),
        'translate_import_type': lambda import_type: request.translate(
            _(import_type)
        )
    }


@PasApp.html(
    model=ImportLog,
    template='import_log.pt',
    permission=Private
)
def view_import_log(
    self: ImportLog, request: PasRequest
) -> RenderData:
    request.include('importlog')
    layout = ImportLogLayout(self, request)
    details_formatted = json.dumps(
        self.details, indent=2, sort_keys=True, ensure_ascii=False
    )

    details = self.details or {}
    summary = details.get('summary', {})
    output_messages = details.get('output_messages', [])

    import_categories = []
    import_results = details.get('import_results', {})
    if import_results:
        for category, stats in import_results.items():
            if category != 'total_import_summary':
                updated_count = len(stats.get('updated', []))
                created_count = len(stats.get('created', []))
                processed_count = stats.get('processed', 0)
                import_categories.append({
                    'name': category,
                    'display_text': f'Updated: {updated_count}, '
                                  f'Created: {created_count}, '
                                  f'Processed: {processed_count}'
                })

    processed_logs = []
    for log_entry in output_messages:
        if isinstance(log_entry, dict) and 'level' in log_entry:
            level = log_entry.get('level', 'info')
            message = log_entry.get('message', '')
            processed_logs.append({
                'level': level.upper(),
                'css_class': f'log-level log-{level}',
                'message': message
            })

    return {
        'layout': layout,
        'title': _('Import Log Details'),
        'log': self,
        'details_formatted': details_formatted,
        'summary': summary,
        'import_categories': import_categories,
        'processed_logs': processed_logs,
    }


@PasApp.view(
    model=ImportLogCollection,
    name='trigger-import',
    permission=Private,
    request_method='POST'
)
def trigger_import_view(
    self: ImportLogCollection, request: PasRequest
) -> Response:
    """Trigger manual KUB data import."""
    try:
        trigger_kub_data_import(request)
        request.success(_(
            'Import triggered successfully. The process may take up to 30 '
            'seconds to complete.'
        ))
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
    self: ImportLog, request: PasRequest
) -> Response:
    """Download source JSON data based on type parameter."""
    source_type = request.params.get('type')

    # Load only the specific deferred column we need
    if source_type in ('people', 'organizations', 'memberships'):
        if source_type == 'people':
            result = request.session.query(ImportLog.people_source).filter(
                ImportLog.id == self.id
            ).scalar()
            self.people_source = result
        elif source_type == 'organizations':
            result = request.session.query(
                ImportLog.organizations_source
            ).filter(ImportLog.id == self.id).scalar()
            self.organizations_source = result
        elif source_type == 'memberships':
            result = request.session.query(
                ImportLog.memberships_source
            ).filter(ImportLog.id == self.id).scalar()
            self.memberships_source = result

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
