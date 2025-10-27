from __future__ import annotations

import json
import logging
from morepath import redirect
from onegov.pas.importer.zug_kub_importer import import_zug_kub_data
from onegov.pas.models import ImportLog
from onegov.core.security import Private
from onegov.core.utils import dictionary_to_binary
from onegov.org.models import Organisation
from onegov.pas import _, PasApp
from onegov.pas.forms.data_import import DataImportForm
from onegov.pas.layouts import ImportLayout


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
    name='pas-import',
    template='data_import.pt',
    form=DataImportForm,
    permission=Private,
)
def handle_data_import(
    self: Organisation, request: TownRequest, form: DataImportForm
) -> RenderData | Response:

    error_message = None

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
            import_results = import_zug_kub_data(
                session=request.session,
                people_data=people_data,
                organization_data=organization_data,
                membership_data=membership_data,
                user_id=(request.current_user.id
                         if request.current_user else None),
                import_type='upload',
                create_import_log=True
            )

            # Check if import log ID was returned and redirect to it
            import_log_id = import_results.get('_import_log_id')
            if import_log_id:
                import_log = request.session.query(ImportLog).filter(
                    ImportLog.id == import_log_id
                ).first()
                if import_log:
                    return redirect(request.link(import_log))

            request.success(_('Import completed successfully'))
            return redirect(request.link(self, name='pas-import'))

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

    layout = ImportLayout(self, request)
    return {
        'layout': layout,
        'title': _('Import'),
        'form': form,
        'error_message': error_message,
    }
