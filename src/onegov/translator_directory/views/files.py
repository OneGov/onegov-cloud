from uuid import uuid4

from onegov.core.security import Secret
from onegov.core.templates import render_macro
from onegov.file import File
from onegov.file.utils import extension_for_content_type
from onegov.org import utils
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


@TranslatorDirectoryApp.html(model=File, permission=Secret, name='details')
def view_file_details(self: File, request: 'TranslatorAppRequest') -> str:
    layout = DefaultLayout(self, request)
    extension = extension_for_content_type(
        self.reference.content_type,
        self.reference.filename
    )
    color = utils.get_extension_color(extension)

    # IE 11 caches all ajax requests otherwise
    @request.after
    def must_revalidate(response: 'Response') -> None:
        response.headers.add('cache-control', 'must-revalidate')
        response.headers.add('cache-control', 'no-cache')
        response.headers.add('cache-control', 'no-store')
        response.headers['pragma'] = 'no-cache'
        response.headers['expires'] = '0'

    return render_macro(
        layout.macros['file-details'],
        request,
        {
            'id': uuid4().hex,
            'file': self,
            'layout': layout,
            'extension': extension,
            'color': color,
            'hide_publication': True
        }
    )
