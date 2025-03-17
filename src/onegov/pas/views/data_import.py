from __future__ import annotations

import logging

from aiohttp.web_exceptions import HTTPBadRequest, HTTPUnsupportedMediaType
from sqlalchemy import text

from onegov.file import FileCollection
from onegov.file import File
from onegov.core.security import Private
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.org.models import Organisation
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.forms.data_import import DataImportForm
from onegov.pas.importer.json_import import import_zug_kub_data
from onegov.pas.layouts import (
    DefaultLayout,
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


log = logging.getLogger('onegov.pas.data_import')


def clean(app) -> None:
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

    log.info(
        f'Removing data from tables: {", ".join(f"{table}({count})" for table, count in counts.items())}',
        fg='green',
    )

    # Truncate all tables in the correct order (respecting foreign key constraints)
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

    if request.method == 'POST' and form.validate():
        breakpoint()
        try:
            results = import_zug_kub_data(
                session=request.session,
                people_source=form.people_source.data,
                organizations_source=form.organizations_source.data,
                memberships_source=form.memberships_source.data,
            )
            request.message(
                _('Data import completed successfully.'), 'success'
            )
        except Exception as e:
            log.error(f'Data import failed: {e}', exc_info=True)
            request.message(_('Data import failed.'), 'error')
            results = str(e)
    elif request.method == 'POST':
        request.message(_('There are errors in the form.'), 'error')

    return {
        'title': _('Import'),
        'layout': layout,
        'form': form,
        'results': results,
    }


@PasApp.view(
    model=FileCollection,
    name='upload-json-import-files',
    permission=Private,
    request_method='POST',
)
def upload_json_import_file(
    self: FileCollection, request: TownRequest
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

    self.files.append(attachment)
