from __future__ import annotations

import json
import logging

from aiohttp.web_exceptions import HTTPBadRequest, HTTPUnsupportedMediaType
from morepath import redirect

from onegov.core.crypto import random_token
from onegov.core.security import Private
from onegov.core.utils import dictionary_to_binary
from onegov.file import File, FileCollection
from onegov.file.utils import as_fileintent
from onegov.org.models import Organisation
from onegov.pas import _, PasApp
from onegov.pas.forms.data_import import DataImportForm
from onegov.pas.importer.json_import import import_zug_kub_data
from onegov.pas.layouts import DefaultLayout


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import LaxFileDict
    from onegov.core.types import RenderData
    from collections.abc import Sequence
    from onegov.town6.request import TownRequest
    from webob import Response


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
            log.error(
                f'Error decoding JSON from file {filename}.', exc_info=True
            )
            raise RuntimeError(
                f'Error decoding JSON from file {filename}.'
            ) from e
        except UnicodeDecodeError as e:
            log.error(
                f'Error decoding file {filename} as UTF-8.', exc_info=True
            )
            raise RuntimeError(
                f'Error decoding file {filename} as UTF-8.'
            ) from e
        except Exception as e:
            log.error(
                f'Unexpected error processing file {filename}: {e}',
                exc_info=True
            )
            raise RuntimeError(
                f'Unexpected error processing file {filename}'
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
    layout = DefaultLayout(self, request)
    import_details: dict[str, dict[str, list[Any]]] | None = None
    error_message: str | None = None

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
            # Renamed variable to import_details
            import_details = import_zug_kub_data(
                session=request.session,
                people_data=people_data,
                organization_data=organization_data,
                membership_data=membership_data,
            )
            request.message(
                _('Data import completed successfully.'), 'success')
        except Exception as e:
            log.error(f'Data import failed: {e}', exc_info=True)
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
        'import_details': import_details,
        'error_message': error_message,
        'errors': form.errors
    }


@PasApp.view(
    model=FileCollection[Any],
    name='upload-json-import-files',
    permission=Private,
    request_method='POST',
)
def upload_json_import_file(
    self: FileCollection[Any], request: TownRequest
) -> None:
    request.assert_valid_csrf_token()

    fs = request.params.get('file', '')
    if isinstance(fs, str):
        # malformed formdata
        raise HTTPBadRequest()

    attachment = File(id=random_token())
    attachment.name = f'import_json-{fs.filename}'
    attachment.reference = as_fileintent(fs.file, fs.filename)

    if attachment.reference.content_type != 'application/json':
        raise HTTPUnsupportedMediaType()

    self.add(attachment.name, content=attachment)  # type:ignore[arg-type]
