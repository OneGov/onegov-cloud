from __future__ import annotations

import click
import transaction
import logging
import warnings
from datetime import date
from onegov.core.cli import command_group
from onegov.org.mail import send_transactional_html_mail
from onegov.pas import _
from onegov.pas.collections.parliamentarian import PASParliamentarianCollection
from onegov.pas.models import Attendence
from onegov.pas.excel_header_constants import (
    commission_expected_headers_variant_1,
    commission_expected_headers_variant_2,
)
from onegov.pas.data_import import import_commissions_excel
from onegov.pas.log import ClickOutputHandler, CompositeOutputHandler
from onegov.pas.importer.output_handlers import DatabaseOutputHandler
from onegov.pas.importer.orchestrator import (
    KubImporter
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.pas.app import PasApp
    from onegov.pas.request import PasRequest

    type Processor = Callable[[PasRequest, PasApp], None]


log = logging.getLogger('onegov.org.cli')

cli = command_group()

# Try to suppress Fontconfig error messages
warnings.filterwarnings('ignore', message='.*Fontconfig error.*')
warnings.filterwarnings('ignore', message='.*No writable cache directories.*')


@cli.command('import-commission-data')
@click.argument('excel_file', type=click.Path(exists=True))
def import_commission_data(
    excel_file: str,
) -> Processor:
    """
    Note: This is deprecated, not really used, as we have the JSON import.

    Import commission data from an Excel or csv file.

    Assumes that the name of the commission is the filename.

    Each row of this import contains a single line, which is a single
    parliamentarian and all the information about them.

    Example:
        onegov-pas --select '/onegov_pas/zug' import-commission-data \
            "Kommission_Gesundheit_und_Soziales.xlsx"
    """

    def import_data(request: PasRequest, app: PasApp) -> None:

        try:
            import_commissions_excel(
                excel_file,
                request.session,
                excel_file,
                expected_headers=commission_expected_headers_variant_1,
            )
            click.echo('Ok.')
        except Exception:
            click.echo('Trying the other variant of headers...')
            import_commissions_excel(
                excel_file,
                request.session,
                excel_file,
                expected_headers=commission_expected_headers_variant_2,
            )
            click.echo('Ok.')

    return import_data


@cli.command(name='update-accounts', context_settings={'singular': True})
@click.option('--dry-run/-no-dry-run', default=False)
def update_accounts_cli(dry_run: bool) -> Processor:
    """ Updates user accounts for parliamentarians. """

    def do_update_accounts(request: PasRequest, app: PasApp) -> None:

        parliamentarians = PASParliamentarianCollection(app)
        for parliamentarian in parliamentarians.query():
            if not parliamentarian.zg_username:
                click.echo(
                    f'Skipping {parliamentarian.title}, no zg_username.'
                )
                continue
            parliamentarians.update_user(
                parliamentarian, parliamentarian.zg_username
            )

        if dry_run:
            transaction.abort()

    return do_update_accounts


@cli.command(name='update-account-single', context_settings={'singular': True})
@click.option(
    '--username', required=True, help='zg_username of the parliamentarian'
)
@click.option('--dry-run/-no-dry-run', default=False)
def update_account_single_cli(username: str, dry_run: bool) -> Processor:
    """Updates user account for a single parliamentarian."""

    def do_update_account(request: PasRequest, app: PasApp) -> None:
        from onegov.pas.models import PASParliamentarian

        parliamentarians = PASParliamentarianCollection(app)
        parliamentarian = (
            parliamentarians.query()
            .filter(PASParliamentarian.zg_username == username)
            .first()
        )

        if not parliamentarian:
            click.secho(f'No parliamentarian found: {username}', fg='red')
            transaction.abort()
            return

        parliamentarians.update_user(
            parliamentarian, parliamentarian.zg_username
        )
        click.secho(f'Updated account for: {username}', fg='green')

        if dry_run:
            transaction.abort()
            click.secho('Dry run - changes aborted', fg='yellow')

    return do_update_account


@cli.command('test-abschluss-mail')
@click.option(
    '--to', 'recipient', required=True, help='Recipient email address'
)
def test_abschluss_mail(recipient: str) -> Processor:
    """Send a sample abschluss notification email for visual inspection.

    Queues the mail. Flush via:
        onegov-core sendmail --queue local_smtp
    Inspect in smtp4dev UI.

    Example:
        onegov-pas --select '/onegov_pas/zug' test-abschluss-mail \
            --to dev@example.org
    """

    def send(request: PasRequest, app: PasApp) -> None:
        attendence = request.session.query(Attendence).first()
        if attendence is None:
            click.secho(
                'No Attendence in DB - need at least one for model ref.',
                fg='red',
            )
            return

        today = date.today()
        send_transactional_html_mail(
            request=request,
            template='mail_abschluss_notification.pt',
            subject=_(
                'PAS: Abschluss set for ${name}',
                mapping={'name': 'Max Muster (TEST)'},
            ),
            receivers=[recipient],
            content={
                'model': attendence,
                'title': request.translate(_('Abschluss Notification')),
                'parliamentarian_name': 'Max Muster (TEST)',
                'commission_name': 'Test Kommission',
                'attendance_date': today,
                'user_name': 'CLI Tester',
                'settlement_run_name': 'TEST-RUN',
                'settlement_run_start': today,
                'settlement_run_end': today,
            },
        )
        click.secho(f'Mail queued for {recipient}.', fg='green')
        click.echo(
            'Flush queue:  onegov-core sendmail --queue local_smtp\n'
            'Inspect:      http://localhost:5000 (smtp4dev UI)'
        )

    return send


@cli.command('import-kub-data')
@click.option('--token', required=True,
              help='Authorization token for KUB API')
@click.option('--base-url',
              help='Base URL for the KUB API, ending in /api/v2')
@click.option('--cert-dir', required=True,
              type=click.Path(exists=True, file_okay=False),
              help='Directory containing .crt and .key files')
@click.option('--update-custom/--no-update-custom', default=True,
              help='Update parliamentarians with custom field data '
                   'after import (default: enabled)')
@click.option('--max-workers', default=3, type=int,
              help='Maximum number of concurrent workers for '
                   'custom data update (default: 3)')
def import_kub_data(
    token: str,
    base_url: str,
    cert_dir: str,
    update_custom: bool,
    max_workers: int,
) -> Processor:
    """
    Import data from the KUB API endpoints.

    Fetches data from /people, /organizations, and /memberships endpoints
    and imports them using the existing import logic. Optionally updates
    parliamentarians with custom field data from individual API calls using
    multi-threaded processing for improved performance.

    Example:
        onegov-pas --select '/onegov_pas/zug' import-kub-data \
            --token "your-token-here"

        # Skip custom data update:
        onegov-pas --select '/onegov_pas/zug' import-kub-data \
            --token "your-token-here" --no-update-custom

        # Use more workers for faster custom data processing:
        onegov-pas --select '/onegov_pas/zug' import-kub-data \
            --token "your-token-here" --max-workers 5
    """

    def cli_wrapper(request: PasRequest, app: PasApp) -> None:
        """CLI wrapper that calls the orchestrator."""
        # Create composite output handler for both CLI and database
        click_handler = ClickOutputHandler()
        db_handler = DatabaseOutputHandler()
        output_handler = CompositeOutputHandler(click_handler, db_handler)

        from onegov.pas.cronjobs import _resolve_cert
        cert = _resolve_cert(cert_dir)

        try:
            with KubImporter(
                token, base_url, output_handler, cert=cert
            ) as importer:
                combined_results, import_log_id = importer.run_full_sync(
                    request, app, 'cli', update_custom, max_workers
                )

            # Display summary
            import_results = combined_results.get('import', {})
            custom_results = combined_results.get('custom_data')

            click_handler.info('Import Results Summary:')
            for category, details in import_results.items():
                created_count = len(details.get('created', []))
                updated_count = len(details.get('updated', []))
                processed_count = details.get('processed', 0)

                if (created_count > 0 or updated_count > 0
                        or processed_count > 0):
                    click_handler.info(
                        f'  {category}: {created_count} created, '
                        f'{updated_count} updated, {processed_count} processed'
                    )

            if custom_results and 'error' not in custom_results:
                click_handler.success(
                    f'Custom data update: {custom_results["updated"]} '
                    f'updated, {custom_results["errors"]} errors'
                )

            click_handler.success(f'Import log ID: {import_log_id}')

        except Exception as e:
            click_handler.error(f'Import failed: {e}')
            raise

    return cli_wrapper


@cli.command('update-custom-data')
@click.option('--token', required=True,
              help='Authorization token for KUB API')
@click.option('--base-url', required=True,
              help='Base URL for the KUB API, ending in /api/v2')
@click.option('--cert-dir', required=True,
              type=click.Path(exists=True, file_okay=False),
              help='Directory containing .crt and .key files')
@click.option('--max-workers', default=3, type=int,
              help='Maximum number of concurrent workers '
                   '(default: 3)')
def update_custom_data(
    token: str,
    base_url: str,
    cert_dir: str,
    max_workers: int,
) -> Processor:
    """
    Update parliamentarians with customFields data which
    somehow is not included in the main /people api.
    Needs to be run after import_kub_data

    Uses multi-threading to fetch custom data concurrently from the API
    while maintaining thread-safe database operations.

    Example:
        onegov-pas --select '/onegov_pas/zug' update-custom-data \
            --token "your-token-here" \
            --base-url "url-ending-in/api/v2"

        # Use more workers for faster processing:
        onegov-pas --select '/onegov_pas/zug' update-custom-data \
            --token "your-token-here" \
            --base-url "url-ending-in/api/v2" \
            --max-workers 5
    """

    def update_data(request: PasRequest, app: PasApp) -> None:
        # Create composite output handler for both CLI and database
        click_handler = ClickOutputHandler()
        db_handler = DatabaseOutputHandler()
        output_handler = CompositeOutputHandler(click_handler, db_handler)

        from onegov.pas.cronjobs import _resolve_cert
        cert = _resolve_cert(cert_dir)

        try:
            with KubImporter(
                token, base_url, output_handler, cert=cert
            ) as importer:
                updated_count, error_count, _output_messages = (
                    importer.update_custom_data(
                        request, app, max_workers
                    )
                )
                click_handler.success(
                    f'Update completed: {updated_count} updated, '
                    f'{error_count} errors'
                )
        except Exception as e:
            click_handler.error(f'Custom data update failed: {e}')
            raise

    return update_data
