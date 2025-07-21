from __future__ import annotations

import json
import logging

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.core.utils import dictionary_to_binary
from onegov.org.models import Organisation
from onegov.pas import _, PasApp
from onegov.pas.forms.data_import import DataImportForm
from onegov.pas.importer.json_import import import_zug_kub_data
from onegov.pas.layouts import ImportLayout
from onegov.pas.models import (
    PASCommission,
    PASCommissionMembership,
    PASParliamentarian,
    PASParliamentarianRole,
    Party,
)


from typing import Any, TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from onegov.core.types import LaxFileDict, RenderData
    from collections.abc import Sequence
    from onegov.town6.request import TownRequest
    from webob import Response

    class ImportCategoryResult(TypedDict):
        created: list[Any]
        updated: list[Any]
        processed: int

    # Define a type alias for the complex import details structure
    # Replace with the actual type returned by the importer
    ImportResultsDict = dict[str, ImportCategoryResult]


log = logging.getLogger('onegov.pas.data_import')


def load_and_concatenate_json(
    sources: Sequence[LaxFileDict]
) -> list[Any]:
    """
    Loads and concatenates the 'results' list from multiple JSON files.
    """
    all_results: list[Any] = []
    for file_info in sources:
        filename = file_info.get('filename', 'unknown file')
        # Ensure file_info has the expected structure for dictionary_to_binary
        if not all(k in file_info for k in (
            'data', 'filename', 'mimetype', 'size')
        ):
            log.warning(
                f'Skipping invalid file data structure for {filename}. '
                f'Expected keys: data, filename, mimetype, size.'
            )
            continue

        try:
            content_bytes = dictionary_to_binary(file_info)
            content_str = content_bytes.decode('utf-8')
            data = json.loads(content_str)

            results_list = data.get('results')
            if isinstance(results_list, list):
                all_results.extend(results_list)
            else:
                log.warning(
                    f'Skipping file {filename}: "results" key not found '
                    f'or is not a list in the JSON data.'
                )
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f'Error decoding JSON from file {filename}.'
            ) from e
        except UnicodeDecodeError as e:
            raise RuntimeError(
                f'Error decoding file {filename} as UTF-8.'
            ) from e
        except Exception as e:
            raise RuntimeError(
                f'Unexpected error processing file {filename}.'
            ) from e

    return all_results


