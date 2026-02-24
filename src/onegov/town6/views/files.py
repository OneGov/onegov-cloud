from __future__ import annotations

from onegov.core.security import Private, Public
from onegov.file import File
from onegov.org.views.files import (
    view_file_details, view_get_image_collection, view_upload_general_file,
    view_upload_image_file, view_file_digest, view_file_links, handle_sign,
    view_get_file_collection)

from onegov.town6 import TownApp
from onegov.town6.layout import (
    DefaultLayout, GeneralFileCollectionLayout, ImageFileCollectionLayout)
from onegov.org.models import (
    GeneralFile, GeneralFileCollection, ImageFileCollection)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest


@TownApp.html(
    model=GeneralFileCollection,
    template='files.pt',
    permission=Private
)
def town_view_file_collection(
    self: GeneralFileCollection,
    request: TownRequest
) -> RenderData:
    return view_get_file_collection(
        self, request, GeneralFileCollectionLayout(self, request))


@TownApp.html(model=GeneralFile, permission=Private, name='details')
def view_town_file_details(self: GeneralFile, request: TownRequest) -> str:
    return view_file_details(self, request, DefaultLayout(self, request))


@TownApp.html(model=GeneralFile, permission=Private, name='links')
def view_town_file_links(self: GeneralFile, request: TownRequest) -> str:
    return view_file_links(self, request, DefaultLayout(self, request))


@TownApp.html(
    model=ImageFileCollection,
    template='images.pt',
    permission=Private
)
def view_town_image_collection(
    self: ImageFileCollection,
    request: TownRequest
) -> RenderData:
    return view_get_image_collection(
        self, request, ImageFileCollectionLayout(self, request))


@TownApp.html(
    model=GeneralFileCollection,
    name='upload',
    request_method='POST',
    permission=Private
)
def view_town_upload_general_file(
    self: GeneralFileCollection,
    request: TownRequest
) -> str:
    return view_upload_general_file(
        self, request, DefaultLayout(self, request))


@TownApp.html(
    model=ImageFileCollection,
    name='upload',
    request_method='POST',
    permission=Private
)
def view_town_upload_image_file(
    self: ImageFileCollection,
    request: TownRequest
) -> str:
    return view_upload_image_file(self, request, DefaultLayout(self, request))


@TownApp.html(model=GeneralFileCollection, name='digest', permission=Public)
def view_town_file_digest(
    self: GeneralFileCollection,
    request: TownRequest
) -> str:
    return view_file_digest(self, request, DefaultLayout(self, request))


@TownApp.html(
    model=File,
    name='sign',
    request_method='POST',
    permission=Private
)
def town_handle_sign(self: File, request: TownRequest) -> str:
    return handle_sign(self, request, DefaultLayout(self, request))
