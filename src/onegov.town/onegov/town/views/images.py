""" The onegov town collection of images uploaded to the site. """

import morepath

from onegov.core.filestorage import delete_static_file, random_filename
from onegov.core.security import Private
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Img, Link
from onegov.town.layout import DefaultLayout
from onegov.town.models import ImageCollection, Image


@TownApp.html(model=ImageCollection, template='images.pt', permission=Private)
def view_get_image_collection(self, request):
    request.include('dropzone')

    images = [
        Img(src=request.link(image.thumbnail), url=request.link(image))
        for image in self.images
    ]

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Images"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _(u'Images'),
        'images': images,
    }


# XXX find a way to switch automatically:
# https://github.com/morepath/morepath/issues/70
@TownApp.json(model=ImageCollection, permission=Private, name='json')
def view_get_image_collection_json(self, request):
    return [
        {'thumb': request.link(image.thumbnail), 'image': request.link(image)}
        for image in self.images
    ]


def handle_file_upload(self, request):
    """ Stores the file given with the request and returns the url to the
    resulting file.

    """

    filename = '.'.join((
        random_filename(), request.params['file'].filename.split('.')[-1]
    ))

    image = self.store_image(request.params['file'].file, filename)

    return request.link(image)


@TownApp.view(model=ImageCollection, name='upload', request_method='POST',
              permission=Private)
def view_upload_file(self, request):
    request.assert_valid_csrf_token()

    handle_file_upload(self, request)

    return morepath.redirect(request.link(self))


@TownApp.json(model=ImageCollection, name='upload.json', request_method='POST',
              permission=Private)
def view_upload_file_by_json(self, request):
    request.assert_valid_csrf_token()

    return {'filelink': handle_file_upload(self, request)}


@TownApp.view(
    model=Image, request_method='DELETE', permission=Private)
def delete_image(self, request):
    """ Overrides the :meth:`onegov.core.filestorage.delete_static_file` to
    ensure that thumbnails are deleted together with the image.

    """

    delete_static_file(self, request)
    ImageCollection(request.app).delete_image_by_filename(self.filename)
