from __future__ import annotations

import click
import logging
import requests
import json
import urllib3
import threading
import queue
import warnings
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse
from onegov.core.cli import command_group
from onegov.pas.excel_header_constants import (
    commission_expected_headers_variant_1,
    commission_expected_headers_variant_2,
)
from onegov.pas.data_import import import_commissions_excel
from onegov.pas.views.data_import import load_and_concatenate_json
from onegov.pas.importer.zug_kub_importer import import_zug_kub_data
from onegov.pas.collections.import_log import ImportLogCollection
from onegov.core.utils import binary_to_dictionary
from onegov.pas.log import ClickOutputHandler
from onegov.pas.log import OutputHandler


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from onegov.core.types import LaxFileDict
    from collections.abc import Callable
    from onegov.pas.app import PasApp
    from onegov.pas.app import TownRequest
    from typing import TypeAlias

    Processor: TypeAlias = Callable[[TownRequest, PasApp], None]


log = logging.getLogger('onegov.org.cli')

cli = command_group()

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Suppress Fontconfig error messages
warnings.filterwarnings('ignore', message='.*Fontconfig error.*')
warnings.filterwarnings('ignore', message='.*No writable cache directories.*')


@dataclass
class UpdateResult:
    parliamentarian_id: str
    title: str
    custom_values: dict[str, str]
    error: str | None = None


def _fetch_custom_data_worker(
    parliamentarian_queue: queue.Queue[Any],
    result_queue: queue.Queue[UpdateResult],
    token: str,
    base_url: str
) -> None:
    """Worker thread that fetches API data for parliamentarians."""
    headers = {
        'Authorization': f'Token {token}',
        'Accept': 'application/json'
    }

    while True:
        try:
            parliamentarian = parliamentarian_queue.get_nowait()
        except queue.Empty:
            break

        try:
            person_id = parliamentarian.external_kub_id
            url = f'{base_url}/people/{person_id}'

            response = requests.get(
                url, headers=headers, verify=False, timeout=30  # nosec: B501
            )
            response.raise_for_status()

            person_data = response.json()
            custom_values = person_data.get('customValues', {})

            result_queue.put(UpdateResult(
                parliamentarian_id=parliamentarian.id,
                title=parliamentarian.title,
                custom_values=custom_values
            ))
        except Exception as e:
            result_queue.put(UpdateResult(
                parliamentarian_id=parliamentarian.id,
                title=parliamentarian.title,
                custom_values={},
                error=str(e)
            ))
        finally:
            parliamentarian_queue.task_done()


@cli.command('import-commission-data')
@click.argument('excel_file', type=click.Path(exists=True))
def import_commission_data(
    excel_file: str,
) -> Processor:
    """Import commission data from an Excel or csv file.

    Assumes that the name of the commission is the filename.

    Each row of this import contains a single line, which is a single
    parliamentarian and all the information about them.

    Example:
        onegov-pas --select '/onegov_pas/zug' import-commission-data \
            "Kommission_Gesundheit_und_Soziales.xlsx"
    """

    def import_data(request: TownRequest, app: PasApp) -> None:

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


