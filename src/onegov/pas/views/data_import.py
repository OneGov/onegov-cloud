from __future__ import annotations

import logging
from typing import Any

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
from onegov.town6.app import TownApp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
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

    if request.method == 'POST' and form.validate():
        if form.clean.data:
            clean(request.app)
        try:
            breakpoint()
            # need to iterate over each .data of for each of these:
            import_zug_kub_data(
                session=request.session,
                people_source=str(form.people_source.data),
                organizations_source=str(form.organizations_source.data),
                memberships_source=str(form.memberships_source.data),
            )
            request.message(
                _('Data import completed successfully.'), 'success'
            )
        except Exception as e:
            breakpoint()
            log.error(f'Data import failed: {e}', exc_info=True)
            request.message(f'Data import failed {e}', 'warning')
            results = str(e)

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
