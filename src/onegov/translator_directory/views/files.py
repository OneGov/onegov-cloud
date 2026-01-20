from __future__ import annotations

from webob.exc import HTTPForbidden

from onegov.core.security import Public, Secret
from onegov.file import File
from onegov.file.integration import (
    render_depot_file,
    view_file as original_view_file,
    view_file_head as original_view_file_head,
    view_thumbnail as original_view_thumbnail,
    view_thumbnail_head as original_view_thumbnail_head,
)
from onegov.org.views.files import view_file_details as org_view_file_details
from onegov.translator_directory import TranslatorDirectoryApp
from onegov.translator_directory.layout import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from depot.io.interfaces import StoredFile
    from onegov.translator_directory.request import TranslatorAppRequest
    from webob import Response


@TranslatorDirectoryApp.html(model=File, permission=Secret, name='details')
def view_file_details(self: File, request: TranslatorAppRequest) -> str:
    return org_view_file_details(self, request, DefaultLayout(self, request))  # type: ignore[arg-type]


@TranslatorDirectoryApp.view(
    model=File, render=render_depot_file, permission=Public
)
def view_file(self: File, request: TranslatorAppRequest) -> StoredFile:
    if request.is_translator:
        raise HTTPForbidden()

    return original_view_file(self, request)


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

    return original_view_thumbnail(self, request)


@TranslatorDirectoryApp.view(
    model=File,
    render=render_depot_file,
    permission=Public,
    request_method='HEAD',
)
def view_file_head(self: File, request: TranslatorAppRequest) -> StoredFile:
    if request.is_translator:
        raise HTTPForbidden()

    return original_view_file_head(self, request)


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

    return original_view_thumbnail_head(self, request)
