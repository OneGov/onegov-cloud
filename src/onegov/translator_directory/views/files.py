from __future__ import annotations

import morepath

from uuid import uuid4
from webob.exc import HTTPForbidden

from onegov.core.security import Public, Secret
from onegov.core.templates import render_macro
from onegov.file import File
from onegov.file.integration import (
    render_depot_file,
    respond_with_alt_text,
    respond_with_caching_header,
    respond_with_x_robots_tag_header,
)
from onegov.file.utils import extension_for_content_type
from onegov.org import utils
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from depot.io.interfaces import StoredFile
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


"""
This is basically the file views from org, but consists of a change made
to restrict translator `GeneralFile` view permissions.
For private files, even knowing the unguessable URL should still return
403 Forbidden when accessed.

While some duplication is regrettable, putting this in org would pollute
the generic module with translator-specific checks at runtime that don't
exist for the majority of onegov apps.
"""


@TranslatorDirectoryApp.html(model=File, permission=Secret, name='details')
def view_file_details(self: File, request: TranslatorAppRequest) -> str:
    layout = DefaultLayout(self, request)
    extension = extension_for_content_type(
        self.reference.content_type,
        self.reference.filename
    )
    color = utils.get_extension_color(extension)

    # IE 11 caches all ajax requests otherwise
    @request.after
    def must_revalidate(response: Response) -> None:
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


@TranslatorDirectoryApp.view(
    model=File, render=render_depot_file, permission=Public
)
def view_file(self: File, request: TranslatorAppRequest) -> StoredFile:
    if request.is_translator:
        raise HTTPForbidden()

    respond_with_alt_text(self, request)
    respond_with_caching_header(self, request)
    respond_with_x_robots_tag_header(self, request)
    return self.reference.file


@TranslatorDirectoryApp.view(
    model=File, name='thumbnail', permission=Public, render=render_depot_file
)
@TranslatorDirectoryApp.view(
    model=File, name='small', permission=Public, render=render_depot_file
)
@TranslatorDirectoryApp.view(
    model=File, name='medium', permission=Public, render=render_depot_file
)
def view_thumbnail(
    self: File, request: TranslatorAppRequest
) -> StoredFile | Response:
    if request.is_translator:
        raise HTTPForbidden()

    if request.view_name in ('small', 'medium'):
        size = request.view_name
    else:
        size = 'small'

    respond_with_alt_text(self, request)
    respond_with_caching_header(self, request)
    respond_with_x_robots_tag_header(self, request)

    thumbnail_id = self.get_thumbnail_id(size)

    if not thumbnail_id:
        return morepath.redirect(request.link(self))

    return request.app.bound_depot.get(thumbnail_id)  # type:ignore


@TranslatorDirectoryApp.view(
    model=File,
    render=render_depot_file,
    permission=Public,
    request_method='HEAD',
)
def view_file_head(self: File, request: TranslatorAppRequest) -> StoredFile:
    if request.is_translator:
        raise HTTPForbidden()

    @request.after
    def set_cache(response: Response) -> None:
        response.cache_control.max_age = 60

    return view_file(self, request)


@TranslatorDirectoryApp.view(
    model=File,
    name='thumbnail',
    render=render_depot_file,
    permission=Public,
    request_method='HEAD',
)
@TranslatorDirectoryApp.view(
    model=File,
    name='small',
    render=render_depot_file,
    permission=Public,
    request_method='HEAD',
)
@TranslatorDirectoryApp.view(
    model=File,
    name='medium',
    render=render_depot_file,
    permission=Public,
    request_method='HEAD',
)
def view_thumbnail_head(
    self: File, request: TranslatorAppRequest
) -> StoredFile | Response:
    if request.is_translator:
        raise HTTPForbidden()

    @request.after
    def set_cache(response: Response) -> None:
        response.cache_control.max_age = 60

    return view_thumbnail(self, request)
