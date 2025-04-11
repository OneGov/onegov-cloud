# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
from io import IOBase
from typing import Any, TYPE_CHECKING

from aiohttp.web_exceptions import HTTPBadRequest, HTTPUnsupportedMediaType
from sqlalchemy import text

from onegov.core.crypto import random_token
from onegov.core.security import Private
from onegov.file import File, FileCollection
from onegov.file.utils import as_fileintent
from onegov.org.models import Organisation
from onegov.pas import _, PasApp
from onegov.pas.forms.data_import import DataImportForm
from onegov.pas.importer.json_import import import_zug_kub_data
from onegov.pas.layouts import DefaultLayout
from onegov.town6.app import TownApp

if TYPE_CHECKING:
    from collections.abc import Sequence, Mapping
    from onegov.core.types import RenderData
    from onegov.pas.importer.json_import import (
        MembershipData,
        OrganizationData,
        PersonData,
        UploadedFileData,
    )
    from onegov.town6.request import TownRequest


log = logging.getLogger('onegov.pas.data_import')


def clean(app: TownApp) -> None:
    schema = app.session_manager.current_schema
    assert schema is not None
    session = app.session_manager.session()
    session.execute(
        text('SET search_path TO :schema;').bindparams(schema=schema)
    )

    # Get counts from each table for logging
    tables = [
        'pas_commission_memberships',
        'pas_parliamentarian_rolesi',
        'pas_commissions',
        'pas_parliamentarians',
        'pas_parliamentary_groups',
        'pas_parties',
    ]

    counts = {}
    for table in tables:
        count = session.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar()
        counts[table] = count

    truncate_statement = """
        TRUNCATE TABLE
            pas_commission_memberships,
            pas_parliamentarian_roles,
            pas_commissions,
            pas_parliamentarians,
            pas_parliamentary_groups,
            pas_parties,
        CASCADE;
        COMMIT;
    """

    session.execute(text(truncate_statement))


@PasApp.form(
    model=Organisation,
    template='data_import.pt',
    name='pas-import',
    form=DataImportForm,
    permission=Private,
)
def handle_data_import(
    self: Organisation, request: TownRequest, form: DataImportForm
) -> RenderData:
    layout = DefaultLayout(self, request)
    results = None

    def load_and_concatenate_json(
        sources: Sequence[UploadedFileData]
    ) -> list[Any]:
        """
        Loads and concatenates the 'results' list from multiple JSON files.
        Moved from json_import._load_json.
        """
        all_results: list[Any] = []
        for file_info in sources:
            filename = file_info.get('filename', 'unknown file')
            # Ensure file_info has the expected structure for dictionary_to_binary
            if not all(k in file_info for k in ('data', 'filename', 'mimetype', 'size')):
                log.warning(
                    f'Skipping invalid file data structure for {filename}. '
                    f'Expected keys: data, filename, mimetype, size.'
                )
                continue

            try:
                # Decode the base64/gzipped data using the utility function
                content_bytes = dictionary_to_binary(file_info) # type: ignore[arg-type]
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
            except json.JSONDecodeError:
                log.error(
                    f'Error decoding JSON from file {filename}.', exc_info=True
                )
                raise  # Re-raise to inform the user in the UI
            except UnicodeDecodeError:
                log.error(
                    f'Error decoding file {filename} as UTF-8.', exc_info=True
                )
                raise  # Re-raise
            except Exception as e:
                log.error(
                    f'Unexpected error processing file {filename}: {e}',
                    exc_info=True
                )
                raise # Re-raise

        return all_results

    if request.method == 'POST' and form.validate():
        if form.clean.data:
            clean(request.app)
        try:
            # Load and concatenate data from uploaded files
            people_data: list[PersonData] = load_and_concatenate_json(
                form.people_source.data
            )
            organization_data: list[OrganizationData] = load_and_concatenate_json(
                form.organizations_source.data
            )
            membership_data: list[MembershipData] = load_and_concatenate_json(
                form.memberships_source.data
            )

            # Pass the processed data lists to the importer
            import_zug_kub_data(
                session=request.session,
                people_data=people_data,
                organization_data=organization_data,
                membership_data=membership_data,
            )
            request.message(
                _('Data import completed successfully.'), 'success'
            )
        except Exception as e:
            log.error(f'Data import failed: {e}', exc_info=True)
            # Provide a more user-friendly error message
            request.message(
                _('Data import failed: ${error}', mapping={'error': str(e)}),
                'warning'
            )
            # Optionally keep the detailed error for display if needed
            results = f'Error during import: {e}'

    return {
        'title': _('Import'),
        'layout': layout,
        'form': form,
        'results': results,
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
