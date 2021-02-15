from onegov.core.security import Public, Private
from onegov.org.views.imagesets import view_imagesets, select_images, \
    handle_select_images, get_form_class, handle_new_imageset, \
    handle_edit_imageset, view_imageset
from onegov.town6 import TownApp
from onegov.org.models import ImageSet, ImageSetCollection


@TownApp.html(model=ImageSetCollection, template='imagesets.pt',
              permission=Public)
def town_view_imagesets(self, request):
    return view_imagesets(self, request)


@TownApp.html(model=ImageSet, name='select', template='select_images.pt',
              permission=Private, request_method='GET')
def town_select_images(self, request):
    return select_images(self, request)


@TownApp.html(model=ImageSet, name='select', template='select_images.pt',
              permission=Private, request_method='POST')
def town_handle_select_images(self, request):
    return handle_select_images(self, request)


@TownApp.form(model=ImageSetCollection, name='new', template='form.pt',
              permission=Private, form=get_form_class)
def town_handle_new_imageset(self, request, form):
    return handle_new_imageset(self, request, form)


@TownApp.form(model=ImageSet, name='edit', template='form.pt',
              permission=Private, form=get_form_class)
def town_handle_edit_imageset(self, request, form):
    return handle_edit_imageset(self, request, form)


@TownApp.html(model=ImageSet, template='imageset.pt', permission=Public)
def town_view_imageset(self, request):
    return view_imageset(self, request)
