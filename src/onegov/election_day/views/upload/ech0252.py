from __future__ import annotations
import transaction

from onegov.election_day import _
from onegov.election_day import ElectionDayApp
from onegov.election_day.collections import ArchivedResultCollection
from onegov.election_day.formats import import_ech
from onegov.election_day.forms.upload.ech0252 import UploadEchForm
from onegov.election_day.layouts import ManageLayout
from onegov.election_day.models import Principal

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.election_day.formats.imports.common import FileImportError
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.request import ElectionDayRequest


@ElectionDayApp.manage_form(
    model=Principal,
    name='upload-ech',
    template='upload_ech0252.pt',
    form=UploadEchForm,
)
def view_upload_ech(
    self: Canton | Municipality,
    request: ElectionDayRequest,
    form: UploadEchForm
) -> RenderData:
    """ Upload results via eCH-0252."""

    errors: list[FileImportError] = []
    status = 'open'

    if form.submitted(request):
        session = request.session
        assert form.xml.file is not None
        assert request.app.default_locale is not None
        errors, updated, _deleted = import_ech(
            self,
            form.xml.file,
            session,
            request.app.default_locale
        )
        archive = ArchivedResultCollection(session)
        for item in updated:
            archive.update(item, request)

        if errors:
            status = 'error'
            transaction.abort()
        else:
            status = 'success'
            request.app.pages_cache.flush()
            request.app.send_zulip(
                self.name,
                'New eCH-0252 results available'
            )

    layout = ManageLayout(self, request)
    layout.breadcrumbs.append(
        (_('eCH-0252 Upload'), request.link(self, 'upload-ech'), '')
    )

    return {
        'layout': layout,
        'title': _('eCH-0252 Upload'),
        'form': form,
        'cancel': layout.manage_model_link,
        'errors': errors,
        'status': status,
    }
