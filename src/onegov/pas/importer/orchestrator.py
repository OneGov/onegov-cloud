from __future__ import annotations

import json
import logging
import queue
import requests
import threading
import urllib3
import uuid
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

from onegov.core.utils import binary_to_dictionary
from onegov.pas.models.import_log import ImportLog
from onegov.pas.views.data_import import load_and_concatenate_json
from onegov.pas.importer.zug_kub_importer import import_zug_kub_data
from onegov.pas.importer.types import OutputLogHandler


from typing import TYPE_CHECKING, Any, Self
if TYPE_CHECKING:
    from types import TracebackType
    from onegov.core.types import LaxFileDict
    from onegov.pas.app import PasApp
    from onegov.pas.app import TownRequest
    from onegov.pas.log import OutputHandler


log = logging.getLogger('onegov.pas.orchestrator')

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class UpdateResult:
    parliamentarian_id: str
    title: str
    custom_values: dict[str, str]
    error: str | None = None


def _fetch_custom_data_worker(
    parliamentarian_queue: queue.Queue[Any],
    result_queue: queue.Queue[UpdateResult],
    session: requests.Session,
    base_url: str
) -> None:
    """Worker thread that fetches API data for parliamentarians."""
    while True:
        try:
            parliamentarian = parliamentarian_queue.get_nowait()
        except queue.Empty:
            break

        try:
            person_id = parliamentarian.external_kub_id
            url = f'{base_url}/people/{person_id}'

            response = session.get(url, timeout=30)
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


def create_mock_file_data(
    data: list[dict[str, Any]], filename: str
) -> LaxFileDict:
    json_content = {'results': data}
    json_str = json.dumps(json_content, ensure_ascii=False)
    json_bytes = json_str.encode('utf-8')
    file_dict = binary_to_dictionary(json_bytes, filename)
    return file_dict  # type: ignore[return-value]


