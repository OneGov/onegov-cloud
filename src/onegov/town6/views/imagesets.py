from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.org.views.imagesets import (
    view_imagesets, select_images, handle_select_images, get_form_class,
    handle_new_imageset, handle_edit_imageset, view_imageset)
from onegov.town6 import TownApp
from onegov.org.models import ImageSet, ImageSetCollection
from onegov.town6.layout import ImageSetCollectionLayout, ImageSetLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.forms import ImageSetForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(
    model=ImageSetCollection,
    template='imagesets.pt',
    permission=Public
)
def town_view_imagesets(
    self: ImageSetCollection,
    request: TownRequest
) -> RenderData:
    return view_imagesets(
        self, request, ImageSetCollectionLayout(self, request))


@TownApp.html(
    model=ImageSet,
    name='select',
    template='select_images.pt',
    permission=Private,
    request_method='GET'
)
def town_select_images(self: ImageSet, request: TownRequest) -> RenderData:
    return select_images(self, request, ImageSetLayout(self, request))


@TownApp.html(
    model=ImageSet,
    name='select',
    template='select_images.pt',
    permission=Private,
    request_method='POST'
)
def town_handle_select_images(
    self: ImageSet,
    request: TownRequest
) -> Response:
    """ No layout passing needed, since it returns a redirect """
    return handle_select_images(self, request)


@TownApp.form(
    model=ImageSetCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_form_class
)
def town_handle_new_imageset(
    self: ImageSetCollection,
    request: TownRequest,
    form: ImageSetForm
) -> RenderData | Response:
    return handle_new_imageset(
        self, request, form, ImageSetCollectionLayout(self, request))


@TownApp.form(
    model=ImageSet,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_form_class
)
def town_handle_edit_imageset(
    self: ImageSet,
    request: TownRequest,
    form: ImageSetForm
) -> RenderData | Response:
    return handle_edit_imageset(
        self, request, form, ImageSetLayout(self, request))


@TownApp.html(model=ImageSet, template='imageset.pt', permission=Public)
def town_view_imageset(self: ImageSet, request: TownRequest) -> RenderData:
    return view_imageset(self, request, ImageSetLayout(self, request))
