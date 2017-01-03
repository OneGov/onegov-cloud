""" The onegov org collection of files uploaded to the site. """

import morepath

from onegov.core.filestorage import view_filestorage_file
from onegov.core.security import Private, Public
from onegov.file import File, FileCollection
from onegov.org import _, OrgApp
from onegov.org.elements import Img, Link
from onegov.org.layout import DefaultLayout
from onegov.org.models import (
    GeneralFile,
    GeneralFileCollection,
    ImageFile,
    ImageFileCollection,
    ImageSetCollection,
    LegacyFile,
    LegacyImage,
)
from sedate import utcnow
from webob import exc


@OrgApp.html(model=GeneralFileCollection, template='files.pt',
             permission=Private)
def view_get_file_collection(self, request):
    request.include('dropzone')

    files = [
        Link(text=f.name, url=request.link(f))
        for f in self.query().order_by(File.name).all()
    ]

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Files"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _('Files'),
        'files': files,
    }


@OrgApp.html(model=ImageFileCollection, template='images.pt',
             permission=Private)
def view_get_image_collection(self, request):
    request.include('common')
    request.include('dropzone')
    request.include('editalttext')

    layout = DefaultLayout(self, request)

    default = ('256', '256')

    def get_thumbnail_size(image):
        if 'thumbnail_small' in image.reference:
            return image.reference.thumbnail_small['size']
        else:
            return default

    images = view_get_image_collection_json(
        self, request, produce_image=lambda image: Img(
            src=request.class_link(File, {'id': image.id}, 'thumbnail'),
            url=request.class_link(File, {'id': image.id}),
            alt=(image.note or '').strip(),
            width=get_thumbnail_size(image)[0],
            height=get_thumbnail_size(image)[1],
            extra=layout.csrf_protected_url(request.link(image, 'note'))
        )
    )

    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Images"), request.link(self))
    ]

    layout.editbar_links = [
        Link(
            text=_("Manage Photo Albums"),
            url=request.class_link(ImageSetCollection),
            classes=('new-photo-album', ))
    ]

    return {
        'layout': layout,
        'title': _('Images'),
        'images': images
    }


@OrgApp.json(model=GeneralFileCollection, permission=Private, name='json')
def view_get_file_collection_json(self, request):
    return [
        {
            'link': request.class_link(File, {'id': id}),
            'title': name
        }
        for id, name in self.query().with_entities(File.id, File.name).all()
    ]


@OrgApp.json(model=ImageFileCollection, permission=Private, name='json')
def view_get_image_collection_json(self, request, produce_image=None):

    if not produce_image:
        def produce_image(image):
            return {
                'thumb': request.class_link(
                    File, {'id': image.id}, 'thumbnail'),
                'image': request.class_link(
                    File, {'id': image.id})
            }

    return [
        {
            'group': request.translate(group),
            'images': tuple(produce_image(image) for group, image in items)
        } for group, items in self.grouped_by_date(id_only=False)
    ]


def handle_file_upload(self, request):
    """ Stores the file given with the request and returns the new file object.

    """

    file = self.add(
        filename=request.params['file'].filename,
        content=request.params['file'].file
    )

    if self.supported_content_types is not 'all':
        if file.reference.content_type not in self.supported_content_types:
            raise exc.HTTPUnsupportedMediaType()

    return file


@OrgApp.view(model=FileCollection, name='upload',
             request_method='POST', permission=Private)
def view_upload_file(self, request):
    request.assert_valid_csrf_token()

    try:
        handle_file_upload(self, request)
    except FileExistsError as e:
        # mark existing files as modified to put them in front of the queue
        e.args[0].modified = utcnow()

    return morepath.redirect(request.link(self))


@OrgApp.json(model=FileCollection, name='upload.json',
             request_method='POST', permission=Private)
def view_upload_file_by_json(self, request):
    request.assert_valid_csrf_token()

    try:
        f = handle_file_upload(self, request)
    except FileExistsError as e:
        # mark existing files as modified to put them in front of the queue
        e.args[0].modified = utcnow()

        return {
            'filelink': request.link(e.args[0]),
            'filename': e.args[0].name
        }
    except exc.HTTPUnsupportedMediaType:
        return {
            'error': True,
            'message': request.translate(_("This file type is not supported"))
        }
    except exc.HTTPRequestHeaderFieldsTooLarge:
        return {
            'error': True,
            'message': request.translate(_("The file name is too long"))
        }

    return {
        'filelink': request.link(f),
        'filename': f.name,
    }


@OrgApp.view(model=LegacyFile, permission=Public)
@OrgApp.view(model=LegacyImage, permission=Public)
def view_old_files_redirect(self, request):
    """ Redirects to the migrated depot file if possible. As a result, old
    image urls are preserved and will continue to function.

    """

    alternate_path = self.path + '.r'

    if request.app.filestorage.isfile(alternate_path):
        with request.app.filestorage.open(alternate_path, 'r') as f:
            id = f.read()

        if isinstance(self, LegacyFile):
            file_class = GeneralFile
        else:
            file_class = ImageFile

        return exc.HTTPMovedPermanently(
            location=request.class_link(file_class, {'id': id}))

    return view_filestorage_file(self, request)
