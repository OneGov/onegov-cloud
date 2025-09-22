from __future__ import annotations

import logging
from onegov.pas.app import PasApp
from onegov.pas.importer.orchestrator import KubImporter
from onegov.pas.log import CompositeOutputHandler
from onegov.pas.importer.output_handlers import (
    DatabaseOutputHandler,
    LogOutputHandler
)

from typing import Any, TYPE_CHECKING, cast
if TYPE_CHECKING:
    from onegov.pas.app import PasApp as PasAppType
    from onegov.town6.request import TownRequest

log = logging.getLogger('onegov.pas.cronjobs')


@PasApp.cronjob(hour='*', minute=0, timezone='UTC')
def hourly_kub_data_import(request: TownRequest) -> None:
    """
    Hourly KUB data import cronjob.

    Imports data from KUB API using the token from configuration.
    Runs every hour on the hour.
    """
    kub_token = getattr(request.app, 'kub_token', None)
    if not kub_token:
        log.warning('KUB token not configured - skipping import')
        return

    log.info('Starting hourly KUB data import')

    try:
        trigger_kub_data_import(request)
        log.info('KUB import completed')
    except ValueError as e:
        log.warning(f'KUB import skipped: {e}')
    except Exception:
        log.exception('KUB import failed')
        raise


def trigger_kub_data_import(request: TownRequest) -> dict[str, Any]:
    app = request.app
    kub_token = getattr(app, 'kub_test_api_token', None)
    if not kub_token:
        kub_token = getattr(app, 'kub_api_token', None)
    if not kub_token:
        raise ValueError('KUB token not configured')
    kub_base_url = getattr(app, 'kub_test_base_url', None)
    if not kub_base_url:
        kub_base_url = getattr(app, 'kub_base_url', None)
    if not kub_base_url:
        raise ValueError('KUB base URL not configured')
    # FIXME: this is a bit crude, this will have to add
    # a conditional statement in puppet

    log.info('Starting KUB data import')

    db_handler = DatabaseOutputHandler()
    log_handler = LogOutputHandler(log)
    output_handler = CompositeOutputHandler(db_handler, log_handler)

    with KubImporter(kub_token, kub_base_url, output_handler) as importer:
        combined_results, import_log_id = importer.run_full_sync(
            request, cast('PasAppType', app), update_custom=True, max_workers=3
        )

    # Return results for UI display (if applicable)
    return {
        'import_results': combined_results.get('import', {}),
        'custom_results': combined_results.get('custom_data'),
        'import_log_id': import_log_id
    }
