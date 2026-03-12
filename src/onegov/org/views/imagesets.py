from __future__ import annotations

import morepath

from onegov.core.security import Public, Private
from onegov.file import File
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms import ImageSetForm
from onegov.org.layout import ImageSetLayout, ImageSetCollectionLayout
from onegov.org.models import (
    ImageFile,
    ImageSet,
    ImageSetCollection,
    ImageFileCollection
)
from purl import URL


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response


def get_form_class(
    self: ImageSet | ImageSetCollection,
    request: OrgRequest
) -> type[ImageSetForm]:

    if isinstance(self, ImageSetCollection):
        model = ImageSet()
    else:
        model = self

    return model.with_content_extensions(ImageSetForm, request)


@OrgApp.html(model=ImageSetCollection, template='imagesets.pt',
             permission=Public)
def view_imagesets(
    self: ImageSetCollection,
    request: OrgRequest,
    layout: ImageSetCollectionLayout | None = None
) -> RenderData:

    # XXX add collation support to the core (create collations automatically)
    imagesets = sorted(self.query(), key=lambda d: d.created, reverse=True)

    return {
        'layout': layout or ImageSetCollectionLayout(self, request),
        'title': _('Photo Albums'),
        'imagesets': request.exclude_invisible(imagesets)
    }


@OrgApp.html(model=ImageSet, name='select', template='select_images.pt',
             permission=Private, request_method='GET')
def select_images(
    self: ImageSet,
    request: OrgRequest,
    layout: ImageSetLayout | None = None
) -> RenderData:

    collection = ImageFileCollection(request.session)
    selected = {f.id for f in self.files}

    def produce_image(id: str) -> dict[str, Any]:
        return {
            'id': id,
            'src': request.class_link(File, {'id': id}, 'thumbnail'),
            'selected': id in selected
        }

    images = [
        {
            'group': request.translate(group),
            'images': tuple(produce_image(id) for group, id in items)
        } for group, items in collection.grouped_by_date()
    ]

    layout = layout or ImageSetLayout(self, request)
    layout.breadcrumbs.append(Link(_('Select'), '#'))

    action = URL(request.link(self, 'select')).query_param(
        'csrf-token', request.new_csrf_token())

    return {
        'layout': layout,
        'title': _('Select images'),
        'images': images,
        'action': action
    }


@OrgApp.html(model=ImageSet, name='select', template='select_images.pt',
             permission=Private, request_method='POST')
def handle_select_images(self: ImageSet, request: OrgRequest) -> Response:

    # we do custom form handling here, so we need to check for CSRF manually
    request.assert_valid_csrf_token()

    if not request.POST:
        self.files = []
    else:
        # NOTE: we could write this as list(query) to get around the invariance
        #       restriction on list, but I worry that .all() performs better
        #       so it's probably better to just ignore the type error
        self.files = (
            request.session.query(ImageFile)  # type:ignore[assignment]
            .filter(ImageFile.id.in_(request.POST))
            .all()
        )

    request.success(_('Your changes were saved'))

    return morepath.redirect(request.link(self))


@OrgApp.form(model=ImageSetCollection, name='new', template='form.pt',
             permission=Private, form=get_form_class)
def handle_new_imageset(
    self: ImageSetCollection,
    request: OrgRequest,
    form: ImageSetForm,
    layout: ImageSetCollectionLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        assert form.title.data is not None
        imageset = self.add(title=form.title.data)
        form.populate_obj(imageset)
        request.success(_('Added a new photo album'))

        return morepath.redirect(request.link(imageset))

    layout = layout or ImageSetCollectionLayout(self, request)
    layout.include_editor()
    layout.breadcrumbs.append(Link(_('New'), '#'))

    return {
        'layout': layout,
        'title': _('New Photo Album'),
        'form': form,
    }


@OrgApp.form(model=ImageSet, name='edit', template='form.pt',
             permission=Private, form=get_form_class)
def handle_edit_imageset(
    self: ImageSet,
    request: OrgRequest,
    form: ImageSetForm,
    layout: ImageSetLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)

        request.success(_('Your changes were saved'))
        return morepath.redirect(request.link(self))

    elif not request.POST:
        form.process(obj=self)

    layout = layout or ImageSetLayout(self, request)
    layout.include_editor()
    layout.breadcrumbs.append(Link(_('Edit'), '#'))

    return {
        'layout': layout,
        'title': self.title,
        'form': form
    }


@OrgApp.view(model=ImageSet, request_method='DELETE', permission=Private)
def handle_delete_imageset(self: ImageSet, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()

    collection = ImageSetCollection(request.session)
    collection.delete(self)


@OrgApp.html(model=ImageSet, template='imageset.pt', permission=Public)
def view_imageset(
    self: ImageSet,
    request: OrgRequest,
    layout: ImageSetLayout | None = None
) -> RenderData:

    return {
        'layout': layout or ImageSetLayout(self, request),
        'title': self.title,
        'imageset': self
    }
