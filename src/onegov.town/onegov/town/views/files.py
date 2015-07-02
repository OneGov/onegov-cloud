""" The onegov town collection of files uploaded to the site. """

import base64
import morepath

from onegov.core.filestorage import random_filename
from onegov.core.security import Private
from onegov.town import _
from onegov.town.app import TownApp
from onegov.town.elements import Link
from onegov.town.layout import DefaultLayout
from onegov.town.models import FileCollection


@TownApp.html(model=FileCollection, template='files.pt', permission=Private)
def view_get_file_collection(self, request):
    request.include('dropzone')

    files = [
        Link(text=file_.original_name, url=request.link(file_))
        for file_ in self.files
    ]

    layout = DefaultLayout(self, request)
    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Files"), request.link(self))
    ]

    return {
        'layout': layout,
        'title': _(u'Files'),
        'files': files,
    }


@TownApp.json(model=FileCollection, permission=Private, name='json')
def view_get_file_collection_json(self, request):
    return [
        {
            'link': request.link(file_),
            'title': file_.original_name.decode('utf-8')
        }
        for file_ in self.files
    ]


def handle_file_upload(self, request):
    """ Stores the file given with the request and returns the url to the
    resulting file.

    """

    extension = request.params['file'].filename.split('.')[-1]
    name = request.params['file'].filename.encode('utf-8')
    # Pad with whitespace to avoid '=' padding in base64 encoded value.
    if len(name) % 3 != 0:
        name = name.ljust(len(name) + (3 - len(name) % 3))
    name = base64.urlsafe_b64encode(name).decode('utf-8')

    filename = '{}-{}.{}'.format(name, random_filename(), extension)

    return self.store_file(request.params['file'].file, filename)


@TownApp.view(model=FileCollection, name='upload', request_method='POST',
              permission=Private)
def view_upload_file(self, request):
    request.assert_valid_csrf_token()

    handle_file_upload(self, request)

    return morepath.redirect(request.link(self))


@TownApp.json(model=FileCollection, name='upload.json', request_method='POST',
              permission=Private)
def view_upload_file_by_json(self, request):
    request.assert_valid_csrf_token()

    file_ = handle_file_upload(self, request)

    return {
        'filelink': request.link(file_),
        'filename': file_.original_name.decode('utf-8'),
    }