class KubImporter:
    """
    KUB API importer that manages shared session and state for both
    data import and custom data updates.
    """

    def __init__(
        self,
        token: str,
        base_url: str,
        output: OutputHandler | None = None
    ):
        self.token = token
        self.base_url = base_url.rstrip('/')  # Normalize
        self.output = output

        # Shared requests session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Token {token}',
            'Accept': 'application/json'
        })
        # Disable SSL verification for self-signed certificates
        self.session.verify = False

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> None:
        self.session.close()

    def _check_api_accessibility(self) -> None:
        """Check if the API is accessible."""
        if self.output:
            self.output.info('Checking API accessibility...')

        test_url = f'{self.base_url}/people'
        try:
            response = self.session.get(test_url, timeout=10)
            if response.status_code != 200:
                raise RuntimeError(
                    f'API check failed: {response.status_code} - '
                    f'{response.text}'
                )
            if self.output:
                self.output.success('API is accessible')
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f'API check failed: {e}') from e

    def _fetch_api_data_with_pagination(
        self, endpoint: str
    ) -> list[dict[str, Any]]:
        """
        Fetches all data from a paginated API endpoint using the shared
        session.

        Args:
            endpoint: The API endpoint (e.g., 'people', 'organizations',
                      'memberships')

        Returns:
            List of all records from all pages
        """
        all_results = []
        url: str | None = f'{self.base_url}/{endpoint}'

        # Parse base URL to get correct hostname/scheme for pagination URL
        # fixes. This is necessary because we use a bridge to access the API
        # and need to dynamically swap the hostname at runtime for pagination
        # URLs
        base_parsed = urlparse(self.base_url)

        while url:
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                data = response.json()
                results = data.get('results', [])
                all_results.extend(results)

                next_url = data.get('next')
                if next_url:
                    next_parsed = urlparse(next_url)
                    # Reconstruct URL with correct bridge hostname from
                    # base_url but keeping path, query parameters, etc. from
                    # API's next URL
                    url = urlunparse((
                        base_parsed.scheme,      # Use scheme from base_url
                        base_parsed.netloc,      # Use bridge hostname
                        next_parsed.path,        # Keep path (/api/v2/people)
                        next_parsed.params,      # Keep URL parameters
                        next_parsed.query,       # Keep query string (page=2)
                        next_parsed.fragment     # Keep fragment (empty)
                    ))
                else:
                    url = None

            except requests.exceptions.RequestException as e:
                raise RuntimeError(
                    f'Failed to fetch from {endpoint}: {e}'
                ) from e
            except ValueError as e:
                raise RuntimeError(
                    f'Invalid JSON response from {endpoint}: {e}'
                ) from e

        return all_results

    def update_custom_data(
        self,
        request: TownRequest,
        app: PasApp,
        max_workers: int = 3,
        import_log_id: uuid.UUID | None = None
    ) -> tuple[int, int, list[dict[str, Any]]]:
        """
        Multi-threaded function that updates parliamentarians with custom
        field data.

        Uses a queue-based approach where worker threads fetch API data
        concurrently while the main thread handles all database updates to
        maintain thread safety.

        Returns:
            Tuple of (updated_count, error_count, output_messages)
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
                f'Warning: {len(parliamentarians_without_id)} '
                f'parliamentarians found without external_kub_id: '
                f'{", ".join(missing_names)}. These will not be synchronized.'
            )
            if self.output:
                self.output.error(warning_msg)
            log.warning(
                f'Found {len(parliamentarians_without_id)} parliamentarians '
                f'without external_kub_id: {missing_names}. '
                f'These will not be synchronized.'
            )

        if not parliamentarians_with_id:
            if self.output:
                self.output.info(
                    'No parliamentarians with external_kub_id found'
                )
            return 0, 0, []

        # Use only parliamentarians with external_kub_id for processing
        parliamentarians = parliamentarians_with_id

        if self.output:
            self.output.info(
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
                args=(
                    parliamentarian_queue, result_queue,
                    self.session, self.base_url
                )
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
                    if self.output:
                        self.output.error(
                            f'✗ Failed to fetch {result.title}: '
                            f'{result.error}'
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
                            if self.output:
                                self.output.success(
                                    f'✓ Updated {result.title}: '
                                    f'{", ".join(updated_fields)}'
                                )
                        else:
                            if self.output:
                                self.output.info(
                                    f'No custom data found for {result.title}'
                                )

                result_queue.task_done()

            except queue.Empty:
                if self.output:
                    self.output.error('Timeout waiting for API results')
                error_count += (len(parliamentarians) - processed)
                break

        # Wait for all worker threads to complete
        timed_out = False
        for t in threads:
            t.join(timeout=30)

        # Check if any threads timed out
        for t in threads:
            if t.is_alive():
                timed_out = True
                if self.output:
                    self.output.error('Warning: Some worker threads timed out')
                break

        # Update ImportLog if provided
        output_messages = []
        if import_log_id:
            import_log = request.session.query(ImportLog).filter(
                ImportLog.id == import_log_id
            ).first()
            if import_log and hasattr(self.output, 'get_messages'):
                output_messages = self.output.get_messages()  # type: ignore

                # Update ImportLog with custom data results
                if not import_log.details:
                    import_log.details = {}

                import_log.details['custom_data_update'] = {
                    'updated': updated_count,
                    'errors': error_count,
                    'processed': len(parliamentarians)
                }

                # Append output messages
                if 'output_messages' not in import_log.details:
                    import_log.details['output_messages'] = []
                import_log.details['output_messages'].extend(output_messages)

                # If timeout occurred, update the status to 'timeout'
                if timed_out:
                    import_log.status = 'timeout'

                request.session.flush()

        return updated_count, error_count, output_messages

    def import_data(
        self,
        request: TownRequest,
        app: PasApp,
        import_log_id: uuid.UUID | None = None
    ) -> tuple[dict[str, Any], list[Any], list[Any], list[Any], uuid.UUID]:
        """
        Performs KUB data import using the shared session.

        Args:
            request: TownRequest object
            app: PasApp object
            import_log_id: Optional existing ImportLog ID to update

        Returns:
            Tuple of (import_results, people_data, organization_data,
                      membership_data, import_log_id)
        """

        # Create or get ImportLog
        if import_log_id is None:
            import_log = ImportLog(
                user_id=(
                    request.current_user.id if request.current_user else None
                ),
                details={'status': 'started'},
                status='in_progress',
                import_type='cli'
            )
            request.session.add(import_log)
            request.session.flush()
            import_log_id = import_log.id
        else:
            import_log_result = request.session.query(ImportLog).filter(
                ImportLog.id == import_log_id
            ).first()
            if not import_log_result:
                raise ValueError(
                    f'ImportLog with ID {import_log_id} not found'
                )
            import_log = import_log_result

        try:
            self._check_api_accessibility()

            if self.output:
                self.output.info('Fetching people data...')
            people_raw = self._fetch_api_data_with_pagination('people')
            if self.output:
                self.output.success(
                    f'Fetched {len(people_raw)} people records'
                )

            if self.output:
                self.output.info('Fetching organizations data...')
            organizations_raw = self._fetch_api_data_with_pagination(
                'organizations'
            )
            if self.output:
                self.output.success(
                    f'Fetched {len(organizations_raw)} organization records'
                )

            if self.output:
                self.output.info('Fetching memberships data...')
            memberships_raw = self._fetch_api_data_with_pagination(
                'memberships'
            )
            if self.output:
                self.output.success(
                    f'Fetched {len(memberships_raw)} membership records'
                )

            # Create mock file data structures for load_and_concatenate_json
            # We use this so we can use the same method as in form upload
            people_mock_files = [
                create_mock_file_data(people_raw, 'people.json')
            ]
            organizations_mock_files = [
                create_mock_file_data(
                    organizations_raw, 'organizations.json'
                )
            ]
            memberships_mock_files = [
                create_mock_file_data(memberships_raw, 'memberships.json')
            ]
            if self.output:
                self.output.info('Processing people data...')
            people_data = load_and_concatenate_json(people_mock_files)
            if self.output:
                self.output.info('Processing organizations data...')
            organization_data = load_and_concatenate_json(
                organizations_mock_files
            )
            if self.output:
                self.output.info('Processing memberships data...')
            membership_data = load_and_concatenate_json(memberships_mock_files)

            # Perform the import
            if self.output:
                self.output.info('Starting data import...')

            # Create logger that forwards to output handler
            import_logger = None
            if self.output:
                import_logger = logging.getLogger('onegov.pas.import.temp')
                import_logger.setLevel(logging.DEBUG)
                # Clear any existing handlers
                import_logger.handlers.clear()
                # Add our custom handler
                handler = OutputLogHandler(self.output)
                handler.setLevel(logging.DEBUG)
                import_logger.addHandler(handler)
                import_logger.propagate = False

            try:
                import_results = import_zug_kub_data(
                    session=request.session,
                    people_data=people_data,
                    organization_data=organization_data,
                    membership_data=membership_data,
                    user_id=(
                        request.current_user.id
                        if request.current_user
                        else None
                    ),
                    logger=import_logger
                )
            finally:
                # Clean up the temporary logger
                if import_logger:
                    import_logger.handlers.clear()

            # Update ImportLog with results
            import_log.details.update({
                'import_results': import_results,
                'status': 'completed'
            })
            import_log.status = 'completed'

            # Store output messages if available
            if hasattr(self.output, 'get_messages'):
                output_messages = self.output.get_messages()  # type: ignore
                import_log.details['output_messages'] = output_messages

            # Store source data
            import_log.people_source = people_data
            import_log.organizations_source = organization_data
            import_log.memberships_source = membership_data

            request.session.flush()

            # Display results
            if self.output:
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
                        self.output.info(
                            f'{category}: {created_count} created, '
                            f'{updated_count} updated, '
                            f'{processed_count} processed'
                        )

                self.output.success(
                    f'Import completed successfully! '
                    f'Total: {total_created} created, '
                    f'{total_updated} updated, '
                    f'{total_processed} processed'
                )

            return (
                import_results, people_data, organization_data,
                membership_data, import_log_id
            )

        except Exception as e:
            # Update ImportLog with error
            import_log.details.update({
                'error': str(e),
                'status': 'failed'
            })
            import_log.status = 'failed'

            # Store output messages if available
            if hasattr(self.output, 'get_messages'):
                output_messages = self.output.get_messages()  # type: ignore
                import_log.details['output_messages'] = output_messages

            request.session.flush()

            if self.output:
                self.output.error(f'Import failed: {e}')
            raise

    def run_full_sync(
        self,
        request: TownRequest,
        app: PasApp,
        update_custom: bool = True,
        max_workers: int = 3
    ) -> tuple[dict[str, Any], uuid.UUID]:
        """
        Complete KUB synchronization including import and custom data update.

        This is the main entry point for cronjobs and automated imports.

        Args:
            request: TownRequest object
            app: PasApp object
            update_custom: Whether to update custom data after import
            max_workers: Maximum number of concurrent workers for custom data

        Returns:
            Tuple of (combined_results, import_log_id)
        """
        # Perform main import
        import_results, _people_data, _org_data, _membership_data, log_id = (
            self.import_data(request, app)
        )

        combined_results = {
            'import': import_results,
            'custom_data': None
        }

        # Update custom data if requested
        if update_custom:
            if self.output:
                self.output.info('Starting custom data update...')

            try:
                updated_count, error_count, _output_messages = (
                    self.update_custom_data(
                        request, app, max_workers, log_id
                    )
                )
                combined_results['custom_data'] = {
                    'updated': updated_count,
                    'errors': error_count
                }

                if self.output:
                    self.output.success(
                        f'Custom data update completed: {updated_count} '
                        f'updated, {error_count} errors'
                    )
            except Exception as e:
                combined_results['custom_data'] = {
                    'error': str(e)
                }
                if self.output:
                    self.output.error(f'Custom data update failed: {e}')
                raise
        else:
            if self.output:
                self.output.info('Skipping custom data update')

        return combined_results, log_id


# Legacy functions for backward compatibility
def fetch_api_data_with_pagination(
    endpoint: str, token: str, base_url: str
) -> list[dict[str, Any]]:
    """
    Legacy function for backward compatibility.

    Fetches all data from a paginated API endpoint.

    Args:
        endpoint: The API endpoint (e.g., 'people', 'organizations',
                  'memberships')
        token: Authorization token
        base_url: Base URL for the API (should not end with slash)

    Returns:
        List of all records from all pages
    """
    with KubImporter(token, base_url) as importer:
        return importer._fetch_api_data_with_pagination(endpoint)


def perform_custom_data_update(
    request: TownRequest,
    app: PasApp,
    token: str,
    base_url: str,
    output: OutputHandler | None = None,
    max_workers: int = 3,
    import_log_id: uuid.UUID | None = None
) -> tuple[int, int, list[dict[str, Any]]]:
    """Legacy function for backward compatibility."""
    with KubImporter(token, base_url, output) as importer:
        return importer.update_custom_data(
            request, app, max_workers, import_log_id
        )


def perform_kub_import(
    request: TownRequest,
    app: PasApp,
    token: str,
    base_url: str,
    output: OutputHandler | None = None,
    import_log_id: uuid.UUID | None = None
) -> tuple[dict[str, Any], list[Any], list[Any], list[Any], uuid.UUID]:
    """Legacy function for backward compatibility."""
    with KubImporter(token, base_url, output) as importer:
        return importer.import_data(request, app, import_log_id)


def run_full_kub_sync(
    request: TownRequest,
    app: PasApp,
    token: str,
    base_url: str,
    output: OutputHandler | None = None,
    update_custom: bool = True,
    max_workers: int = 3
) -> tuple[dict[str, Any], uuid.UUID]:
    """Legacy function for backward compatibility."""
    with KubImporter(token, base_url, output) as importer:
        return importer.run_full_sync(request, app, update_custom, max_workers)
