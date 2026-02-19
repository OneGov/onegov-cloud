""" The onegov org collection of files uploaded to the site. """
from __future__ import annotations

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
from onegov.directory.models.directory import DirectoryFile
from onegov.file import File, FileCollection
from onegov.file.integration import (
    render_depot_file,
    view_file, view_file_head,
    view_thumbnail, view_thumbnail_head
)
from onegov.file.utils import extension_for_content_type
from onegov.file.errors import AlreadySignedError, InvalidTokenError
from onegov.org import _, OrgApp
from onegov.core.elements import Link
from onegov.org.layout import (
    DefaultLayout, GeneralFileCollectionLayout, ImageFileCollectionLayout)
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
from sedate import to_timezone, utcnow, standardize_date
from time import time
from webob import exc
from uuid import uuid4


from typing import overload, Any, Literal, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from depot.io.interfaces import StoredFile
    from onegov.core.types import JSON_ro, RenderData
    from onegov.org.models.file import BaseImageFileCollection
    from onegov.org.request import OrgRequest
    from typing import TypeVar
    from webob import Response

    FileT = TypeVar('FileT', bound=File)


def get_thumbnail_size(image: ImageFile) -> tuple[str, str]:
    if 'thumbnail_small' in image.reference:
        return image.reference.thumbnail_small['size']
    else:
        return ('256', '256')


class Img:
    """ Represents an img element. """

    __slots__ = ('src', 'alt', 'title', 'url', 'extra', 'width', 'height')

    def __init__(
        self,
        src: str,
        alt: str | None = None,
        title: str | None = None,
        url: str | None = None,
        extra: str | None = None,
        width: str | None = None,
        height: str | None = None
    ) -> None:
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
    def from_image(
        cls,
        layout: DefaultLayout,
        image: ImageFile
    ) -> Self:

        request = layout.request
        width, height = get_thumbnail_size(image)

        return cls(
            src=request.class_link(File, {'id': image.id}, 'thumbnail'),
            url=request.class_link(File, {'id': image.id}),
            alt=(image.note or '').strip(),
            width=width,
            height=height,
            extra=layout.csrf_protected_url(request.link(image, 'note'))
        )


@OrgApp.html(model=GeneralFileCollection, template='files.pt',
             permission=Private)
def view_get_file_collection(
    self: GeneralFileCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    layout = layout or GeneralFileCollectionLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Files'), '#')
    ]

    files = tuple(self.files)

    # XXX build somewhat manually for more speed
    locale = Locale.parse(request.locale)
    pattern = parse_pattern(layout.datetime_format)

    @lru_cache(maxsize=len(files) // 4)
    def format_date(date: datetime.datetime) -> str:
        if not date:
            return '-'

        date = to_timezone(date, layout.timezone)
        return pattern.apply(date, locale)

    grouped = tuple(
        (group, tuple(files))
        for group, files in groupby(files, key=self.group)
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
            GeneralFile, name='details', variables={'id': file_id}
        ),
        'upload_url': layout.csrf_protected_url(
            request.link(self, name='upload')
        )
    }