@PasApp.form(
    model=Organisation,
    template='data_import.pt',
    name='pas-import',
    form=DataImportForm,
    permission=Private,
)
def handle_data_import(
    self: Organisation, request: TownRequest, form: DataImportForm
) -> RenderData | Response:
    layout = ImportLayout(self, request)
    processed_import_details: dict[str, dict[str, Any]] = {}  # For template
    error_message: str | None = None
    total_processed = 0
    total_created = 0
    total_updated = 0

    # Helper function to get display title for various imported objects
    def get_item_display_title(item: Any) -> str:
        if isinstance(item, PASParliamentarian):
            return item.title  # Already includes first/last name etc.
        elif isinstance(item, (PASCommission, Party)):
            return item.name
        elif isinstance(item, PASCommissionMembership):
            # Ensure related objects are loaded or handle potential errors
            parl_title = (item.parliamentarian.title
                          if item.parliamentarian else 'Unknown Parl.')
            comm_name = (item.commission.name
                         if item.commission else 'Unknown Comm.')
            return f'{parl_title} in {comm_name} ({item.role})'
        elif isinstance(item, PASParliamentarianRole):
            parl_title = (item.parliamentarian.title
                          if item.parliamentarian else 'Unknown Parl.')
            role_details: list[str] = [str(item.role)]
            if item.party:
                role_details.append(f'Party: {item.party.name}')
            if item.parliamentary_group:
                role_details.append(f'Group: {item.parliamentary_group.name}')
            if item.additional_information:
                role_details.append(f'({item.additional_information})')
            return f'{parl_title} - {" ".join(role_details)}'
        elif hasattr(item, 'title') and isinstance(item.title, str):
            return item.title  # Fallback for unexpected types with a title
        elif hasattr(item, 'name') and isinstance(item.name, str):
            return item.name  # Fallback for unexpected types with a name
        else:
            return f'Unknown Object (Type: {type(item).__name__})'

    # Extract category details for template rendering
    def extract_category_details(
        import_details: ImportResultsDict
    ) -> dict[str, dict[str, Any]]:
        """
        Process import details to prepare data for template rendering.
        Extracts and calculates values that were previously defined in TAL.
        """
        processed_details = {}
        for category_name, details in import_details.items():
            # details is now guaranteed to be ImportCategoryResult
            created = details.get('created', [])
            updated = details.get('updated', [])
            processed = details.get('processed', 0)

            # Ensure we're dealing with lists before calling len()
            created_list = created if isinstance(created, list) else []
            updated_list = updated if isinstance(updated, list) else []
            created_count = len(created_list)
            updated_count = len(updated_list)
            category_title = category_name.replace('_', ' ').title()

            processed_details[category_name] = {
                'created': created,
                'updated': updated,
                'processed': processed,
                'created_count': created_count,
                'updated_count': updated_count,
                'category_title': category_title,
            }
        return processed_details

    if request.method == 'POST' and form.validate():
        try:
            # Load and concatenate data from uploaded files
            people_data = load_and_concatenate_json(
                form.people_source.data
            )
            organization_data = load_and_concatenate_json(
                form.organizations_source.data
            )
            membership_data = load_and_concatenate_json(
                form.memberships_source.data
            )
            # Get raw results from the import function
            # The return type is dict[str, ImportCategoryResult]
            import_results = import_zug_kub_data(
                session=request.session,
                people_data=people_data,
                organization_data=organization_data,
                membership_data=membership_data,
                user_id=(request.current_user.id
                         if request.current_user else None)
            )

            # Process results for template and calculate totals
            any_changes = False
            if import_results:  # Ensure import_results is not None
                for details in import_results.values():
                    # details is now guaranteed to be ImportCategoryResult
                    created = details.get('created', [])
                    updated = details.get('updated', [])
                    processed = details.get('processed', 0)  # Already int

                    # Ensure we're dealing with lists before calling len()
                    created_list = created if isinstance(created, list) else []
                    updated_list = updated if isinstance(updated, list) else []
                    created_count = len(created_list)
                    updated_count = len(updated_list)

                    total_created += created_count
                    total_updated += updated_count
                    # Ensure processed is an int
                    processed_int = (processed if isinstance(processed, int)
                                     else 0)
                    total_processed += processed_int

                    if created_count > 0 or updated_count > 0:
                        any_changes = True

                # Use the extracted function to prepare data for the template
                # Pass import_results which is ImportResultsDict
                processed_import_details = extract_category_details(
                    import_results
                )

            # Generate success/info message based on totals
            if any_changes:
                request.message(
                    _(
                        'Data import completed. Processed ${processed} items: '
                        '${created} created, ${updated} updated.',
                        mapping={
                            'processed': total_processed,
                            'created': total_created,
                            'updated': total_updated
                        }
                    ), 'success'
                 )
            else:
                request.message(
                    _(
                        'Data import completed. Processed ${processed} items. '
                        'No changes were needed - data is already up to date.',
                         mapping={'processed': total_processed}
                    ), 'info'
                 )

            layout.breadcrumbs.append(Link(_('Import result'), '#'))

        except Exception as e:
            log.exception('Data import failed')
            # Provide a more user-friendly error message
            request.message(
                _('Data import failed: ${error}', mapping={'error': str(e)}),
                'warning'
            )
            # Display the exception message
            cause = e.__cause__ or e.__context__
            error_msg = f'Error during import: {e}'
            if cause:
                error_msg += f'\nCaused by: {cause}'
            error_message = error_msg

    return {
        'title': _('Import'),
        'layout': layout,
        'form': form,
        'import_details': processed_import_details,
        'error_message': error_message,
        'get_item_display_title': get_item_display_title,
        'errors': form.errors
    }
