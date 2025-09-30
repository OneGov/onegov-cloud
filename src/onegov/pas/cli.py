from __future__ import annotations

import click
import transaction
import logging
import requests
import urllib3
import warnings
from onegov.core.cli import command_group
from onegov.pas.collections.parliamentarian import PASParliamentarianCollection
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
    from typing import TypeAlias

    Processor: TypeAlias = Callable[[PasRequest, PasApp], None]


log = logging.getLogger('onegov.org.cli')

cli = command_group()

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
            if not parliamentarian.email_primary:
                click.echo(
                    f'Skipping {parliamentarian.title}, no primary email.'
                )
                continue
            parliamentarians.update_user(
                parliamentarian, parliamentarian.email_primary
            )

        if dry_run:
            transaction.abort()

    return do_update_accounts


@cli.command('check-api')
@click.option('--url', default='',
              help='API endpoint to check')
@click.option('--token', default='', help='Authorization token')
def check_api(url: str, token: str) -> None:
    """ Check if the KuB API is reachable.

    Example:
        onegov-pas check-api --token "your-token-here"
    """
    # Disable SSL warnings (self signed)
    urllib3.disable_warnings(
        urllib3.exceptions.InsecureRequestWarning)
    headers = {
        'Authorization': f'Token {token}',
        'Accept': 'application/json'
    }

    try:
        response = requests.get(
            url, headers=headers, verify=False, timeout=10  # nosec: B501
        )
        click.echo(f'Status Code: {response.status_code}')
        click.echo(f'Response: {response.text}')

        if response.status_code == 200:
            click.echo('✓ API is reachable')
        else:
            click.echo('✗ API returned non-200 status')

    except requests.exceptions.RequestException as e:
        click.echo(f'✗ Failed to reach API: {e}')


@cli.command('import-kub-data')
@click.option('--token', required=True, help='Authorization token for KUB API')
@click.option('--base-url', help='Base URL for the KUB API, ending in /api/v2')
@click.option('--update-custom/--no-update-custom', default=True,
              help='Update parliamentarians with custom field data after '
                   'import (default: enabled)')
@click.option('--max-workers', default=3, type=int,
              help='Maximum number of concurrent workers for custom data '
                   'update (default: 3)')
def import_kub_data(
    token: str, base_url: str, update_custom: bool, max_workers: int
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

        try:
            with KubImporter(token, base_url, output_handler) as importer:
                combined_results, import_log_id = importer.run_full_sync(
                    request, app, update_custom, max_workers
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
@click.option('--token', required=True, help='Authorization token for KUB API')
@click.option('--base-url', required=True,
              help='Base URL for the KUB API, ending in /api/v2')
@click.option('--max-workers', default=3, type=int,
              help='Maximum number of concurrent workers (default: 3)')
def update_custom_data(
    token: str, base_url: str, max_workers: int
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

        try:
            with KubImporter(token, base_url, output_handler) as importer:
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