def fetch_api_data_with_pagination(
    endpoint: str, token: str, base_url: str
) -> list[dict[str, Any]]:
    """
    Fetches all data from a paginated API endpoint.

    Args:
        endpoint: The API endpoint (e.g., 'people', 'organizations',
                  'memberships')
        token: Authorization token
        base_url: Base URL for the API (should not end with slash)

    Returns:
        List of all records from all pages
    """

    # Normalize base URL - remove trailing slash for consistent construction
    base_url = base_url.rstrip('/')

    # Disable SSL warnings (self signed)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    headers = {
        'Authorization': f'Token {token}',
        'Accept': 'application/json'
    }

    all_results = []
    url: str | None = f'{base_url}/{endpoint}'

    # Parse base URL to get correct hostname/scheme for pagination URL fixes
    # This is necessary because we use a bridge to access the API and need
    # to dynamically swap the hostname at runtime for pagination URLs
    base_parsed = urlparse(base_url)

    while url:
        try:
            response = requests.get(
                url, headers=headers, verify=False, timeout=30  # nosec: B501
            )
            response.raise_for_status()

            data = response.json()
            results = data.get('results', [])
            all_results.extend(results)

            # Handle pagination: API returns 'next' URLs with bridge hostname
            # We need to dynamically swap the hostname with our runtime host
            # from base_url to ensure subsequent requests use correct bridge
            next_url = data.get('next')
            if next_url:
                next_parsed = urlparse(next_url)
                # Reconstruct URL with correct bridge hostname from base_url
                # but keeping path, query parameters, etc. from API's next URL
                url = urlunparse((
                    base_parsed.scheme,      # Use scheme from base_url (https)
                    base_parsed.netloc,      # Use bridge hostname
                    next_parsed.path,        # Keep path (/api/v2/people)
                    next_parsed.params,      # Keep URL parameters
                    next_parsed.query,       # Keep query string (page=2, etc.)
                    next_parsed.fragment     # Keep fragment (usually empty)
                ))
            else:
                url = None

        except requests.exceptions.RequestException as e:
            raise click.ClickException(
                f'Failed to fetch from {endpoint}: {e}'
            ) from e
        except ValueError as e:
            raise click.ClickException(
                f'Invalid JSON response from {endpoint}: {e}'
            ) from e

    return all_results


