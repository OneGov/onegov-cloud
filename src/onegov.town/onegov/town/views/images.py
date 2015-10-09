""" The onegov town collection of images uploaded to the site. """
from onegov.core.filestorage import delete_static_file
from onegov.core.security import Private
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Img, Link
from onegov.town.layout import DefaultLayout
from onegov.town.models import ImageCollection, Image


@TownApp.html(model=ImageCollection, template='images.pt', permission=Private)
def view_get_image_collection(self, request):
    request.include('dropzone')

    image_groups = [
        [group, [Img(src=request.link(image.thumbnail),
                     url=request.link(image)) for image in images]]
        for group, images in self.grouped_files()
    ]

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Images"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _('Images'),
        'image_groups': image_groups,
    }


# XXX find a way to switch automatically:
# https://github.com/morepath/morepath/issues/70
@TownApp.json(model=ImageCollection, permission=Private, name='json')
def view_get_image_collection_json(self, request):
    return [
        {
            'group': request.translate(group),
            'images': [{'thumb': request.link(image.thumbnail),
                        'image': request.link(image)} for image in images]
        } for group, images in self.grouped_files()
    ]


@TownApp.view(
    model=Image, request_method='DELETE', permission=Private)
def delete_image(self, request):
    """ Overrides the :meth:`onegov.core.filestorage.delete_static_file` to
    ensure that thumbnails are deleted together with the image.

    """

    delete_static_file(self, request)
    ImageCollection(request.app).delete_file_by_filename(self.filename)
