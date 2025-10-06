from __future__ import annotations

import logging
from onegov.pas.app import PasApp
from onegov.pas.importer.orchestrator import KubImporter
from onegov.pas.log import CompositeOutputHandler, LogOutputHandler
from onegov.pas.importer.output_handlers import DatabaseOutputHandler

from typing import Any, TYPE_CHECKING, cast
if TYPE_CHECKING:
    from onegov.pas.app import PasApp as PasAppType
    from onegov.pas.request import PasRequest

log = logging.getLogger('onegov.pas.cronjobs')


@PasApp.cronjob(hour='*', minute=0, timezone='UTC')
def hourly_kub_data_import(request: PasRequest) -> None:

    try:
        trigger_kub_data_import(request, import_type='automatic')
    except ValueError as e:
        log.warning(f'KUB import skipped: {e}')
    except Exception:
        log.exception('KUB import failed')
        raise


def trigger_kub_data_import(
    request: PasRequest, import_type: str
) -> dict[str, Any] | None:
    app = request.app
    # FIXME: this is a bit crude, this will have to be
    # a conditional statement in puppet
    if not (kub_token := getattr(app, 'kub_test_api_token', None)):
        if not (kub_token := getattr(app, 'kub_api_token', None)):
            return None

    if not (kub_base_url := getattr(app, 'kub_test_base_url', None)):
        if not (kub_base_url := getattr(app, 'kub_base_url', None)):
            raise ValueError('KUB base URL not configured')

    db_handler = DatabaseOutputHandler()
    log_handler = LogOutputHandler()
    output_handler = CompositeOutputHandler(db_handler, log_handler)

    with KubImporter(kub_token, kub_base_url, output_handler) as importer:
        combined_results, import_log_id = importer.run_full_sync(
            request, cast('PasAppType', app), import_type
        )

    # Return results for UI display (if applicable)
    return {
        'import_results': combined_results.get('import', {}),
        'custom_results': combined_results.get('custom_data'),
        'import_log_id': import_log_id
    }
