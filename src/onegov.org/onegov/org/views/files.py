""" The onegov org collection of files uploaded to the site. """

import datetime
import isodate
import morepath
import sedate

from babel.core import Locale
from babel.dates import parse_pattern
from dateutil.parser import parse
from functools import lru_cache
from itertools import groupby
from onegov.core.filestorage import view_filestorage_file
from onegov.core.security import Private, Public
from onegov.core.templates import render_macro
from onegov.file import File, FileCollection
from onegov.file.utils import extension_for_content_type
from onegov.file.errors import AlreadySignedError, InvalidTokenError
from onegov.org import _, OrgApp
from onegov.org.new_elements import Link
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
from onegov.org import utils
from onegov.user import UserCollection
from sedate import to_timezone, utcnow, standardize_date
from time import time
from webob import exc
from uuid import uuid4


def get_thumbnail_size(image):
    if 'thumbnail_small' in image.reference:
        return image.reference.thumbnail_small['size']
    else:
        return ('256', '256')


class Img(object):
    """ Represents an img element. """

    __slots__ = ['src', 'alt', 'title', 'url', 'extra', 'width', 'height']

    def __init__(self, src, alt=None, title=None, url=None, extra=None,
                 width=None, height=None):
        #: The src of the image
        self.src = src

        #: The text for people that can't or won't look at the picture
        self.alt = alt

        #: The title of the image
        self.title = title

        #: The target of this image
        self.url = url

        #: The width of the image in pixel
        self.width = width

        #: The height of the image in pixel
        self.height = height

        #: Extra parameters
        self.extra = extra

    @classmethod
    def from_image(cls, layout, image):
        request = layout.request

        return cls(
            src=request.class_link(File, {'id': image.id}, 'thumbnail'),
            url=request.class_link(File, {'id': image.id}),
            alt=(image.note or '').strip(),
            width=get_thumbnail_size(image)[0],
            height=get_thumbnail_size(image)[1],
            extra=layout.csrf_protected_url(request.link(image, 'note'))
        )


@OrgApp.html(model=GeneralFileCollection, template='files.pt',
             permission=Private)
def view_get_file_collection(self, request):
    request.include('common')
    request.include('upload')
    request.include('prompt')

    layout = DefaultLayout(self, request)
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


@OrgApp.html(model=GeneralFile, permission=Private, name='details')
def view_file_details(self, request):
    layout = DefaultLayout(self, request)
    extension = extension_for_content_type(
        self.reference.content_type,
        self.reference.filename
    )
    color = utils.get_extension_color(extension)

    # IE 11 caches all ajax requests otherwise
    @request.after
    def must_revalidate(response):
        response.headers.add('cache-control', 'must-revalidate')
        response.headers.add('cache-control', 'no-cache')
        response.headers.add('cache-control', 'no-store')
        response.headers['pragma'] = 'no-cache'
        response.headers['expires'] = '0'

    return render_macro(
        layout.macros['file-details'],
        request,
        {
            'id': uuid4().hex,
            'file': self,
            'layout': layout,
            'extension': extension,
            'color': color
        }
    )


@OrgApp.view(model=GeneralFile, permission=Private, name='publish',
             request_method='POST')
def handle_publish(self, request):
    request.assert_valid_csrf_token()
    self.published = True
    self.publish_date = None


@OrgApp.view(model=GeneralFile, permission=Private, name='unpublish',
             request_method='POST')
def handle_unpublish(self, request):
    request.assert_valid_csrf_token()
    self.published = False


@OrgApp.view(model=GeneralFile, permission=Private, name='update-publish-date',
             request_method='POST')
def handle_update_publish_date(self, request):
    request.assert_valid_csrf_token()
    layout = DefaultLayout(self, request)

    if request.params.get('clear', None):
        self.publish_date = None
        return

    try:
        date = parse(request.params['date'], dayfirst=True)
    except (ValueError, KeyError):
        date = self.publish_date and self.publish_date.date()
        date = date or layout.today()

    try:
        hour = next(map(int, request.params.get('hour').split(':')))
    except ValueError:
        hour = self.publish_date and self.publish_date.hour
        hour = hour or 0

    publish_date = datetime.datetime.combine(date, datetime.time(hour, 0))
    publish_date = standardize_date(publish_date, layout.timezone)

    self.publish_date = publish_date


@OrgApp.html(model=ImageFileCollection, template='images.pt',
             permission=Private)
def view_get_image_collection(self, request):
    request.include('common')
    request.include('upload')
    request.include('editalttext')

    layout = DefaultLayout(self, request)

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
def view_upload_file(self, request, return_file=False):
    request.assert_valid_csrf_token()

    try:
        uploaded_file = handle_file_upload(self, request)
    except FileExistsError as e:
        # mark existing files as modified to put them in front of the queue
        uploaded_file = e.args[0]

    if return_file:
        return uploaded_file

    return morepath.redirect(request.link(self))


@OrgApp.html(model=GeneralFileCollection, name='upload',
             request_method='POST', permission=Private)
def view_upload_general_file(self, request):
    uploaded_file = view_upload_file(self, request, return_file=True)
    layout = DefaultLayout(self, request)

    return render_macro(layout.macros['file-info'], request, {
        'file': uploaded_file,
        'format_date': lambda dt: layout.format_date(dt, 'datetime'),
        'actions_url': lambda file_id: request.class_link(
            GeneralFile, name="details", variables={'id': file_id}
        ),
        'extension': lambda file: extension_for_content_type(
            file.reference.content_type,
            file.name
        )
    })


@OrgApp.html(model=ImageFileCollection, name='upload',
             request_method='POST', permission=Private)
def view_upload_image_file(self, request):
    uploaded_file = view_upload_file(self, request, return_file=True)
    layout = DefaultLayout(self, request)

    return render_macro(layout.macros['uploaded_image'], request, {
        'image': Img.from_image(layout, uploaded_file),
        'index': int(time() * 1000),
        'layout': layout
    })


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


@OrgApp.html(model=GeneralFileCollection, name='digest', permission=Public)
def view_file_digest(self, request):
    name = request.params.get('name')
    digest = request.params.get('digest')

    if not name:
        raise exc.HTTPBadRequest("missing filename")

    if not digest:
        raise exc.HTTPBadRequest("missing digest")

    metadata = self.locate_signature_metadata(digest)
    layout = DefaultLayout(self, request)

    return render_macro(layout.macros['digest_result'], request, {
        'layout': layout,
        'name': name,
        'is_known': metadata and True or False,
        'date': metadata and sedate.replace_timezone(
            isodate.parse_datetime(
                metadata['timestamp']
            ), 'UTC'
        ),
    })


@OrgApp.html(model=File, name='sign', request_method='POST',
             permission=Private)
def handle_sign(self, request):
    request.assert_valid_csrf_token()
    token = request.params.get('token')

    user = UserCollection(request.session).by_username(
        request.current_username)

    def may_sign():
        if not token:
            request.alert(_("Please submit your yubikey"))
            return False

        if not user.second_factor:
            request.alert(_("Your account is not linked to a Yubikey"))
            return False

        if not token.startswith(user.second_factor['data']):
            request.alert(_("The used Yubikey is not linked to your account"))
            return False

        return True

    try:
        if may_sign():
            request.app.sign_file(
                file=self,
                signee=request.current_username,
                token=token)

    except AlreadySignedError:
        request.alert(_("This file already has a digital signature"))
    except InvalidTokenError:
        request.alert(_("Your Yubikey could not be validated"))

    layout = DefaultLayout(self, request)

    return render_macro(layout.macros['sign_result'], request, {
        'layout': layout,
        'file': self,
    })


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