def create_mock_file_data(
    data: list[dict[str, Any]], filename: str
) -> LaxFileDict:
    json_content = {'results': data}
    json_str = json.dumps(json_content, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    file_dict = binary_to_dictionary(json_bytes, filename)
    return file_dict  # type: ignore[return-value]


def perform_custom_data_update(
    request: TownRequest,
    app: PasApp,
    token: str,
    base_url: str,
    output: OutputHandler | None = None,
    max_workers: int = 3
) -> tuple[int, int]:
    """
    Multi-threaded function that updates parliamentarians with custom field
    data.

    Uses a queue-based approach where worker threads fetch API data
    concurrently while the main thread handles all database updates to
    maintain thread safety.

    Args:
        request: TownRequest object
        app: PasApp object
        token: Authorization token for KUB API
        base_url: Base URL for the KUB API
        output: Optional output handler for progress messages
        max_workers: Maximum number of concurrent API worker threads
            (default: 3)

    Returns:
        Tuple of (updated_count, error_count)
    """
    from onegov.parliament.models import Parliamentarian

    field_mappings = {
        'personalnummer': 'personnel_number',
        'vertragsnummer': 'contract_number',
        'wahlkreis': 'district',
        'beruf': 'occupation',
        'adress_anrede': 'salutation_for_address',
        'brief_anrede': 'salutation_for_letter'
    }

    # Get all parliamentarians (single DB query)
    all_parliamentarians = request.session.query(Parliamentarian).all()

    # Separate parliamentarians with and without external_kub_id
    parliamentarians_with_id = [
        p for p in all_parliamentarians if p.external_kub_id is not None
    ]
    parliamentarians_without_id = [
        p for p in all_parliamentarians if p.external_kub_id is None
    ]

    # Log warning if parliamentarians without external_kub_id exist
    if parliamentarians_without_id:
        missing_names = [p.title for p in parliamentarians_without_id]
        warning_msg = (
            f'Warning: {len(parliamentarians_without_id)} parliamentarians '
            f'found without external_kub_id: {", ".join(missing_names)}. '
            f'These will not be synchronized.'
        )
        if output:
            output.error(warning_msg)
        log.warning(
            f'Found {len(parliamentarians_without_id)} parliamentarians '
            f'without external_kub_id: {missing_names}. '
            f'These will not be synchronized.'
        )

    if not parliamentarians_with_id:
        if output:
            output.info('No parliamentarians with external_kub_id found')
        return 0, 0

    # Use only parliamentarians with external_kub_id for processing
    parliamentarians = parliamentarians_with_id

    if output:
        output.info(
            f'Found {len(parliamentarians)} parliamentarians to update '
            f'with custom data using {max_workers} workers'
        )

    # Set up queues for thread communication
    parliamentarian_queue: queue.Queue[Any] = queue.Queue()
    result_queue: queue.Queue[UpdateResult] = queue.Queue()

    # Fill work queue with parliamentarians
    for p in parliamentarians:
        parliamentarian_queue.put(p)

    # Start worker threads (API fetching only)
    threads = []
    for i in range(max_workers):
        t = threading.Thread(
            target=_fetch_custom_data_worker,
            args=(parliamentarian_queue, result_queue, token, base_url)
        )
        t.start()
        threads.append(t)

    # Main thread handles all DB updates (single session, thread-safe)
    updated_count = 0
    error_count = 0
    processed = 0

    # Process results as they come in from worker threads
    while processed < len(parliamentarians):
        try:
            # Wait for next result with timeout
            result = result_queue.get(timeout=120)  # 2 min timeout
            processed += 1

            if result.error:
                error_count += 1
                if output:
                    output.error(
                        f'✗ Failed to fetch {result.title}: {result.error}'
                    )
            else:
                # Update parliamentarian in main thread's session
                parliamentarian = request.session.query(
                    Parliamentarian).filter(
                    Parliamentarian.id == result.parliamentarian_id
                ).first()

                if parliamentarian:
                    updated_fields = []
                    for custom_key, attr_name in field_mappings.items():
                        if custom_key in result.custom_values:
                            setattr(
                                parliamentarian, attr_name,
                                result.custom_values[custom_key]
                            )
                            updated_fields.append(attr_name)

                    if updated_fields:
                        updated_count += 1
                        if output:
                            output.success(
                                f'✓ Updated {result.title}: '
                                f'{", ".join(updated_fields)}'
                            )
                    else:
                        if output:
                            output.info(
                                f'No custom data found for {result.title}'
                            )

            result_queue.task_done()

        except queue.Empty:
            if output:
                output.error('Timeout waiting for API results')
            error_count += (len(parliamentarians) - processed)
            break

    # Wait for all worker threads to complete
    for t in threads:
        t.join(timeout=10)  # Give threads 10s to finish up

    return updated_count, error_count


def perform_kub_import(
    request: TownRequest,
    app: PasApp,
    token: str,
    base_url: str,
    output: OutputHandler | None = None
) -> tuple[dict[str, Any], list[Any], list[Any], list[Any]]:
    """
    Reusable function that performs KUB data import.

    Args:
        request: TownRequest object
        app: PasApp object
        token: Authorization token for KUB API
        base_url: Base URL for the KUB API
        output: Optional output handler for progress messages

    Returns:
        Tuple of (import_results, people_data, organization_data,
                  membership_data)
    """

    try:
        if output:
            output.info('Checking API accessibility...')

        # Check API accessibility
        headers = {
            'Authorization': f'Token {token}',
            'Accept': 'application/json'
        }
        test_url = f'{base_url}/people'

        try:
            response = requests.get(
                test_url, headers=headers, verify=False, timeout=10  # nosec: B501
            )
            if response.status_code != 200:
                raise RuntimeError(
                    f'API check failed: {response.status_code} - '
                    f'{response.text}'
                )
            if output:
                output.success('API is accessible')
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f'API check failed: {e}') from e

        if output:
            output.info('Fetching people data...')
        people_raw = fetch_api_data_with_pagination('people', token, base_url)
        if output:
            output.success(f'Fetched {len(people_raw)} people records')

        if output:
            output.info('Fetching organizations data...')
        organizations_raw = fetch_api_data_with_pagination(
            'organizations', token, base_url
        )
        if output:
            output.success(
                f'Fetched {len(organizations_raw)} organization records'
            )

        if output:
            output.info('Fetching memberships data...')
        memberships_raw = fetch_api_data_with_pagination(
            'memberships', token, base_url
        )
        if output:
            output.success(
                f'Fetched {len(memberships_raw)} membership records'
            )

        # Create mock file data structures for load_and_concatenate_json
        people_mock_files = [create_mock_file_data(people_raw, 'people.json')]
        organizations_mock_files = [
            create_mock_file_data(organizations_raw, 'organizations.json')
        ]
        memberships_mock_files = [
            create_mock_file_data(memberships_raw, 'memberships.json')
        ]

        # Use load_and_concatenate_json to process the data
        if output:
            output.info('Processing people data...')
        people_data = load_and_concatenate_json(people_mock_files)
        if output:
            output.info('Processing organizations data...')
        organization_data = load_and_concatenate_json(organizations_mock_files)
        if output:
            output.info('Processing memberships data...')
        membership_data = load_and_concatenate_json(memberships_mock_files)

        # Perform the import
        if output:
            output.info('Starting data import...')
        import_results = import_zug_kub_data(
            session=request.session,
            people_data=people_data,
            organization_data=organization_data,
            membership_data=membership_data,
            user_id=request.current_user.id if request.current_user else None
        )

        # Display results
        if output:
            total_created = 0
            total_updated = 0
            total_processed = 0

            for category, details in import_results.items():
                created_count = len(details.get('created', []))
                updated_count = len(details.get('updated', []))
                processed_count = details.get('processed', 0)

                total_created += created_count
                total_updated += updated_count
                total_processed += processed_count

                if (created_count > 0 or updated_count > 0 or
                        processed_count > 0):
                    output.info(
                        f'{category}: {created_count} created, '
                        f'{updated_count} updated, {processed_count} processed'
                    )

            output.success(
                f'Import completed successfully! '
                f'Total: {total_created} created, {total_updated} updated, '
                f'{total_processed} processed'
            )

        return import_results, people_data, organization_data, membership_data

    except Exception as e:
        if output:
            output.error(f'Import failed: {e}')
        raise


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

    def cli_wrapper(request: TownRequest, app: PasApp) -> None:
        """CLI wrapper that calls the reusable import function."""
        output_handler = ClickOutputHandler()

        try:
            import_results, people_data, organization_data, membership_data = (
                perform_kub_import(
                    request, app, token, base_url, output_handler
                )
            )

            # Add the concatenated data to the most recent ImportLog entry
            output_handler.info('Saving concatenated data to import log...')
            import_log_collection = ImportLogCollection(request.session)
            most_recent_log = (
                import_log_collection.most_recent_completed_cli_import()
            )

            if most_recent_log:
                most_recent_log.people_source = people_data
                most_recent_log.organizations_source = organization_data
                most_recent_log.memberships_source = membership_data
                request.session.flush()
                output_handler.success('Concatenated data saved to import log')

            # Display detailed import results
            output_handler.info('Import Results Summary:')
            for category, details in import_results.items():
                created_count = len(details.get('created', []))
                updated_count = len(details.get('updated', []))
                processed_count = details.get('processed', 0)

                if (created_count > 0 or updated_count > 0
                        or processed_count > 0):
                    output_handler.info(
                        f'  {category}: {created_count} created, '
                        f'{updated_count} updated, {processed_count} processed'
                    )

            # Update parliamentarians with custom data if requested
            if update_custom:
                output_handler.info('Starting custom data update...')
                try:
                    custom_updated, custom_errors = perform_custom_data_update(
                        request, app, token, base_url, output_handler,
                        max_workers
                    )
                    output_handler.success(
                        f'Custom data update completed: {custom_updated} '
                        f'updated, {custom_errors} errors'
                    )
                except Exception as e:
                    output_handler.error(f'Custom data update failed: {e}')
                    raise
            else:
                output_handler.info(
                    'Skipping custom data update (--no-update-custom)'
                )

        except Exception as e:
            output_handler.error(f'Import failed: {e}')
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

    def update_data(request: TownRequest, app: PasApp) -> None:
        output_handler = ClickOutputHandler()

        try:
            updated_count, error_count = perform_custom_data_update(
                request, app, token, base_url, output_handler, max_workers
            )
            output_handler.success(
                f'Update completed: {updated_count} updated, '
                f'{error_count} errors'
            )
        except Exception as e:
            output_handler.error(f'Custom data update failed: {e}')
            raise

    return update_data
