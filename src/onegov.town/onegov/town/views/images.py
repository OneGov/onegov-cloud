""" The onegov town collection of images uploaded to the site. """

import morepath

from onegov.core.filestorage import random_filename
from onegov.core.security import Private
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Image, Link
from onegov.town.layout import DefaultLayout
from onegov.town.model import ImageCollection
from webob.exc import HTTPUnsupportedMediaType


@TownApp.html(model=ImageCollection, template='images.pt', permission=Private)
def view_get_image_collection(self, request):
    request.include('dropzone')

    images = [
        Image(request.filestorage_link(self.path_prefix + image))
        for image in self.filestorage.listdir(files_only=True)
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


def handle_file_upload(self, request):
    """ Stores the file given with the request and returns the url to the
    resulting file.

    """
    extension = request.params['file'].filename.split('.')[-1]

    if extension not in {'png', 'jpg', 'jpeg', 'gif', 'svg'}:
        raise HTTPUnsupportedMediaType()

    filename = '.'.join((random_filename(), extension))

    self.filestorage.setcontents(filename, request.params['file'].file.read())

    return request.filestorage_link(self.path_prefix + filename)


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
