from __future__ import annotations

from onegov.translator_directory import _
from onegov.core.security import Secret
from onegov.core.templates import render_macro
from onegov.file import File
from onegov.file.utils import extension_for_content_type
from onegov.org.views.files import view_upload_file
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.collections.documents import (
    TranslatorDocumentCollection)
from onegov.translator_directory.layout import (
    TranslatorDocumentsLayout, DefaultLayout)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.translator_directory.request import TranslatorAppRequest


@TranslatorDirectoryApp.html(
    model=TranslatorDocumentCollection,
    permission=Secret,
    template='documents.pt'
)
def view_translator_documents(
    self: TranslatorDocumentCollection,
    request: TranslatorAppRequest
) -> RenderData:

    layout = TranslatorDocumentsLayout(self, request)

    return {
        'layout': layout,
        'model': self,
        'grouped': self.files_by_category,
        'title': _('Documents'),
        'categories': self.unique_categories,
        'format_date': lambda dt: layout.format_date(dt, 'datetime'),
        'actions_url': lambda file_id: request.class_link(
            File, name='details', variables={'id': file_id}
        ),
        'extension': lambda file: extension_for_content_type(
            file.reference.content_type,
            file.name
        )
    }


@TranslatorDirectoryApp.html(
    model=TranslatorDocumentCollection,
    name='upload',
    request_method='POST',
    permission=Secret
)
def view_upload_file_translator(
    self: TranslatorDocumentCollection,
    request: TranslatorAppRequest
) -> str:

    assert self.translator is not None
    file = view_upload_file(self, request, return_file=True)

    # File could be a new file or duplicate
    created_before = file.note
    if not created_before:
        self.translator.files.append(file)

    file.published = False
    # If duplicate, we change the category
    category = request.params.get('category')
    file.note = category if isinstance(category, str) else None

    layout = DefaultLayout(self, request)
    return render_macro(layout.macros['file-info'], request, {
        'file': file,
        'format_date': lambda dt: layout.format_date(dt, 'datetime'),
        'actions_url': lambda file_id: request.class_link(
            File, name='details', variables={'id': file_id}
        ),
        'extension': lambda file: extension_for_content_type(
            file.reference.content_type,
            file.name
        )
    })
