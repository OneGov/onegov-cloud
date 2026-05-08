from __future__ import annotations

import glob
import logging
from onegov.pas.app import PasApp
from onegov.pas.collections.parliamentarian import (
    PASParliamentarianCollection,
)
from onegov.pas.importer.orchestrator import KubImporter
from onegov.pas.log import CompositeOutputHandler, LogOutputHandler
from onegov.pas.importer.output_handlers import DatabaseOutputHandler
from onegov.pas.models import ImportLog
from sqlalchemy.orm.attributes import flag_modified

from typing import Any, TYPE_CHECKING, cast
if TYPE_CHECKING:
    from onegov.pas.app import PasApp as PasAppType
    from onegov.pas.request import PasRequest

log = logging.getLogger('onegov.pas.cronjobs')


def _resolve_cert(cert_dir: str) -> tuple[str, str]:
    crt = glob.glob(f'{cert_dir}/*.crt')
    key = glob.glob(f'{cert_dir}/*.key')
    if len(crt) != 1 or len(key) != 1:
        raise FileNotFoundError(
            f'Expected exactly one .crt and one .key in {cert_dir}, '
            f'found {len(crt)} .crt and {len(key)} .key'
        )
    return crt[0], key[0]


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
    if not (kub_token := getattr(app, 'kub_api_token', None)):
        return None

    if not (kub_base_url := getattr(app, 'kub_base_url', None)):
        return None

    cert_dir = getattr(app, 'kub_cert_dir', None)
    if not cert_dir:
        return None
    cert = _resolve_cert(cert_dir)

    db_handler = DatabaseOutputHandler()
    log_handler = LogOutputHandler()
    output_handler = CompositeOutputHandler(db_handler, log_handler)

    with KubImporter(
        kub_token, kub_base_url, output_handler, cert=cert
    ) as importer:
        combined_results, import_log_id = importer.run_full_sync(
            request, cast('PasAppType', app), import_type
        )

    # Sync user accounts right after import
    collection = PASParliamentarianCollection(app)
    sync_result = collection.sync_user_accounts()
    combined_results['user_sync'] = sync_result

    log.info(
        f'User account sync: {sync_result["synced"]} synced, '
        f'{sync_result["skipped"]} skipped'
    )
    if sync_result['created']:
        log.info(
            f'Created {len(sync_result["created"])} user '
            f'accounts: {", ".join(sync_result["created"])}'
        )

    # Store user sync results in ImportLog
    import_log = request.session.get(ImportLog, import_log_id)
    if import_log:
        import_log.details['user_sync'] = sync_result
        flag_modified(import_log, 'details')
        request.session.flush()

    return {
        'import_results': combined_results.get('import', {}),
        'custom_results': combined_results.get('custom_data'),
        'user_sync': sync_result,
        'import_log_id': import_log_id
    }
