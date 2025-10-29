from __future__ import annotations

import logging
from email_validator import EmailNotValidError, validate_email
from onegov.pas.app import PasApp
from onegov.pas.collections.parliamentarian import PASParliamentarianCollection
from onegov.pas.importer.orchestrator import KubImporter
from onegov.pas.log import CompositeOutputHandler, LogOutputHandler
from onegov.pas.importer.output_handlers import DatabaseOutputHandler
from onegov.user import UserCollection

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


@PasApp.cronjob(hour='*', minute=15, timezone='UTC')
def hourly_user_account_sync(request: PasRequest) -> None:
    """Sync user accounts with parliamentarians.

    Groups parliamentarians by email and picks one representative per
    email to avoid role conflicts when the same person appears multiple
    times. Prioritizes commission presidents over regular parliamentarians.
    """

    try:
        collection = PASParliamentarianCollection(request.app)
        parliamentarians = collection.query().all()

        users = UserCollection(request.session)
        # We also need to use username.lower() to avoid potential 
        # onegov.user.errors.ExistingUserError
        users_cache = {
            user.username.lower(): user for user in users.query()
        }

        # Build a dict email_to_parl mapping each unique email to ONE
        # parliamentarian
        # If the same email appears multiple times, keep the "highest
        # priority" one
        email_to_parl: dict[str, Any] = {}
        for parl in parliamentarians:
            email = parl.email_primary
            if not email:
                continue

            email_lower = email.lower()
            if email_lower not in email_to_parl:
                email_to_parl[email_lower] = parl
            else:
                existing = email_to_parl[email_lower]
                is_president = collection._is_current_commission_president
                if is_president(parl) and not is_president(existing):
                    email_to_parl[email_lower] = parl

        synced_count = 0
        skipped_count = 0

        for email_lower, parliamentarian in email_to_parl.items():
            email = parliamentarian.email_primary

            try:
                # Note: We probably want to check deliverability,
                # but not hourly. This would need to be seperate.
                validate_email(email, check_deliverability=False)
            except EmailNotValidError as e:
                log.warning(
                    f'Skipping parliamentarian '
                    f'{parliamentarian.title} with invalid email '
                    f'{email}: {e}'
                )
                skipped_count += 1
                continue

            collection.update_user(parliamentarian, email, users_cache)
            synced_count += 1

        request.session.flush()
        log.info(
            f'User account sync completed: {synced_count} synced, '
            f'{skipped_count} skipped'
        )

    except Exception:
        log.exception('User account sync failed')
        raise
