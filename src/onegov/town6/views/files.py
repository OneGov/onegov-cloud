from babel.core import Locale
from babel.dates import parse_pattern
from functools import lru_cache
from itertools import groupby
from onegov.core.security import Private, Public
from onegov.file import File
from onegov.file.utils import extension_for_content_type
from onegov.org.views.files import view_file_details, \
    view_get_image_collection, view_upload_general_file, \
    view_upload_image_file, view_file_digest, handle_sign, Img, \
    view_get_image_collection_json

from onegov.town6 import _, TownApp
from onegov.core.elements import Link
from onegov.org.layout import DefaultLayout
from onegov.org.models import (
    GeneralFile,
    GeneralFileCollection,
    ImageFileCollection,
    ImageSetCollection,
)

from sedate import to_timezone


@TownApp.html(model=GeneralFileCollection, template='files.pt',
              permission=Private)
def view_town_file_collection(self, request):

    layout = DefaultLayout(self, request)

    request.include('upload')
    request.include('prompt')

    layout.breadcrumbs = [
        Link(_("Homepage"), layout.homepage_url),
        Link(_("Files"), '#')
    ]

    files = tuple(self.files)

    # XXX build somewhat manually for more speed
    locale = Locale.parse(request.locale)
    pattern = parse_pattern(layout.datetime_format)

    @lru_cache(maxsize=len(files) // 4)
    def format_date(date):
        date = to_timezone(date, layout.timezone)
        return pattern.apply(date, locale)

    grouped = tuple(
        (group, tuple(files))
        for group, files in groupby(files, key=lambda f: self.group(f))
    )

    return {
        'layout': layout,
        'title': _('Files'),
        'grouped': grouped,
        'count': len(files),
        'format_date': format_date,
        'model': self,
        'extension': lambda f: extension_for_content_type(
            f.content_type,
            f.name
        ),
        'actions_url': lambda file_id: request.class_link(
            GeneralFile, name="details", variables={'id': file_id}
        ),
        'upload_url': layout.csrf_protected_url(
            request.link(self, name='upload')
        )
    }


@TownApp.html(model=GeneralFile, permission=Private, name='details')
def view_town_file_details(self, request):
    return view_file_details(self, request)


@TownApp.html(model=ImageFileCollection, template='images.pt',
              permission=Private)
def view_town_image_collection(self, request):
    return view_get_image_collection(self, request)
    layout = DefaultLayout(self, request)

    request.include('common')
    request.include('upload')
    request.include('editalttext')

    images = view_get_image_collection_json(
        self, request, produce_image=lambda image: Img.from_image(
            layout, image
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
            attrs={'class': 'new-photo-album'}
        )
    ]

    return {
        'layout': layout,
        'title': _('Images'),
        'images': images,
        'upload_url': layout.csrf_protected_url(
            request.link(self, name='upload')
        )
    }


@TownApp.html(model=GeneralFileCollection, name='upload',
              request_method='POST', permission=Private)
def view_town_upload_general_file(self, request):
    return view_upload_general_file(self, request)


@TownApp.html(model=ImageFileCollection, name='upload',
              request_method='POST', permission=Private)
def view_town_upload_image_file(self, request):
    return view_upload_image_file(self, request)


@TownApp.html(model=GeneralFileCollection, name='digest', permission=Public)
def view_town_file_digest(self, request):
    return view_file_digest(self, request)


@TownApp.html(model=File, name='sign', request_method='POST',
              permission=Private)
def town_handle_sign(self, request):
    return handle_sign(self, request)