@OrgApp.html(model=GeneralFile, permission=Private, name='details')
def view_file_details(
    self: GeneralFile,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> str:

    layout = layout or DefaultLayout(self, request)
    extension = extension_for_content_type(
        self.reference.content_type,
        self.reference.filename
    )
    color = utils.get_extension_color(extension)

    # IE 11 caches all ajax requests otherwise
    @request.after
    def must_revalidate(response: Response) -> None:
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


@OrgApp.html(model=GeneralFile, permission=Private, name='links')
def view_file_links(
    self: GeneralFile,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> str:

    layout = layout or DefaultLayout(self, request)

    # IE 11 caches all ajax requests otherwise
    @request.after
    def must_revalidate(response: Response) -> None:
        response.headers.add('cache-control', 'must-revalidate')
        response.headers.add('cache-control', 'no-cache')
        response.headers.add('cache-control', 'no-store')
        response.headers['pragma'] = 'no-cache'
        response.headers['expires'] = '0'

    return render_macro(
        layout.macros['file-links'],
        request,
        {
            'file': self,
            'layout': layout,
        }
    )


@OrgApp.view(model=GeneralFile, permission=Private, name='publish',
             request_method='POST')
def handle_publish(self: GeneralFile, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    self.published = True
    self.publish_end_date = None
    self.publish_date = None


@OrgApp.view(model=GeneralFile, permission=Private, name='unpublish',
             request_method='POST')
def handle_unpublish(self: GeneralFile, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    self.published = False


@OrgApp.view(model=GeneralFile, permission=Private, name='toggle-publication',
             request_method='POST')
def toggle_publication(self: GeneralFile, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    self.publication = not self.publication


@OrgApp.view(model=GeneralFile, permission=Private, name='update-publish-date',
             request_method='POST')
def handle_update_publish_date(
    self: GeneralFile,
    request: OrgRequest
) -> None:

    request.assert_valid_csrf_token()
    layout = DefaultLayout(self, request)
    if request.params.get('clear_start_date', None):
        self.publish_date = None
        return
    if request.params.get('clear_end_date', None):
        self.publish_end_date = None
        return

    handle_update_start_date(layout, request, self)
    handle_update_end_date(layout, request, self)


def handle_update_start_date(
    layout: DefaultLayout,
    request: OrgRequest,
    self: GeneralFile
) -> None:

    # FIXME: Validating the contents of request.params using try/except is
    #        rather inelegant and slow, we should write robust parsing logic
    #        that can deal with malformed data gracefully and then reuse it
    #        for end_date
    params: Any = request.params
    date: datetime.date | None
    hour: int | None
    try:
        # dates are returned as 2019-01-31
        date = parse(params['date'], dayfirst=False)
        hour = next(map(int, params['hour'].split(':')))
        if not date and not hour:
            return
    except (ValueError, KeyError, AttributeError):
        date = self.publish_date.date() if self.publish_date else None
        date = date or layout.today()

    try:
        hour = next(map(int, params['hour'].split(':')))
    except (ValueError, KeyError, AttributeError):
        hour = self.publish_date.hour if self.publish_date else 0

    publish_date = datetime.datetime.combine(date, datetime.time(hour, 0))
    publish_date = standardize_date(publish_date, layout.timezone)
    self.publish_date = publish_date


def handle_update_end_date(
    layout: DefaultLayout,
    request: OrgRequest,
    self: GeneralFile
) -> None:

    # FIXME: same issue as with start_date
    params: Any = request.params
    end_date: datetime.date | None
    end_hour: int | None
    try:
        end_date = parse(params['end-date'], dayfirst=False)
    except (ValueError, KeyError, AttributeError):
        self.publish_end_date = None
        return
    try:
        end_hour = next(
            map(int, params['end-hour'].split(':'))
        )
    except (ValueError, KeyError, AttributeError):
        end_hour = self.publish_end_date.hour if self.publish_end_date else 0

    publish_end_date = datetime.datetime.combine(
        end_date, datetime.time(end_hour, 0)
    )
    try:
        publish_end_date = standardize_date(
            publish_end_date, layout.timezone
        )
        # Prevent adding invalid date range:
        if not self.publish_date or self.publish_date < publish_end_date:
            self.publish_end_date = publish_end_date
    except OverflowError:
        self.publish_end_date = None


@OrgApp.html(model=ImageFileCollection, template='images.pt',
             permission=Private)
def view_get_image_collection(
    self: BaseImageFileCollection[Any],
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> RenderData:

    layout = layout or ImageFileCollectionLayout(self, request)

    images = view_get_image_collection_json(
        self, request, produce_image=lambda image: Img.from_image(
            layout, image
        )
    )

    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Images'), request.link(self))
    ]

    layout.editbar_links = [
        Link(
            text=_('Manage Photo Albums'),
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
def view_get_file_collection_json(
    self: GeneralFileCollection,
    request: OrgRequest
) -> JSON_ro:
    return [
        {
            'link': request.class_link(File, {'id': id}),
            'title': name
        }
        for id, name in self.query().with_entities(
            File.id, File.name).order_by(File.name).all()
    ]


@OrgApp.json(model=ImageFileCollection, permission=Private, name='json')
def view_get_image_collection_json(
    self: BaseImageFileCollection[Any],
    request: OrgRequest,
    produce_image: Callable[[ImageFile], Any] | None = None
) -> list[dict[str, Any]]:

    if not produce_image:
        def produce_image(image: ImageFile) -> JSON_ro:
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


def handle_file_upload(
    self: FileCollection[FileT],
    request: OrgRequest
) -> FileT:
    """ Stores the file given with the request and returns the new file object.

    """

    fs = request.params['file']
    assert not isinstance(fs, str)

    file = self.add(
        filename=fs.filename,
        content=fs.file
    )

    supported_content_types = getattr(self, 'supported_content_types', WhitelistedMimeType.whitelist)

    if supported_content_types != 'all':
        if file.reference.content_type not in supported_content_types:
            # Fail the post request from upload.js with status code 415
            # (Unsupported Media Type). Raising the HTTP exception here causes
            # the request transaction to abort and roll back any previous
            # changes (including the `self.add(...)` above), so the file won't
            # be persisted if the content type is unsupported.
            raise exc.HTTPUnsupportedMediaType()

    return file


@overload
def view_upload_file(
    self: FileCollection[FileT],
    request: OrgRequest,
    return_file: Literal[True]
) -> FileT: ...


@overload
def view_upload_file(
    self: FileCollection[FileT],
    request: OrgRequest,
    return_file: Literal[False] = False
) -> Response: ...


@OrgApp.view(model=FileCollection, name='upload',
             request_method='POST', permission=Private)
def view_upload_file(
    self: FileCollection[Any],
    request: OrgRequest,
    return_file: bool = False
) -> Response | File:

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
def view_upload_general_file(
    self: GeneralFileCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> str:

    uploaded_file = view_upload_file(self, request, return_file=True)
    layout = layout or DefaultLayout(self, request)

    return render_macro(layout.macros['file-info'], request, {
        'file': uploaded_file,
        'format_date': lambda dt: layout.format_date(dt, 'datetime'),
        'actions_url': lambda file_id: request.class_link(
            GeneralFile, name='details', variables={'id': file_id}
        ),
        'extension': lambda file: extension_for_content_type(
            file.reference.content_type,
            file.name
        )
    })


@OrgApp.html(model=ImageFileCollection, name='upload',
             request_method='POST', permission=Private)
def view_upload_image_file(
    self: ImageFileCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> str:

    uploaded_file = view_upload_file(self, request, return_file=True)
    layout = layout or DefaultLayout(self, request)

    return render_macro(layout.macros['uploaded_image'], request, {
        'image': Img.from_image(layout, uploaded_file),
        'index': int(time() * 1000),
        'layout': layout
    })


@OrgApp.json(model=FileCollection, name='upload.json',
             request_method='POST', permission=Private)
def view_upload_file_by_json(
    self: FileCollection[Any],
    request: OrgRequest
) -> JSON_ro:

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
            'message': request.translate(_('This file type is not supported'))
        }
    except exc.HTTPRequestHeaderFieldsTooLarge:
        return {
            'error': True,
            'message': request.translate(_('The file name is too long'))
        }
    except ValueError:
        return {
            'error': True,
            'message': request.translate(_('The file cannot be processed'))
        }

    return {
        'filelink': request.link(f),
        'filename': f.name,
    }


@OrgApp.html(model=GeneralFileCollection, name='digest', permission=Public)
def view_file_digest(
    self: GeneralFileCollection,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> str:

    name = request.params.get('name')
    digest = request.params.get('digest')

    if not isinstance(name, str) or not name:
        raise exc.HTTPBadRequest('missing filename')

    if not isinstance(digest, str) or not digest:
        raise exc.HTTPBadRequest('missing digest')

    metadata = self.locate_signature_metadata(digest)
    layout = layout or DefaultLayout(self, request)

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
def handle_sign(
    self: File,
    request: OrgRequest,
    layout: DefaultLayout | None = None
) -> str:

    request.assert_valid_csrf_token()
    token = request.params.get('token')

    user = request.current_user
    assert user is not None

    if not isinstance(token, str) or not token:
        request.alert(_('Please submit your yubikey'))

    elif not user.second_factor:
        request.alert(_('Your account is not linked to a Yubikey'))

    elif not token.startswith(user.second_factor['data']):
        request.alert(_('The used Yubikey is not linked to your account'))

    else:
        try:
            request.app.sign_file(
                file=self,
                signee=user.username,
                token=token)

        except AlreadySignedError:
            request.alert(_('This file already has a digital seal'))
        except InvalidTokenError:
            request.alert(_('Your Yubikey could not be validated'))

    layout = layout or DefaultLayout(self, request)

    return render_macro(layout.macros['sign_result'], request, {
        'layout': layout,
        'file': self,
    })


@OrgApp.view(model=LegacyFile, permission=Public)
@OrgApp.view(model=LegacyImage, permission=Public)
def view_old_files_redirect(
    self: LegacyFile | LegacyImage,
    request: OrgRequest
) -> Response | str:
    """ Redirects to the migrated depot file if possible. As a result, old
    image urls are preserved and will continue to function.

    """
    fs = request.app.filestorage
    assert fs is not None

    alternate_path = self.path + '.r'

    if fs.isfile(alternate_path):
        with fs.open(alternate_path, 'r') as f:
            id = f.read()

        file_class: type[ImageFile | GeneralFile]
        if isinstance(self, LegacyImage):
            file_class = ImageFile
        else:
            file_class = GeneralFile

        return exc.HTTPMovedPermanently(
            location=request.class_link(file_class, {'id': id}))

    return view_filestorage_file(self, request)


# we override the generic file views for DirectoryFile, in order to respect
# mTAN access. This is not a complete solution and there's arguably other
# cases that should be looked at, but DirectoryFile is a really simple case
# where the solution is obvious, so we fix it.
def assert_has_mtan_access(self: DirectoryFile, request: OrgRequest) -> None:
    if request.is_manager:
        # no restriction for admins/editors
        return

    if (
        getattr(self.directory_entry, 'access', '').endswith('mtan')
        and not request.active_mtan_session
    ):
        raise exc.HTTPForbidden()


@OrgApp.view(model=DirectoryFile, render=render_depot_file, permission=Public)
def view_directory_file(
    self: DirectoryFile,
    request: OrgRequest
) -> StoredFile:

    assert_has_mtan_access(self, request)
    return view_file(self, request)


@OrgApp.view(model=DirectoryFile, name='thumbnail', permission=Public,
             render=render_depot_file)
@OrgApp.view(model=DirectoryFile, name='small', permission=Public,
             render=render_depot_file)
@OrgApp.view(model=DirectoryFile, name='medium', permission=Public,
             render=render_depot_file)
def view_directory_thumbnail(
    self: DirectoryFile,
    request: OrgRequest
) -> StoredFile | Response:

    assert_has_mtan_access(self, request)
    return view_thumbnail(self, request)


@OrgApp.view(model=DirectoryFile, render=render_depot_file, permission=Public,
             request_method='HEAD')
def view_directory_file_head(
    self: DirectoryFile,
    request: OrgRequest
) -> StoredFile:

    assert_has_mtan_access(self, request)
    return view_file_head(self, request)


@OrgApp.view(model=DirectoryFile, name='thumbnail', render=render_depot_file,
             permission=Public, request_method='HEAD')
@OrgApp.view(model=DirectoryFile, name='small', render=render_depot_file,
             permission=Public, request_method='HEAD')
@OrgApp.view(model=DirectoryFile, name='medium', render=render_depot_file,
             permission=Public, request_method='HEAD')
def view_directory_thumbnail_head(
    self: DirectoryFile,
    request: OrgRequest
) -> StoredFile | Response:

    assert_has_mtan_access(self, request)
    return view_thumbnail_head(self, request)
