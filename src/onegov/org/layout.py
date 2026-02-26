from __future__ import annotations

import numbers

import babel.dates
import re

from babel import Locale
from datetime import date, datetime, time, timedelta
from dateutil import rrule
from dateutil.rrule import rrulestr
from decimal import Decimal
from functools import cached_property
from markupsafe import Markup
from math import isclose
from os.path import splitext, basename

from onegov.chat import TextModuleCollection
from onegov.core import Framework
from onegov.core.crypto import RANDOM_TOKEN_LENGTH
from onegov.core.custom import json
from onegov.core.elements import Block, Button, Confirm, Intercooler
from onegov.core.elements import Link, LinkGroup
from onegov.core.framework import layout_predicate
from onegov.form.collection import SurveyCollection
from onegov.org.elements import QrCodeLink, IFrameLink
from onegov.core.i18n import SiteLocale
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.core.utils import linkify, paragraphify
from onegov.directory import DirectoryCollection, Directory, DirectoryEntry
from onegov.event import Event
from onegov.event import Occurrence
from onegov.event import OccurrenceCollection
from onegov.file import File
from onegov.form import as_internal_id
from onegov.form import FormCollection
from onegov.form import FormDefinition
from onegov.org.models.document_form import (
    FormDocument,
    FormDocumentCollection)
from onegov.newsletter import Newsletter
from onegov.newsletter import NewsletterCollection
from onegov.newsletter import RecipientCollection
from onegov.org import _
from onegov.org import utils
from onegov.org.app import OrgApp
from onegov.org.exports.base import OrgExport
from onegov.org.models import CitizenDashboard
from onegov.org.models import Clipboard
from onegov.org.models import ExportCollection, Editor
from onegov.org.models import GeneralFile
from onegov.org.models import GeneralFileCollection
from onegov.org.models import ImageFile
from onegov.org.models import ImageFileCollection
from onegov.org.models import ImageSet
from onegov.org.models import ImageSetCollection
from onegov.org.models import News
from onegov.org.models import PageMove
from onegov.org.models import PersonMove
from onegov.org.models import PublicationCollection
from onegov.org.models import ResourceRecipientCollection
from onegov.org.models import Search
from onegov.org.models import SiteCollection
from onegov.org.models import Topic
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.org.models.extensions import PersonLinkExtension
from onegov.org.models.external_link import ExternalLinkCollection
from onegov.org.models.form import submission_deletable
from onegov.org.open_graph import OpenGraphMixin
from onegov.org.theme.org_theme import user_options
from onegov.org.utils import IMG_URLS, get_current_tickets_url
from onegov.pay import PaymentCollection, PaymentProviderCollection
from onegov.people import PersonCollection, Person
from onegov.qrcode import QrCode
from onegov.reservation import Resource
from onegov.reservation import ResourceCollection
from onegov.ticket import Ticket
from onegov.ticket import TicketCollection, TicketInvoiceCollection
from onegov.ticket.collection import ArchivedTicketCollection
from onegov.user import Auth, User, UserCollection, UserGroupCollection
from onegov.user.utils import password_reset_url
from operator import itemgetter
from sedate import to_timezone
from translationstring import TranslationString

from typing import overload, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from chameleon import PageTemplateFile
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from onegov.core.elements import Trait
    from onegov.core.elements import Link as BaseLink
    from onegov.core.orm.abstract import AdjacencyList
    from onegov.core.security.permissions import Intent
    from onegov.core.templates import MacrosLookup
    from onegov.directory import DirectoryEntryCollection
    from onegov.form import FormSubmission
    from onegov.form.models.definition import (
        SurveySubmission, SurveyDefinition)
    from onegov.org.models import (
        ExtendedDirectory, ExtendedDirectoryEntry, Organisation)
    from onegov.org.request import OrgRequest
    from onegov.org.request import PageMeta
    from onegov.user import UserGroup
    from sedate.types import TzInfoOrName
    from typing import TypeAlias, TypeVar
    from webob import Response
    from wtforms import Field

    _T = TypeVar('_T')

    AnyFormDefinitionOrCollection: TypeAlias = (
        FormDefinition | FormCollection | SurveyCollection | SurveyDefinition
        | FormDocumentCollection | FormDocument)


capitalised_name = re.compile(r'[A-Z]{1}[a-z]+')


class Layout(ChameleonLayout, OpenGraphMixin):
    """ Contains methods to render a page inheriting from layout.pt.

    All pages inheriting from layout.pt rely on this class being present
    as 'layout' variable::

     @OrgApp.html(model=Example, template='example.pt', permission=Public)
        def view_example(self, request):
            return { 'layout': DefaultLayout(self, request) }

    It is meant to be extended for different parts of the site. For example,
    the :class:`DefaultLayout` includes the top navigation defined by
    onegov.page.

    It's possible though to have a different part of the website use a
    completely different top navigation. For that, a new Layout class
    inheriting from this one should be added.

    """

    app: OrgApp
    request: OrgRequest

    date_long_without_year_format = 'E d. MMMM'
    datetime_long_without_year_format = 'E d. MMMM HH:mm'
    datetime_short_format = 'E d.MM.Y HH:mm'
    event_format = 'EEEE, d. MMMM YYYY'
    event_short_format = 'EE d. MMMM YYYY'
    isodate_format = 'y-M-d'

    def has_model_permission(self, permission: type[Intent] | None) -> bool:
        return self.request.has_permission(self.model, permission)

    @property
    def name(self) -> str:
        """ Takes the class name of the layout and generates a name which
        can be used as a class. """

        return '-'.join(
            token.lower() for token in capitalised_name.findall(
                self.__class__.__name__
            )
        )

    @property
    def org(self) -> Organisation:
        """ An alias for self.request.app.org. """
        return self.request.app.org

    @property
    def primary_color(self) -> str:
        return (self.org.theme_options or {}).get(
            'primary-color', user_options['primary-color'])

    @cached_property
    def favicon_apple_touch_url(self) -> str | None:
        return self.app.org.favicon_apple_touch_url

    @cached_property
    def favicon_pinned_tab_safari_url(self) -> str | None:
        return self.app.org.favicon_pinned_tab_safari_url

    @cached_property
    def favicon_win_url(self) -> str | None:
        return self.app.org.favicon_win_url

    @cached_property
    def favicon_mac_url(self) -> str | None:
        return self.app.org.favicon_mac_url

    @cached_property
    def default_map_view(self) -> dict[str, Any]:
        return self.org.default_map_view or {
            'lon': 8.30576869173879,
            'lat': 47.05183585,
            'zoom': 12
        }

    @cached_property
    def svg(self) -> PageTemplateFile:
        return self.template_loader['svg.pt']

    @cached_property
    def font_awesome_path(self) -> str:
        return self.request.link(StaticFile(
            'font-awesome/css/font-awesome.min.css',
            version=self.app.version
        ))

    @cached_property
    def sentry_init_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'sentry/js/sentry-init.js'
        )
        return self.request.link(static_file)

    def static_file_path(self, path: str) -> str:
        return self.request.link(StaticFile(path, version=self.app.version))

    def with_hashtags(self, text: str | None) -> Markup | None:
        if text is None:
            return None

        return utils.hashtag_elements(self.request, text)

    @cached_property
    def page_id(self) -> str:
        """ Returns the unique page id of the rendered page. Used to have
        a useful id in the body element for CSS/JS.

        """
        page_id = self.request.path_info
        assert page_id is not None
        page_id = page_id.lstrip('/')
        page_id = page_id.replace('/', '-')
        page_id = page_id.replace('+', '')
        page_id = page_id.rstrip('-')

        return 'page-' + (page_id or 'root')

    @cached_property
    def body_classes(self) -> Iterator[str]:
        """ Yields a list of body classes used on the body. """

        if self.request.is_logged_in:
            yield 'is-logged-in'
            yield 'role-{}'.format(self.request.current_role)
        else:
            yield 'is-logged-out'

        yield self.name

    @cached_property
    def top_navigation(self) -> Sequence[Link] | None:
        """ Returns a list of :class:`onegov.org.elements.Link` objects.
        Those links are used for the top navigation.

        If nothing is returned, no top navigation is displayed.

        """
        return None

    @cached_property
    def breadcrumbs(self) -> Sequence[Link] | None:
        """ Returns a list of :class:`onegov.org.elements.Link` objects.
        Those links are used for the breadcrumbs.

        If nothing is returned, no top breadcrumbs are displayed.

        """
        return None

    @cached_property
    def sidebar_links(self) -> Sequence[Link | LinkGroup] | None:
        """ A list of links shown in the sidebar, used for navigation. """
        return None

    @cached_property
    def editbar_links(self) -> Sequence[BaseLink | LinkGroup] | None:
        """ A of :class:`onegov.org.elements.LinkGroup` classes. Each of them
        will be shown in the top editbar, with the group title being the
        dropdown title.
        """
        return None

    @cached_property
    def locales(self) -> list[tuple[str, str]]:
        to = self.request.url

        def get_name(locale: str) -> str:
            language_name = Locale.parse(locale).get_language_name()
            if language_name is None:
                # fallback to just the locale name
                return locale
            return language_name.capitalize()

        def get_link(locale: str) -> str:
            return SiteLocale(locale).link(self.request, to)

        return [
            (get_name(locale), get_link(locale))
            for locale in sorted(self.app.locales)
        ]

    @cached_property
    def files_url(self) -> str:
        """ Returns the url to the files view. """
        url = self.request.link(
            GeneralFileCollection(self.request.session)
        )
        return self.csrf_protected_url(url)

    def files_url_with_anchor(self, file: GeneralFile | None) -> str:
        """ Returns the url to the files view including anchor. """
        if file is None:
            return self.files_url

        return f'{self.files_url}#{file.name}'

    @cached_property
    def file_upload_url(self) -> str:
        """ Returns the url to the file upload action. """
        url = self.request.link(
            GeneralFileCollection(self.request.session), name='upload'
        )
        return self.csrf_protected_url(url)

    @cached_property
    def file_upload_json_url(self) -> str:
        """ Adds the json url for file uploads. """
        url = self.request.link(
            GeneralFileCollection(self.request.session), name='upload.json'
        )
        return self.csrf_protected_url(url)

    @cached_property
    def file_list_url(self) -> str:
        """ Adds the json url for file lists. """
        return self.request.link(
            GeneralFileCollection(self.request.session), name='json'
        )

    @cached_property
    def image_upload_url(self) -> str:
        """ Returns the url to the image upload action. """
        url = self.request.link(
            ImageFileCollection(self.request.session), name='upload'
        )
        return self.csrf_protected_url(url)

    @cached_property
    def image_upload_json_url(self) -> str:
        """ Adds the json url for image uploads. """
        url = self.request.link(
            ImageFileCollection(self.request.session), name='upload.json'
        )
        return self.csrf_protected_url(url)

    @cached_property
    def image_list_url(self) -> str:
        """ Adds the json url for image lists. """
        return self.request.link(
            ImageFileCollection(self.request.session), name='json'
        )

    @cached_property
    def sitecollection_url(self) -> str:
        """ Adds the json url for internal links lists. """
        return self.request.link(SiteCollection(self.request.session))

    @cached_property
    def homepage_url(self) -> str:
        """ Returns the url to the main page. """
        return self.request.link(self.app.org)

    @cached_property
    def search_url(self) -> str:
        """ Returns the url to the search page. """
        return self.request.class_link(Search)

    @cached_property
    def suggestions_url(self) -> str:
        """ Returns the url to the suggestions json view. """
        return self.request.class_link(Search, name='suggest')

    @cached_property
    def events_url(self) -> str:
        return self.request.link(
            OccurrenceCollection(self.request.session)
        )

    @cached_property
    def directories_url(self) -> str:
        return self.request.link(
            DirectoryCollection(self.request.session)
        )

    @cached_property
    def news_url(self) -> str:
        return self.request.class_link(News, {'absorb': ''})

    @cached_property
    def newsletter_url(self) -> str:
        return self.request.class_link(NewsletterCollection)

    @cached_property
    def vat_rate(self) -> Decimal:
        return Decimal(self.app.org.vat_rate or 0.0)

    def login_to_url(self, to: str | None, skip: bool = False) -> str:
        auth = Auth.from_request(self.request, to=to, skip=skip)
        return self.request.link(auth, 'login')

    def login_from_path(self) -> str:
        auth = Auth.from_request_path(self.request)
        return self.request.link(auth, name='login')

    def citizen_login(self) -> str:
        dashboard = CitizenDashboard(self.request)
        if dashboard.is_available:
            auth = Auth.from_request(
                self.request,
                self.request.link(dashboard)
            )
        else:
            auth = Auth.from_request_path(self.request)
        return self.request.link(auth, name='citizen-login')

    def export_formatter(self, format: str) -> Callable[[object], Any]:
        """ Returns a formatter function which takes a value and returns
        the value ready for export.

        """

        def is_daterange_list(
            value: object,
            datetype: type[object] | tuple[type[object], ...]
        ) -> bool:
            if isinstance(value, (list, tuple)):
                return all(is_daterange(v, datetype) for v in value)

            return False

        def is_daterange(
            value: object,
            datetype: type[object] | tuple[type[object], ...]
        ) -> bool:

            if isinstance(value, (list, tuple)):
                if len(value) == 2:
                    if all(isinstance(v, datetype) for v in value):
                        return True

            return False

        def default(value: object) -> Any:
            if isinstance(value, Decimal):
                return float(value)
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            if isinstance(value, time):
                return f'{value.hour}:{value.minute}'
            # FIXME: Why not isinstance(value, TranslationString)?
            if hasattr(value, 'domain'):
                return self.request.translator(value)  # type:ignore[arg-type]
            if isinstance(value, str):
                return '\n'.join(value.splitlines())  # normalize newlines
            if isinstance(value, (list, tuple)):
                return tuple(formatter(v) for v in value)

            return value

        if format in ('xlsx', 'csv'):
            # FIXME: For some reason TypeGuard wasn't working so I changed
            #        value from object to Any
            def formatter(value: Any) -> Any:
                if is_daterange_list(value, (date, datetime)):
                    return '\n'.join(formatter(v) for v in value)
                if is_daterange(value, datetime):
                    return ' - '.join(
                        self.format_date(v, 'datetime') for v in value)
                if is_daterange(value, date):
                    return ' - '.join(
                        self.format_date(v, 'date') for v in value)
                if isinstance(value, datetime):
                    return self.format_date(value, 'datetime')
                if isinstance(value, date):
                    return self.format_date(value, 'date')
                if isinstance(value, (list, tuple)):
                    return '\n'.join(formatter(v) for v in value)
                if isinstance(value, bool):
                    value = value and _('Yes') or _('No')
                if isinstance(value, dict):
                    return value and json.dumps(value) or None
                return default(value)
        else:
            formatter = default

        return formatter

    def thumbnail_url(self, url: str | None) -> str | None:
        """ Takes the given url and returns the thumbnail url for it.

        Uses some rough heuristic to determine if a url is actually served
        by onegov.file or not. May possibly fail.

        """
        if not url or '/storage/' not in url:
            return url

        image_id = url.split('/storage/')[-1]

        # image file ids are generated from the random_token function
        if len(image_id) == RANDOM_TOKEN_LENGTH:
            return self.request.class_link(
                ImageFile, {'id': image_id}, name='thumbnail')
        else:
            return url

    @property
    def custom_links(self) -> list[tuple[str, str]]:
        links: dict[int, dict[str, Any]] = {}

        def split_entry(name: str) -> tuple[int, str]:
            num_, key = name.replace('custom_link_', '').split('_')
            return int(num_), key

        for entry, value in self.org.meta.items():
            if entry.startswith('custom_link'):
                num, key = split_entry(entry)
                link = links.setdefault(num, {})
                link[key] = value

        return [
            (v['name'], v['url']) for k, v in sorted(
                links.items(), key=itemgetter(0))
            if v['name'] and v['url']
        ]

    def include_editor(self) -> None:
        self.request.include('redactor')
        self.request.include('editor')

    def include_code_editor(self) -> None:
        self.request.include('code_editor')

    def file_data_download_link(
        self,
        file_data: dict[str, Any] | None
    ) -> str | None:

        if file_data is None:
            return None

        if (ref := file_data.get('data', '')).startswith('@'):
            return self.request.class_link(File, {
                'id': ref.lstrip('@')
            })
        return None

    def file_data_file(
        self,
        file_data: dict[str, Any] | None
    ) -> File | None:

        if file_data is None:
            return None

        if (ref := file_data.get('data', '')).startswith('@'):
            return self.request.session.query(File).filter_by(
                id=ref.lstrip('@')).first()
        return None

    def field_download_link(
        self,
        field: Field
    ) -> list[str | None] | str | None:

        if field.type == 'UploadField':
            return self.file_data_download_link(field.data)
        elif field.type == 'UploadMultipleField':
            return [
                self.file_data_download_link(file_data)
                for file_data in (field.data or [])
            ]
        return None

    def field_file(self, field: Field) -> list[File | None] | File | None:
        if field.type == 'UploadField':
            return self.file_data_file(field.data)
        elif field.type == 'UploadMultipleField':
            return [
                self.file_data_file(file_data)
                for file_data in (field.data or [])
            ]
        return None

    @cached_property
    def move_person_url_template(self) -> str:
        assert isinstance(self.model, PersonLinkExtension)
        implementation = PersonMove.get_implementation(self.model)
        return self.csrf_protected_url(self.request.class_link(
            implementation,
            {
                'subject': '{subject_id}',
                'target': '{target_id}',
                'direction': '{direction}',
                'key': PersonMove.get_key(self.model)
            }
        ))

    def get_user_color(self, username: str) -> str:
        return utils.get_user_color(username)

    def get_user_title(self, username: str) -> str:
        user = UserCollection(self.request.session).by_username(username)
        return user and user.title or username

    def to_timezone(
        self,
        date: datetime,
        timezone: TzInfoOrName
    ) -> datetime:
        return to_timezone(date, timezone)

    def format_time_range(
        self,
        start: datetime | time,
        end: datetime | time
    ) -> str:

        time_range = utils.render_time_range(start, end)

        if time_range in ('00:00 - 24:00', '00:00 - 23:59'):
            return self.request.translate(_('all day'))

        return time_range

    def format_date_range(
        self,
        start: date | datetime,
        end: date | datetime
    ) -> str:

        if start == end:
            return self.format_date(start, 'date')
        else:
            return ' - '.join((
                self.format_date(start, 'date'),
                self.format_date(end, 'date')
            ))

    def format_datetime_range(
        self,
        start: datetime,
        end: datetime,
        with_year: bool = False
    ) -> str:

        if start.date() == end.date() or (
            (end - start) <= timedelta(hours=23)
            and end.time() < time(6, 0)
        ):
            show_single_day = True
        else:
            show_single_day = False

        if show_single_day:
            fmt: str = with_year and 'date_long' or 'date_long_without_year'

            return (
                f'{self.format_date(start, fmt)} '
                f'{self.format_time_range(start, end)}'
            )
        else:
            fmt = with_year and 'datetime_long' or 'datetime_long_without_year'

            return (
                f'{self.format_date(start, fmt)} - '
                f'{self.format_date(end, fmt)}'
            )

    def format_timedelta(self, delta: timedelta) -> str:
        return babel.dates.format_timedelta(
            delta=delta,
            locale=self.request.locale
        )

    def format_seconds(self, seconds: float) -> str:
        return self.format_timedelta(timedelta(seconds=seconds))

    def get_vat_amount(
        self,
        amount: numbers.Number | Decimal | float | None
    ) -> Decimal | None:
        """
        Takes the given amount and currency returning the amount
        of the paid price that is attributed to the VAT.
        """
        if amount is not None and self.vat_rate:
            if isinstance(amount, (Decimal, int, float, str)):
                amount = Decimal(amount)
            else:
                amount = Decimal(str(amount))
            return amount / (100 + self.vat_rate) * self.vat_rate
        return None

    def format_phone_number(self, phone_number: str) -> str:
        return utils.format_phone_number(phone_number)

    def password_reset_url(self, user: User | None) -> str | None:
        if not user:
            return None

        return password_reset_url(
            user,
            self.request,
            self.request.class_link(Auth, name='reset-password')
        )

    @overload
    def linkify(self, text: str) -> Markup: ...
    @overload
    def linkify(self, text: None) -> None: ...

    def linkify(self, text: str | None) -> Markup | None:
        if text is None:
            return None

        if isinstance(text, TranslationString):
            # translate the text before applying linkify if it's a
            # translation string
            text = self.request.translate(text)

        linkified = linkify(text)
        if isinstance(text, Markup):
            return linkified
        return linkified.replace('\n', Markup('<br>'))

    def linkify_field(self, field: Field, rendered: Markup) -> Markup:
        include = ('TextAreaField', 'StringField', 'EmailField', 'URLField')
        if field.render_kw:
            if field.render_kw.get('data-editor') == 'markdown':
                return rendered
            # HtmlField
            if field.render_kw.get('class_') == 'editor':
                return rendered
        if field.type in include:
            return self.linkify(rendered)
        return rendered

    @property
    def file_link_target(self) -> str | None:
        """ Use with tal:attributes='target layout.file_link_target' """
        return '_blank' if self.org.open_files_target_blank else None

    file_extension_fa_icon_mapping = {
        'pdf': 'fa-file-pdf',
        'jpg': 'fa-file-image',
        'jpeg': 'fa-file-image',
        'png': 'fa-file-image',
        'img': 'fa-file-image',
        'ico': 'fa-file-image',
        'svg': 'fa-file-image',
        'bmp': 'fa-file-image',
        'gif': 'fa-file-image',
        'tiff': 'fa-file-image',
        'ogg': 'fa-file-music',
        'wav': 'fa-file-music',
        'mpa': 'fa-file-music',
        'mp3': 'fa-file-music',
        'avi': 'fa-file-video',
        'mp4': 'fa-file-video',
        'mpg': 'fa-file-video',
        'mpeg': 'fa-file-video',
        'mov': 'fa-file-video',
        'vid': 'fa-file-video',
        'webm': 'fa-file-video',
        'zip': 'fa-file-zip',
        '7z': 'fa-file-zip',
        'rar': 'fa-file-zip',
        'pkg': 'fa-file-zip',
        'tar.gz': 'fa-file-zip',
        'txt': 'fa-file-alt',
        'log': 'fa-file-alt',
        'csv': 'fas fa-file-csv',  # hack: csv icon is a pro-icon
        'xls': 'fa-file-excel',
        'xlsx': 'fa-file-excel',
        'xlsm': 'fa-file-excel',
        'ods': 'fa-file-excel',
        'odt': 'fa-file-word',
        'doc': 'fa-file-word',
        'docx': 'fa-file-word',
        'pptx': 'fa-file-powerpoint',
    }

    def get_fa_file_icon(self, filename: str) -> str:
        """
        Returns the font awesome file icon name for the given file
        according its extension.

        NOTE: Currently, org and town6 are using different font awesome
        versions, hence this only works for town6.
        """
        default_icon = 'fa-file'
        ext = self.get_filename_extension(filename)
        return self.file_extension_fa_icon_mapping.get(ext, default_icon)

    def get_filename_extension(self, filename: str) -> str:
        """ Returns the filename extension. """
        base = self.get_filename_without_extension(filename)
        ext = filename.removeprefix(base).lstrip('.')
        return ext.lower()

    def get_filename_without_extension(self, filename: str) -> str:
        """ Returns the filename stem (no extension)."""
        name = basename(filename)
        lower = name.lower()

        # handle common compound extensions
        for ext in ('.tar.gz', '.tar.bz2', '.tar.xz'):
            if lower.endswith(ext):
                return name[:-len(ext)]

        return splitext(filename)[0]


class DefaultLayoutMixin:
    if TYPE_CHECKING:
        # forward declare required attributes
        model: Any
        request: OrgRequest

    def hide_from_robots(self) -> None:
        """ Returns a X-Robots-Tag:noindex header on secret pages.

        This is probably not where you would expect this to happen, but it
        ensures that this works on all pages without having to jump through
        hoops.

        """
        if not hasattr(self.model, 'access'):
            return

        if self.model.access not in ('secret', 'secret_mtan'):
            return

        @self.request.after
        def respond_with_no_index(response: Response) -> None:
            response.headers['X-Robots-Tag'] = 'noindex'


class DefaultLayout(Layout, DefaultLayoutMixin):
    """ The default layout meant for the public facing parts of the site. """

    request: OrgRequest
    edit_mode: bool

    def __init__(self, model: Any, request: OrgRequest,
                 edit_mode: bool = False) -> None:
        super().__init__(model, request)

        self.edit_mode = edit_mode

        # always include the common js files
        self.request.include('common')
        self.request.include('chosen')

        # always include the map components
        self.request.include(self.org.geo_provider)

        if self.request.is_manager:
            self.request.include('sortable')
            self.request.include('websockets')
            self.custom_body_attributes['data-websocket-endpoint'] = (
                self.app.websockets_client_url(request))
            self.custom_body_attributes['data-websocket-schema'] = (
                self.app.schema)
            self.custom_body_attributes['data-websocket-channel'] = (
                self.app.websockets_private_channel)

        if self.org.open_files_target_blank:
            self.request.include('all_blank')

        self.hide_from_robots()

    def show_label(self, field: Field) -> bool:
        return True

    @cached_property
    def breadcrumbs(self) -> Sequence[Link] | None:
        """ Returns the breadcrumbs for the current page. """
        return [Link(_('Homepage'), self.homepage_url)]

    def exclude_invisible(self, items: Iterable[_T]) -> Sequence[_T]:
        items = self.request.exclude_invisible(items)
        if not self.request.is_manager:
            return tuple(i for i in items if getattr(i, 'published', True))
        return items

    @property
    def root_pages(self) -> tuple[PageMeta, ...]:
        return self.request.root_pages

    @cached_property
    def top_navigation(self) -> Sequence[Link] | None:
        return tuple(
            Link(r.title, r.link(self.request)) for r in self.root_pages
        )

    @cached_property
    def qr_endpoint(self) -> str:
        return self.request.class_link(QrCode)

    @cached_property
    def editmode_links(self) -> list[Link | LinkGroup | Button]:
        return [
            Button(
                text=_('Save'),
                attrs={'class': 'save-link', 'form': 'main-form',
                       'type': 'submit'},
            ),
            Link(
                text=_('Cancel'),
                url=self.request.link(self.model),
                attrs={'class': 'cancel-link'}
            ),]


# registers the `DefaultLayout` as the default layout for all models in
# org. Look for this kind of decorator `@TownApp.layout(model=<ModelName>)`
@OrgApp.predicate_fallback(Framework.get_layout, layout_predicate)
def layout_not_found(
    self: OrgApp,
    obj: object,
    request: OrgRequest
) -> Layout:
    return DefaultLayout(obj, request)


class DefaultMailLayoutMixin:
    if TYPE_CHECKING:
        # forward declare required attributes
        request: OrgRequest

        @property
        def org(self) -> Organisation: ...

    def unsubscribe_link(self, username: str) -> str:
        return '{}?token={}'.format(
            self.request.link(self.org, name='unsubscribe'),
            self.request.new_url_safe_token(
                data={'user': username},
                salt='unsubscribe'
            )
        )

    def paragraphify(self, text: str) -> Markup:
        return paragraphify(text)


class DefaultMailLayout(Layout, DefaultMailLayoutMixin):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self) -> PageTemplateFile:
        return self.template_loader['mail_layout.pt']

    @cached_property
    def macros(self) -> MacrosLookup:
        return self.template_loader.mail_macros

    @cached_property
    def contact_html(self) -> Markup:
        """ Returns the contacts html, but instead of breaking it into multiple
        lines (like on the site footer), this version puts it all on one line.

        """

        lines = (l.strip() for l in self.org.meta['contact'].splitlines())
        lines = (l for l in lines if l)
        return linkify(', '.join(lines))


class AdjacencyListMixin:
    """ Provides layouts for models inheriting from
    :class:`onegov.core.orm.abstract.AdjacencyList`
    """

    if TYPE_CHECKING:
        model: AdjacencyList
        request: OrgRequest

        def csrf_protected_url(self, url: str) -> str: ...
        @property
        def homepage_url(self) -> str: ...

    @cached_property
    def sortable_url_template(self) -> str:
        return self.csrf_protected_url(
            self.request.class_link(
                PageMove,
                {
                    'subject_id': '{subject_id}',
                    'target_id': '{target_id}',
                    'direction': '{direction}'
                }
            )
        )

    def get_breadcrumbs(self, item: AdjacencyList) -> Iterator[Link]:
        """ Yields the breadcrumbs for the given adjacency list item. """
        yield Link(_('Homepage'), self.homepage_url)

        if item:
            for ancestor in item.ancestors:
                yield Link(ancestor.title, self.request.link(ancestor))

            yield Link(item.title, self.request.link(item))

    def get_sidebar(
        self,
        type: str | None = None
    ) -> Iterator[Link | LinkGroup]:
        """ Yields the sidebar for the given adjacency list item. """
        query = self.model.siblings.filter(self.model.__class__.type == type)

        def filter(
            items: Iterable[AdjacencyList]
        ) -> Sequence[AdjacencyList]:

            items = self.request.exclude_invisible(items)
            if not self.request.is_manager:
                return tuple(i for i in items if getattr(i, 'published', True))
            return items

        items = filter(query.all())

        for item in items:
            if item != self.model:
                yield Link(item.title, self.request.link(item), model=item)
            else:
                children = (
                    Link(c.title, self.request.link(c), model=c) for c
                    in filter(self.model.children)
                )

                yield LinkGroup(
                    title=item.title,
                    links=tuple(children),
                    model=item
                )


class AdjacencyListLayout(DefaultLayout, AdjacencyListMixin):
    request: OrgRequest


class SettingsLayout(DefaultLayout):
    def __init__(
        self,
        model: Any,
        request: OrgRequest,
        setting: str | None = None
    ) -> None:
        super().__init__(model, request)

        self.include_editor()
        self.include_code_editor()
        self.request.include('tags-input')

        self.setting = setting

    edit_mode = True

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        bc = [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Settings'), self.request.link(self.org, 'settings'))
        ]

        if self.setting:
            bc.append(Link(_(self.setting), '#'))

        return bc


@OrgApp.layout(model=Topic)
class PageLayout(AdjacencyListLayout):

    @cached_property
    def og_image_source(self) -> str | None:
        if not self.model.text:
            return super().og_image_source
        for url in IMG_URLS.findall(self.model.text) or []:
            if self.is_internal(url):
                return url
        return super().og_image_source

    @cached_property
    def breadcrumbs(self) -> Sequence[Link]:
        return tuple(self.get_breadcrumbs(self.model))

    @cached_property
    def sidebar_links(self) -> Sequence[Link | LinkGroup]:
        return tuple(self.get_sidebar(type='topic'))


@OrgApp.layout(model=News)
class NewsLayout(AdjacencyListLayout):

    @cached_property
    def og_image_source(self) -> str | None:
        if not self.model.text:
            return super().og_image_source
        for url in IMG_URLS.findall(self.model.text) or []:
            if self.is_internal(url):
                return url
        return super().og_image_source

    @cached_property
    def breadcrumbs(self) -> Sequence[Link]:
        return tuple(self.get_breadcrumbs(self.model))


# FIXME: This layout is a little bit too lax about the model type
#        but without intersections this will be annoying to type
class EditorLayout(AdjacencyListLayout):

    def __init__(
        self,
        model: Editor,
        request: OrgRequest,
        site_title: str | None
    ) -> None:
        super().__init__(model, request)
        self.site_title = site_title
        self.include_editor()
        self.edit_mode = True

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = list(self.get_breadcrumbs(self.model.page))
        links.append(Link(self.site_title, url='#'))

        return links


class FormEditorLayout(DefaultLayout):

    model: AnyFormDefinitionOrCollection

    def __init__(
        self,
        model: AnyFormDefinitionOrCollection,
        request: OrgRequest
    ) -> None:

        super().__init__(model, request)
        self.include_editor()
        self.include_code_editor()


class FormSubmissionLayout(DefaultLayout):

    model: FormSubmission | FormDefinition

    def __init__(
        self,
        model: FormSubmission | FormDefinition,
        request: OrgRequest,
        title: str | None = None
    ) -> None:

        super().__init__(model, request)
        self.include_code_editor()
        self.title = title or self.form.title

    @cached_property
    def form(self) -> FormDefinition:
        if hasattr(self.model, 'form'):
            return self.model.form  # type:ignore[return-value]
        else:
            return self.model

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        collection = FormCollection(self.request.session)

        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Forms'), self.request.link(collection)),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def can_delete_form(self) -> bool:
        return all(
            submission_deletable(submission, self.request.session)
            for submission in self.form.submissions
        )

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:

        if not self.request.is_manager:
            return None

        # only show the edit bar links if the site is the base of the form
        # -> if the user already entered some form data remove the edit bar
        # because it makes it seem like it's there to edit the submission,
        # not the actual form
        if hasattr(self.model, 'form'):
            return None

        collection = FormCollection(self.request.session)

        edit_link = Link(
            text=_('Edit'),
            url=self.request.link(self.form, name='edit'),
            attrs={'class': 'edit-link'}
        )

        qr_link = QrCodeLink(
            text=_('QR'),
            url=self.request.link(self.model),
            attrs={'class': 'qr-code-link'}
        )

        if not self.can_delete_form:
            delete_link = Link(
                text=_('Delete'),
                attrs={'class': 'delete-link'},
                traits=(
                    Block(
                        _("This form can't be deleted."),
                        _(
                            'There are submissions associated with the form. '
                            'Those need to be removed first.'
                        ),
                        _('Cancel')
                    )
                )
            )

        else:
            delete_link = Link(
                text=_('Delete'),
                url=self.csrf_protected_url(
                    self.request.link(self.form)
                ),
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _('Do you really want to delete this form?'),
                        _('This cannot be undone.'),
                        _('Delete form'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.link(collection)
                    )
                )
            )

        export_link = Link(
            text=_('Export'),
            url=self.request.link(self.form, name='export'),
            attrs={'class': 'export-link'}
        )

        change_url_link = Link(
            text=_('Change URL'),
            url=self.request.link(self.form, name='change-url'),
            attrs={'class': 'internal-url'}
        )

        registration_windows_link = LinkGroup(
            title=_('Registration Windows'),
            links=[
                Link(
                    text=_('Add'),
                    url=self.request.link(
                        self.model, 'new-registration-window'
                    ),
                    attrs={'class': 'new-registration-window'}
                ),
                *(
                    Link(
                        text=self.format_date_range(w.start, w.end),
                        url=self.request.link(w),
                        attrs={'class': 'view-link'}
                    ) for w in self.form.registration_windows
                )
            ]
        )

        return [
            edit_link,
            delete_link,
            export_link,
            change_url_link,
            registration_windows_link,
            qr_link
        ]


class FormCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Forms'), '#')
        ]

    @property
    def external_forms(self) -> ExternalLinkCollection:
        return ExternalLinkCollection(self.request.session)

    @property
    def form_definitions(self) -> FormCollection:
        return FormCollection(self.request.session)

    @property
    def document_forms(self) -> FormDocumentCollection:
        return FormDocumentCollection(self.request.session)

    @property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Form'),
                            url=self.request.link(
                                self.form_definitions,
                                name='new'
                            ),
                            attrs={'class': 'new-form'}
                        ),
                        Link(
                            text=_('External form'),
                            url=self.request.link(
                                self.external_forms,
                                query_params={
                                    'title': self.request.translate(
                                        _('New external form')),
                                    'type': 'form'
                                },
                                name='new'
                            ),
                            attrs={'class': 'new-form'}
                        ),
                        Link(
                            text=_('Document form'),
                            url=self.request.link(
                                self.document_forms,
                                name='new'
                            ),
                            attrs={'class': 'new-document-form'}
                        ),
                    ]
                ),
            ]
        return None


@OrgApp.layout(model=FormDefinition)
class FormDefinitionLayout(DefaultLayout):

    @property
    def forms_url(self) -> str:
        return self.request.class_link(FormCollection)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Forms'), self.forms_url),
            Link(self.model.title, self.request.link(self.model))
        ]


class SurveySubmissionWindowLayout(DefaultLayout):
    @cached_property
    def breadcrumbs(self) -> list[Link]:
        collection = SurveyCollection(self.request.session)

        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Surveys'), self.request.link(collection)),
            Link(self.model.survey.title, self.request.link(self.model.survey)
                 ),
            Link(self.model.title, self.request.link(self.model))
        ]

    @property
    def editbar_links(self) -> list[Link] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(self.request.link(self.model)),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete '
                                'this submission window?'
                            ),
                            _('Submissions associated with this submission '
                              'window will be deleted as well.'),
                            _('Delete submission window'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.model.survey)
                        )
                    )
                ),
                QrCodeLink(
                    text=_('QR'),
                    url=self.request.link(self.model),
                    attrs={'class': 'qr-code-link'}
                ),
                Link(
                    text=_('Results'),
                    url=self.request.link(
                        self.model,
                        name='results'
                    ),
                    attrs={'class': 'results-link'}
                ),
            ]
        return None


class SurveySubmissionLayout(DefaultLayout):

    model: SurveySubmission | SurveyDefinition

    def __init__(
        self,
        model: SurveySubmission | SurveyDefinition,
        request: OrgRequest,
        title: str | None = None
    ) -> None:

        super().__init__(model, request)
        self.include_code_editor()
        self.title = title or self.form.title

    @cached_property
    def form(self) -> SurveyDefinition:
        if hasattr(self.model, 'survey'):
            return self.model.survey  # type:ignore[return-value]
        else:
            return self.model

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        collection = SurveyCollection(self.request.session)

        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Surveys'), self.request.link(collection)),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:

        if not self.request.is_manager:
            return None

        # only show the edit bar links if the site is the base of the form
        # -> if the user already entered some form data remove the edit bar
        # because it makes it seem like it's there to edit the submission,
        # not the actual form
        if hasattr(self.model, 'form'):
            return None

        collection = SurveyCollection(self.request.session)

        edit_link = Link(
            text=_('Edit'),
            url=self.request.link(self.form, name='edit'),
            attrs={'class': 'edit-link'}
        )

        qr_link = QrCodeLink(
            text=_('QR'),
            url=self.request.link(self.model),
            attrs={'class': 'qr-code-link'}
        )

        delete_link = Link(
            text=_('Delete'),
            url=self.csrf_protected_url(
                self.request.link(self.form)
            ),
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _('Do you really want to delete this survey?'),
                    _('This cannot be undone. And all submissions will be '
                      'deleted with it.'),
                    _('Delete survey'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=self.request.link(collection)
                )
            )
        )

        export_link = Link(
            text=_('Export'),
            url=self.request.link(self.form, name='export'),
            attrs={'class': 'export-link'}
        )

        change_url_link = Link(
            text=_('Change URL'),
            url=self.request.link(self.form, name='change-url'),
            attrs={'class': 'internal-url'}
        )

        results_link = Link(
            text=_('Results'),
            url=self.request.link(self.model, name='results'),
            attrs={'class': 'results-link'}
        )

        submission_windows_link = LinkGroup(
            title=_('Submission Windows'),
            links=[
                Link(
                    text=_('Add'),
                    url=self.request.link(
                        self.model, 'new-submission-window'
                    ),
                    attrs={'class': 'new-submission-window'}
                ),
                *(
                    Link(
                        text=w.title if w.title else self.format_date_range(
                            w.start, w.end),
                        url=self.request.link(w),
                        attrs={'class': 'view-link'}
                    ) for w in self.form.submission_windows
                )
            ]
        )

        return [
            edit_link,
            delete_link,
            export_link,
            change_url_link,
            submission_windows_link,
            qr_link,
            results_link,
        ]


class SurveyCollectionLayout(DefaultLayout):
    @property
    def survey_definitions(self) -> SurveyCollection:
        return SurveyCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Surveys'), '#')
        ]

    @property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Survey'),
                            url=self.request.link(
                                self.survey_definitions,
                                name='new'
                            ),
                            attrs={'class': 'new-form'}
                        ),
                    ]
                ),
            ]
        return None


@OrgApp.layout(model=FormDocument)
class FormDocumentLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        collection = FormCollection(self.request.session)

        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Forms'), self.request.link(collection)),
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:

        if not self.request.is_manager:
            return None

        collection = FormCollection(self.request.session)

        edit_link = Link(
            text=_('Edit'),
            url=self.request.link(self.model, name='edit'),
            attrs={'class': 'edit-link'}
        )

        qr_link = QrCodeLink(
            text=_('QR'),
            url=self.request.link(self.model),
            attrs={'class': 'qr-code-link'}
        )

        delete_link = Link(
            text=_('Delete'),
            url=self.csrf_protected_url(
                self.request.link(self.model)
            ),
            attrs={'class': 'delete-link'},
            traits=(
                Confirm(
                    _('Do you really want to delete this form?'),
                    _('This cannot be undone.'),
                    _('Delete form'),
                    _('Cancel')
                ),
                Intercooler(
                    request_method='DELETE',
                    redirect_after=self.request.link(collection)
                )
            )
        )

        return [
            edit_link,
            delete_link,
            qr_link
        ]


class PersonCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('People'), '#')
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Settings'),
                    url=self.request.link(
                        self.request.app.org, 'people-settings'),
                    attrs={'class': 'settings-link'}
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Person'),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-person'}
                        )
                    ]
                ),
            ]
        return None


@OrgApp.layout(model=Person)
class PersonLayout(DefaultLayout):

    @cached_property
    def collection(self) -> PersonCollection:
        return PersonCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('People'), self.request.link(self.collection)),
            Link(_(self.model.title), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this person?'),
                            _('This cannot be undone.'),
                            _('Delete person'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]
        return None


class TicketsLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Tickets'), '#')
        ]


class ArchivedTicketsLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Tickets'), '#')
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []
        if self.request.is_admin:
            text = self.request.translate(_('Delete archived tickets'))
            links.append(
                Link(
                    text=text,
                    url=self.csrf_protected_url(self.request.link(self.model,
                                                                  'delete')),
                    traits=(
                        Confirm(
                            _('Do you really want to delete all archived '
                              'tickets?'),
                            _('This cannot be undone.'),
                            _('Delete archived tickets'),
                            _('Cancel'),
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                ArchivedTicketCollection, {'handler': 'ALL'}
                            ),
                        ),
                    ),
                    attrs={'class': 'delete-link'},
                )

            )
        return links


@OrgApp.layout(model=Ticket)
class TicketLayout(DefaultLayout):
    model: Ticket

    def __init__(self, model: Ticket, request: OrgRequest) -> None:
        super().__init__(model, request)
        self.request.include('timeline')

    @cached_property
    def collection(self) -> TicketCollection:
        return TicketCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Tickets'), get_current_tickets_url(self.request)),
            Link(self.model.number, self.request.link(
                TicketCollection(self.request.session).by_id(self.model.id)))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        links: list[Link | LinkGroup] = []
        if is_manager := self.request.is_manager_for_model(self.model):

            # only show the model related links when the ticket is pending
            # or if the handler explicitly allows it for closed tickets
            show_links_when_closed = getattr(
                self.model.handler, 'show_links_when_closed', False
            )
            if self.model.state == 'pending' or (
                self.model.state == 'closed' and show_links_when_closed
            ):
                # FIXME: This is a weird discrepancy where we unsafely change
                #        the API for Handler.get_links inside onegov.org, not
                #        sure what to do about this. We should probably move
                #        onegov.org.elements.Link* to onegov.core.elements and
                #        consistently use that
                links = self.model.handler.get_links(  # type:ignore
                    self.request
                )
                assert len(links) <= 3, """
                    Models are limited to three model-specific links. Usually
                    a primary single link and a link group containing the
                    other links.
                """
            else:
                links = []

            if self.model.state == 'open':
                links.append(Link(
                    text=_('Accept ticket'),
                    url=self.request.link(self.model, 'accept'),
                    attrs={'class': ('ticket-button', 'ticket-accept')}
                ))

            elif self.model.state == 'pending':
                traits: Sequence[Trait] = ()

                if self.model.handler.undecided:
                    traits = (
                        Block(
                            _("This ticket can't be closed."),
                            _(
                                'This ticket requires a decision, but no '
                                'decision has been made yet.'
                            ),
                            _('Cancel')
                        ),
                    )

                links.append(Link(
                    text=_('Close ticket'),
                    url=self.request.link(self.model, 'close'),
                    attrs={'class': ('ticket-button', 'ticket-close')},
                    traits=traits
                ))

            elif self.model.state == 'closed':
                links.append(Link(
                    text=_('Reopen ticket'),
                    url=self.request.link(self.model, 'reopen'),
                    attrs={'class': ('ticket-button', 'ticket-reopen')}
                ))
                links.append(Link(
                    text=_('Archive ticket'),
                    url=self.request.link(self.model, 'archive'),
                    attrs={'class': ('ticket-button', 'ticket-archive')})
                )
            elif self.model.state == 'archived':
                links.append(Link(
                    text=_('Recover from archive'),
                    url=self.request.link(self.model, 'unarchive'),
                    attrs={'class': ('ticket-button', 'ticket-reopen')}
                ))
                links.append(Link(
                    text=_('Delete Ticket'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model, 'delete')
                    ),
                    attrs={'class': ('ticket-button', 'ticket-delete')},
                ))

            if self.model.state != 'closed':
                links.append(Link(
                    text=_('Assign ticket'),
                    url=self.request.link(self.model, 'assign'),
                    attrs={'class': ('ticket-button', 'ticket-assign')},
                ))

        if self.request.is_logged_in:
            # ticket notes are always enabled
            links.append(
                Link(
                    text=_('New Note'),
                    url=self.request.link(self.model, 'note'),
                    attrs={'class': 'new-note'}
                )
            )
            if getattr(self.model, 'order_id', None) is not None:
                links.append(LinkGroup(
                    title=_('PDF'),
                    links=[
                        Link(
                            text=_('Only this ticket'),
                            url=self.request.link(self.model, 'pdf'),
                            attrs={'class': 'ticket-pdf'}
                        ),
                        Link(
                            text=_('With related tickets'),
                            url=self.request.link(
                                self.model, 'related-tickets-pdf'),
                            attrs={'class': 'ticket-pdf'}
                        ),
                    ],
                    classes=['ticket-pdf']
                ))
            else:
                links.append(
                    Link(
                        text=_('PDF'),
                        url=self.request.link(self.model, 'pdf'),
                        attrs={'class': 'ticket-pdf'}
                    )
                )

        if is_manager and self.has_submission_files:
            links.append(
                Link(
                    text=_('Download files'),
                    url=self.request.link(self.model, 'files'),
                    attrs={'class': 'ticket-files'}
                )
            )

        return links or None

    @cached_property
    def has_submission_files(self) -> bool:
        submission = getattr(self.model.handler, 'submission', None)
        return submission is not None and bool(submission.files)


class TicketNoteLayout(DefaultLayout):

    ticket: Ticket

    @overload
    def __init__(
        self,
        model: Ticket,
        request: OrgRequest,
        title: str,
        ticket: None = None
    ) -> None: ...

    @overload
    def __init__(
        self,
        model: Any,
        request: OrgRequest,
        title: str,
        ticket: Ticket
    ) -> None: ...

    def __init__(
        self,
        model: Any,
        request: OrgRequest,
        title: str,
        ticket: Ticket | None = None
    ) -> None:

        super().__init__(model, request)
        self.title = title
        self.ticket = ticket or model

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Tickets'), get_current_tickets_url(self.request)),
            Link(self.ticket.number, self.request.link(self.ticket)),
            Link(self.title, '#')
        ]


# FIXME: Something about this layout is really broken, since it clearly
#        expects a Ticket as the first argument, but we sometimes pass
#        it a Reservation instead, also we never seem to be using internal
#        breadcrumbs, which are broken, because they were using a non-existant
#        ticket attribute, much akin to TicketNoteLayout
class TicketChatMessageLayout(DefaultLayout):

    model: Ticket

    def __init__(
        self,
        model: Ticket,
        request: OrgRequest,
        internal: bool = False
    ) -> None:

        super().__init__(model, request)
        self.internal = internal

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return (
            self.internal_breadcrumbs
            if self.internal
            else self.public_breadcrumbs
        )

    @property
    def internal_breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Tickets'), get_current_tickets_url(self.request)),
            Link(self.model.number, self.request.link(self.model)),
            Link(_('New Message'), '#')
        ]

    @property
    def public_breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Ticket Status'), self.request.link(self.model, 'status')),
            Link(_('New Message'), '#')
        ]


class TicketInvoiceLayout(DefaultLayout):

    model: Ticket

    def __init__(self, model: Ticket, request: OrgRequest) -> None:
        super().__init__(model, request)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Tickets'), get_current_tickets_url(self.request)),
            Link(self.model.number, self.request.link(self.model)),
            Link(_('Invoice'), '#')
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager_for_model(self.model):
            payment = self.model.payment
            if payment is not None and (
                payment.source != 'manual'
                or payment.state != 'open'
            ):
                return None

            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Discount / Surcharge'),
                            url=self.request.link(
                                self.model,
                                name='add-invoice-item'
                            ),
                            attrs={'class': 'new-invoice-item'}
                        )
                    ]
                ),
            ]
        return None


class TextModulesLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Text modules'), '#')
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Text module'),
                            url=self.request.link(
                                self.model,
                                name='add'
                            ),
                            attrs={'class': 'new-text-module'}
                        )
                    ]
                ),
            ]
        return None


class TextModuleLayout(DefaultLayout):

    @cached_property
    def collection(self) -> TextModuleCollection:
        return TextModuleCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Text modules'), self.request.link(self.collection)),
            Link(self.model.name, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete this text '
                                'module?'
                            ),
                            _('This cannot be undone.'),
                            _('Delete text module'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]
        return None


class ResourcesLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Reservations'), self.request.link(self.model))
        ]

    @property
    def external_resources(self) -> ExternalLinkCollection:
        return ExternalLinkCollection(self.request.session)

    @property
    def resources_url(self) -> str:
        return self.request.class_link(ResourceCollection)

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Recipients'),
                    url=self.request.class_link(ResourceRecipientCollection),
                    attrs={'class': 'manage-recipients'}
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Room'),
                            url=self.request.link(
                                self.model,
                                name='new-room'
                            ),
                            attrs={'class': 'new-room'}
                        ),
                        Link(
                            text=_('Daypass'),
                            url=self.request.link(
                                self.model,
                                name='new-daypass'
                            ),
                            attrs={'class': 'new-daypass'}
                        ),
                        Link(
                            text=_('Resource Item'),
                            url=self.request.link(
                                self.model,
                                name='new-daily-item'
                            ),
                            attrs={'class': 'new-daily-item'}
                        ),
                        Link(
                            text=_('External resource link'),
                            url=self.request.link(
                                self.external_resources,
                                query_params={
                                    'to': self.resources_url,
                                    'title': self.request.translate(
                                        _('New external resource')),
                                    'type': 'resource'
                                },
                                name='new'
                            ),
                            attrs={'class': 'new-resource-link'}
                        )
                    ]
                ),
                Link(
                    text=_('Export All'),
                    url=self.request.link(self.model, name='export-all'),
                ),
                IFrameLink(
                    text=_('iFrame'),
                    url=self.request.link(self.model),
                    attrs={'class': 'new-iframe'}
                )
            ]
        return None


class FindYourSpotLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(
                _('Homepage'), self.homepage_url
            ),
            Link(
                _('Reservations'), self.request.class_link(ResourceCollection)
            ),
            Link(
                _('Find Your Spot'), self.request.link(self.model)
            )
        ]


class ResourceRecipientsLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(
                _('Homepage'), self.homepage_url
            ),
            Link(
                _('Reservations'), self.request.class_link(ResourceCollection)
            ),
            Link(
                _('Notifications'), self.request.link(self.model)
            )
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('E-Mail Recipient'),
                            url=self.request.link(
                                self.model,
                                name='new-recipient'
                            ),
                            attrs={'class': 'new-recipient'}
                        ),
                    ]
                ),
            ]
        return None


class ResourceRecipientsFormLayout(DefaultLayout):

    def __init__(self, model: Any, request: OrgRequest, title: str) -> None:
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(
                _('Homepage'), self.homepage_url
            ),
            Link(
                _('Reservations'), self.request.class_link(ResourceCollection)
            ),
            Link(
                _('Notifications'), self.request.class_link(
                    ResourceRecipientCollection
                )
            ),
            Link(self.title, '#')
        ]


@OrgApp.layout(model=Resource)
class ResourceLayout(DefaultLayout):
    model: Resource

    def __init__(self, model: Resource, request: OrgRequest) -> None:
        super().__init__(model, request)

        self.request.include('fullcalendar')

    @cached_property
    def collection(self) -> ResourceCollection:
        return ResourceCollection(self.request.app.libres_context)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Reservations'), self.request.link(self.collection)),
            Link(
                _(self.model.title),
                self.request.link(self.model),
                {'class': 'calendar-dependent'}
            )
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            # FIXME: Should deletable be part of the base Resource class?
            if getattr(self.model, 'deletable', False):
                delete_link = Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this resource?'),
                            _('This cannot be undone and will take a while '
                              'depending on the number of reservations.'),
                            _('Delete resource'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )

            else:
                delete_link = Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this resource?'),
                            _('There are future reservations associated with '
                              'this resource that will also be deleted. This '
                              'cannot be undone and will take a while '
                              'depending on the number of reservations.'),
                            _('Delete resource'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                delete_link,
                Link(
                    text=_('Clean up'),
                    url=self.request.link(self.model, 'cleanup'),
                    attrs={'class': ('cleanup-link', 'calendar-dependent')}
                ),
                Link(
                    text=_('Occupancy'),
                    url=self.request.link(self.model, 'occupancy'),
                    attrs={'class': ('occupancy-link', 'calendar-dependent')}
                ),
                Link(
                    text=_('Export'),
                    url=self.request.link(self.model, 'export'),
                    attrs={'class': ('export-link', 'calendar-dependent')}
                ),
                Link(
                    text=_('Subscribe'),
                    url=self.request.link(self.model, 'subscribe'),
                    attrs={'class': 'subscribe-link'}
                ),
                Link(
                    text=_('Availability periods'),
                    url=self.request.link(self.model, 'rules'),
                    attrs={'class': 'rule-link'}
                ),
                IFrameLink(
                    text=_('iFrame'),
                    url=self.request.link(self.model),
                    attrs={'class': 'new-iframe'}
                )
            ]
        elif self.request.has_role('member'):
            if getattr(self.model, 'occupancy_is_visible_to_members', False):
                return [
                    Link(
                        text=_('Occupancy'),
                        url=self.request.link(self.model, 'occupancy'),
                        attrs={
                            'class': ('occupancy-link', 'calendar-dependent')}
                    )
                ]
        return None


class ReservationLayout(ResourceLayout):
    editbar_links = None


class AllocationRulesLayout(ResourceLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Reservations'), self.request.link(self.collection)),
            Link(_(self.model.title), self.request.link(self.model)),
            Link(_('Availability periods'), '#')
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        add_link = LinkGroup(
            title=_('Add'),
            links=[
                Link(
                    text=_('Availability period'),
                    url=self.request.link(
                        self.model,
                        name='new-rule'
                    ),
                    attrs={'class': 'new-link'}
                )
            ]
        )

        if self.request.browser_session.get(  # type: ignore[call-overload]
            'copied_allocation_rules', {}
        ).get(self.model.type):
            return [
                add_link,
                Link(
                    text=_('Paste'),
                    url=self.request.csrf_protected_url(
                        self.request.link(self.model, 'paste-rule')
                    ),
                    attrs={'class': 'paste-link'},
                    traits=(
                        Intercooler(
                            request_method='POST',
                            redirect_after=self.request.link(
                                self.model, 'rules'
                            )
                        ),
                    )
                )
            ]
        return [add_link]


class AllocationEditFormLayout(DefaultLayout):
    """ Same as the resource layout, but with different editbar links, because
    there's not really an allocation view, but there are allocation forms.

    """

    @cached_property
    def collection(self) -> ResourceCollection:
        return ResourceCollection(self.request.app.libres_context)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Reservations'), self.request.link(self.collection)),
            Link(_('Edit allocation'), '#')
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        def links() -> Iterator[Link | LinkGroup]:
            if not self.request.is_manager:
                return

            if isclose(self.model.availability, 100.0, abs_tol=.005):
                yield Link(
                    _('Delete'),
                    self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this allocation?'),
                            _('This cannot be undone.'),
                            _('Delete allocation'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            else:
                yield Link(
                    text=_('Delete'),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Block(
                            _("This resource can't be deleted."),
                            _(
                                'There are existing reservations associated '
                                'with this resource'
                            ),
                            _('Cancel')
                        )
                    )
                )
        return list(links())


class EventLayoutMixin:

    request: OrgRequest

    def format_recurrence(self, recurrence: str | None) -> str:
        """ Returns a human readable version of an RRULE used by us. """

        # FIXME: We define a very similar constant in our forms, we should
        #        move this to onegov.org.constants and use it for both.
        WEEKDAYS = (  # noqa: N806
            _('Mo'), _('Tu'), _('We'), _('Th'), _('Fr'), _('Sa'), _('Su')
        )

        if recurrence:
            rule = rrulestr(recurrence)

            # FIXME: Implement this without relying on internal attributes
            if getattr(rule, '_freq', None) == rrule.WEEKLY:
                return _(
                    'Every ${days} until ${end}',
                    mapping={
                        'days': ', '.join(
                            self.request.translate(WEEKDAYS[day])
                            for day in rule._byweekday  # type:ignore
                        ),
                        'end': rule._until.date(  # type:ignore
                        ).strftime('%d.%m.%Y')
                    }
                )

        return ''

    def event_deletable(self, event: Event) -> bool:
        tickets = TicketCollection(self.request.session)
        ticket = tickets.by_handler_id(event.id.hex)
        return not ticket


class OccurrencesLayout(DefaultLayout, EventLayoutMixin):

    app: OrgApp
    request: OrgRequest

    @property
    def og_description(self) -> str:
        return self.request.translate(_('Events'))

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Events'), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        def links() -> Iterator[Link | LinkGroup]:
            if (self.request.is_admin and self.request.app.org.
                    event_filter_type in ['filters', 'tags_and_filters']):
                yield Link(
                    text=_('Configure'),
                    url=self.request.link(self.model, '+edit'),
                    attrs={'class': 'filters-link'}
                )

            if self.request.is_manager:
                yield Link(
                    text=_('Edit'),
                    url=self.request.link(self.request.app.org,
                                          'event-settings'),
                    attrs={'class': 'edit-link'}
                )

                yield Link(
                    text=_('Import'),
                    url=self.request.link(self.model, 'import'),
                    attrs={'class': 'import-link'}
                )

                yield Link(
                    text=_('Export'),
                    url=self.request.link(self.model, 'export'),
                    attrs={'class': 'export-link'}
                )

                yield IFrameLink(
                    text=_('iFrame'),
                    url=self.request.link(self.model),
                    attrs={'class': 'new-iframe'}
                )

        return list(links())


@OrgApp.layout(model=Occurrence)
class OccurrenceLayout(DefaultLayout, EventLayoutMixin):
    app: OrgApp
    request: OrgRequest
    model: Occurrence

    def __init__(self, model: Occurrence, request: OrgRequest) -> None:
        super().__init__(model, request)
        self.request.include('monthly-view')

    @cached_property
    def collection(self) -> OccurrenceCollection:
        return OccurrenceCollection(self.request.session)

    @property
    def og_description(self) -> str | None:
        return self.model.event.description

    @cached_property
    def og_image(self) -> File | None:
        return self.model.event.image or super().og_image

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Events'), self.request.link(self.collection)),
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            if self.model.event.source:
                return [
                    Link(
                        text=_('Edit'),
                        attrs={'class': 'edit-link'},
                        traits=(
                            Block(
                                _("This event can't be edited."),
                                _('Imported events can not be edited.'),
                                _('Cancel')
                            )
                        )
                    ),
                    Link(
                        text=_('Delete'),
                        url=self.csrf_protected_url(
                            self.request.link(self.model.event, 'withdraw'),
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Confirm(
                                _('Do you really want to delete this event?'),
                                _('This cannot be undone.'),
                                _('Delete event'),
                                _('Cancel')
                            ),
                            Intercooler(
                                request_method='POST',
                                redirect_after=self.events_url
                            ),
                        )
                    )
                ]

            edit_link = Link(
                text=_('Edit'),
                url=self.request.return_here(
                    self.request.link(self.model.event, 'edit')
                ),
                attrs={'class': 'edit-link'}
            )

            if self.event_deletable(self.model.event):
                delete_link = Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model.event)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this event?'),
                            _('This cannot be undone.'),
                            _('Delete event'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.events_url
                        )
                    )
                )
            else:
                delete_link = Link(
                    text=_('Delete'),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Block(
                            _("This event can't be deleted."),
                            _(
                                'To remove this event, go to the ticket '
                                'and reject it.'
                            ),
                            _('Cancel')
                        )
                    )
                )

            return [edit_link, delete_link]
        return None


@OrgApp.layout(model=Event)
class EventLayout(EventLayoutMixin, DefaultLayout):
    app: OrgApp
    request: OrgRequest
    model: Event

    if TYPE_CHECKING:
        def __init__(self, model: Event, request: OrgRequest) -> None: ...

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Events'), self.events_url),
            Link(self.model.title, self.request.link(self.model)),
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if not self.request.is_manager:
            return None

        links: list[Link | LinkGroup] = []
        if self.model.source:
            links = [
                Link(
                    text=_('Edit'),
                    attrs={'class': 'edit-link'},
                    traits=(
                        Block(
                            _("This event can't be edited."),
                            _('Imported events can not be edited.'),
                            _('Cancel')
                        )
                    )
                )]
        if self.model.source and self.model.state == 'published':
            links.append(
                Link(
                    text=_('Withdraw event'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model, 'withdraw'),
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to withdraw this event?'),
                            _('You can re-publish an imported event later.'),
                            _('Withdraw event'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='POST',
                            redirect_after=self.events_url
                        ),
                    )
                )
            )
        if self.model.source and self.model.state == 'withdrawn':
            links.append(
                Link(
                    text=_('Re-publish event'),
                    url=self.request.return_here(
                        self.request.link(self.model, 'publish')),
                    attrs={'class': 'accept-link'}
                )
            )
        if self.model.source:
            return links

        edit_link = Link(
            text=_('Edit'),
            url=self.request.link(self.model, 'edit'),
            attrs={'class': 'edit-link'}
        )
        if self.event_deletable(self.model):
            delete_link = Link(
                text=_('Delete'),
                url=self.csrf_protected_url(
                    self.request.link(self.model)
                ),
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _('Do you really want to delete this event?'),
                        _('This cannot be undone.'),
                        _('Delete event'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.events_url
                    )
                )
            )
        else:
            delete_link = Link(
                text=_('Delete'),
                attrs={'class': 'delete-link'},
                traits=(
                    Block(
                        _("This event can't be deleted."),
                        _(
                            'To remove this event, go to the ticket '
                            'and reject it.'
                        ),
                        _('Cancel')
                    )
                )
            )

        return [edit_link, delete_link]


@OrgApp.layout(model=Newsletter)
class NewsletterLayout(DefaultLayout):

    @cached_property
    def collection(self) -> NewsletterCollection:
        return NewsletterCollection(self.app.session())

    @cached_property
    def recipients(self) -> RecipientCollection:
        return RecipientCollection(self.app.session())

    @cached_property
    def is_collection(self) -> bool:
        return isinstance(self.model, NewsletterCollection)

    @cached_property
    def breadcrumbs(self) -> list[Link]:

        if self.is_collection and self.view_name == 'new':
            return [
                Link(_('Homepage'), self.homepage_url),
                Link(_('Newsletter'), self.request.link(self.collection)),
                Link(_('New'), '#')
            ]
        if self.is_collection and self.view_name == 'new-paste':
            return [
                Link(_('Homepage'), self.homepage_url),
                Link(_('Newsletter'), self.request.link(self.collection)),
                Link(_('Paste'), '#'),
            ]
        if self.is_collection and self.view_name == 'update':
            return [
                Link(_('Homepage'), self.homepage_url),
                Link(_('Newsletter'), self.request.link(self.collection)),
                Link(_('Edit'), '#')
            ]
        elif self.is_collection:
            return [
                Link(_('Homepage'), self.homepage_url),
                Link(_('Newsletter'), '#')
            ]
        else:
            return [
                Link(_('Homepage'), self.homepage_url),
                Link(_('Newsletter'), self.request.link(self.collection)),
                Link(self.model.title, '#')
            ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if not self.request.is_manager:
            return None

        if self.is_collection:
            links: list[Link | LinkGroup] = [
                Link(
                    text=_('Subscribers'),
                    url=self.request.link(self.recipients),
                    attrs={'class': 'manage-subscribers'}
                ),
                Link(
                    text=_('Settings'),
                    url=self.request.link(
                        self.request.app.org, 'newsletter-settings'),
                    attrs={'class': 'settings-link'}
                ),
            ]

            if self.request.browser_session.has('clipboard_url'):
                clipboard = Clipboard.from_session(self.request)
                source = clipboard.get_object()
                if source is None:
                    clipboard.clear()
                elif isinstance(source, Newsletter):
                    links.append(
                        Link(
                            text=_('Paste'),
                            url=self.request.link(self.model, 'new-paste'),
                            attrs={'class': 'paste-link'},
                        )
                    )

            links.append(
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Newsletter'),
                            url=self.request.link(
                                NewsletterCollection(self.app.session()),
                                name='new'
                            ),
                            attrs={'class': 'new-newsletter'}
                        ),
                    ]
                )
            )

            return links
        else:
            if self.view_name == 'send':
                return []

            return [
                Link(
                    text=_('Send'),
                    url=self.request.link(self.model, 'send'),
                    attrs={'class': 'send-link'}
                ),
                Link(
                    text=_('Test'),
                    url=self.request.link(self.model, 'test'),
                    attrs={'class': 'test-link'}
                ),
                Link(
                    text=_('Copy'),
                    url=self.request.link(
                        Clipboard.from_url(
                            self.request, self.request.path_info or ''
                        )
                    ),
                    attrs={'class': 'copy-link'},
                ),
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete "{}"?'.format(
                                self.model.title
                            )),
                            _('This cannot be undone.'),
                            _('Delete newsletter'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]


class RecipientLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Newsletter'), self.request.link(
                NewsletterCollection(self.app.session())
            )),
            Link(_('Subscribers'), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Import'),
                    url=self.request.link(self.model,
                                          'import-newsletter-recipients'),
                    attrs={'class': 'import-link'},
                ),
                Link(
                    text=_('Export'),
                    url=self.request.link(self.model,
                                          'export-newsletter-recipients'),
                    attrs={'class': 'export-link'},
                ),
            ]
        return None


class ImageSetCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Photo Albums'), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Manage images'),
                    url=self.request.link(
                        ImageFileCollection(self.request.session)
                    ),
                    attrs={'class': 'upload'}
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Photo Album'),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-photo-album'}
                        )
                    ]
                ),
            ]
        return None


@OrgApp.layout(model=ImageSet)
class ImageSetLayout(DefaultLayout):
    model: ImageSet

    def __init__(self, model: ImageSet, request: OrgRequest) -> None:
        super().__init__(model, request)
        self.request.include('photoswipe')

    @property
    def collection(self) -> ImageSetCollection:
        return ImageSetCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Photo Albums'), self.request.link(self.collection)),
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Choose images'),
                    url=self.request.link(self.model, 'select'),
                    attrs={'class': 'select'}
                ),
                Link(
                    text=_('Edit'),
                    url=self.request.link(
                        self.model,
                        name='edit'
                    ),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete "{}"?'.format(
                                self.model.title
                            )),
                            _('This cannot be undone.'),
                            _('Delete photo album'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]
        return None


class UserManagementLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Usermanagement'), self.request.class_link(
                UserCollection,
                variables={'active': '1'}
        )),
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []

        if self.request.is_manager:

            if self.app.enable_user_registration:
                links.append(
                    Link(
                        text=_('Create Signup Link'),
                        url=self.request.class_link(
                            UserCollection,
                            name='signup-link'
                        ),
                        attrs={'class': 'new-link'}
                    )
                )

            links.append(
                LinkGroup(
                    title=_('Add'),
                    links=(
                        Link(
                            text=_('User'),
                            url=self.request.class_link(
                                UserCollection, name='new'
                            ),
                            attrs={'class': 'new-user'}
                        ),
                    )
                )
            )

        return links


@OrgApp.layout(model=User)
class UserLayout(DefaultLayout):
    if TYPE_CHECKING:
        model: User

        def __init__(self, model: User, request: OrgRequest) -> None: ...

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Usermanagement'), self.request.class_link(
                UserCollection,
                variables={'active': '1'}
        )),
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_admin and not self.model.source:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                )
            ]
        return None


class UserGroupCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('User groups'), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_admin:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('User group'),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-user'}
                        )
                    ]
                ),
            ]
        return None


class UserGroupLayout(DefaultLayout):

    if TYPE_CHECKING:
        model: UserGroup

        def __init__(self, model: UserGroup, request: OrgRequest) -> None: ...

    @cached_property
    def collection(self) -> UserGroupCollection[UserGroup]:
        return UserGroupCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('User groups'), self.request.link(self.collection)),
            Link(self.model.name, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_admin:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this user group?'),
                            _('This cannot be undone.'),
                            _('Delete user group'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]
        return None


class ExportCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Exports'), self.request.class_link(ExportCollection))
        ]


class PaymentProviderLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Payment Providers'), self.request.class_link(
                PaymentProviderCollection
            ))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_admin:
            return [
                Link(
                    text=_('Payments'),
                    url=self.request.class_link(PaymentCollection),
                    attrs={'class': 'payments'}
                ),
                LinkGroup(
                    title=_('Add'),
                    links=(
                        Link(
                            text=_('Datatrans'),
                            url=self.request.class_link(
                                PaymentProviderCollection,
                                name='new-datatrans'
                            ),
                            attrs={'class': 'new-datatrans'}
                        ),
                        Link(
                            text=_('Stripe Connect'),
                            url=self.request.class_link(
                                PaymentProviderCollection,
                                name='stripe-connect-oauth'
                            ),
                            attrs={'class': 'new-stripe-connect'}
                        ),
                        Link(
                            text=_('Worldline Saferpay'),
                            url=self.request.class_link(
                                PaymentProviderCollection,
                                name='new-saferpay'
                            ),
                            attrs={'class': 'new-worldline-saferpay'}
                        ),
                    )
                )
            ]
        return None


class PaymentCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Payments'), self.request.class_link(
                PaymentCollection
            ))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []

        if self.app.payment_providers_enabled:
            if self.request.is_admin:
                links.append(
                    Link(
                        text=_('Payment Provider'),
                        url=self.request.class_link(PaymentProviderCollection),
                        attrs={'class': 'payment-provider'}
                    )
                )

            links.append(
                Link(
                    text=_('Synchronise'),
                    url=self.request.class_link(
                        PaymentProviderCollection, name='sync'
                    ),
                    attrs={'class': 'sync'}
                )
            )
            links.append(
                Link(
                    text=_('Export'),
                    url=self.request.class_link(OrgExport, {'id': 'payments'}),
                    attrs={'class': 'export-link'}
                )
            )

        return links


class TicketInvoiceCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Invoices'), self.request.class_link(
                TicketInvoiceCollection
            ))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links: list[Link | LinkGroup] = []

        if self.request.is_manager_for_model(self.model):

            links.append(
                Link(
                    text=_('Export Bill run as PDF'),
                    url=self.request.link(
                        self.model,
                        query_params={'format': 'pdf'}
                    ),
                    attrs={'class': 'ticket-pdf'}
                )
            )

        return links


class MessageCollectionLayout(DefaultLayout):
    def __init__(self, model: Any, request: OrgRequest) -> None:
        super().__init__(model, request)
        self.request.include('timeline')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Timeline'), '#')
        ]


class DirectoryCollectionLayout(DefaultLayout):

    model: DirectoryCollection[Any] | DirectoryEntryCollection[Any]

    def __init__(
        self,
        model: DirectoryCollection[Any] | DirectoryEntryCollection[Any],
        request: OrgRequest
    ) -> None:

        super().__init__(model, request)
        self.include_editor()
        self.include_code_editor()
        self.request.include('iconwidget')

    @property
    def og_description(self) -> str:
        return self.request.translate(_('Directories'))

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Directories'), self.request.class_link(
                DirectoryCollection
            )),
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_admin:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Directory'),
                            url=self.request.link(
                                self.model,
                                name='+new'
                            ),
                            attrs={'class': 'new-directory'}
                        )
                    ]
                ),
            ]
        return None


@OrgApp.layout(model=Directory)
class DirectoryLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Directories'), self.request.class_link(
                DirectoryCollection
            )),
            Link(self.model.title, self.request.link(self.model))
        ]


class DirectoryEntryMixin:

    request: OrgRequest
    model: ExtendedDirectoryEntry | ExtendedDirectoryEntryCollection
    custom_body_attributes: dict[str, Any]

    def init_markers(self) -> None:
        self.request.include('photoswipe')
        if self.directory.marker_color:
            self.custom_body_attributes['data-default-marker-color'] = (
                self.directory.marker_color)

        if self.directory.marker_icon:
            self.custom_body_attributes['data-default-marker-icon'] = (
                self.directory.marker_icon.encode('unicode-escape')[2:])

    @property
    def directory(self) -> ExtendedDirectory:
        return self.model.directory

    @cached_property
    def thumbnail_field_id(self) -> str | None:
        if thumbnail := self.directory.configuration.thumbnail:
            return as_internal_id(thumbnail)
        return None

    def thumbnail_file_id(self, entry: ExtendedDirectoryEntry) -> str | None:
        thumbnail = self.thumbnail_field_id
        if not thumbnail:
            return None
        return (entry.values.get(thumbnail) or {}).get('data', '').lstrip('@')

    def thumbnail_link(self, entry: ExtendedDirectoryEntry) -> str | None:
        file_id = self.thumbnail_file_id(entry)
        return self.request.class_link(
            File, {'id': file_id}, name='thumbnail'
        ) if file_id else None

    def thumbnail_file(self, entry: ExtendedDirectoryEntry) -> File | None:
        file_id = self.thumbnail_file_id(entry)
        if not file_id:
            return None
        return self.request.session.query(File).filter_by(id=file_id).first()


class DirectoryEntryCollectionLayout(DefaultLayout, DirectoryEntryMixin):

    request: OrgRequest
    model: ExtendedDirectoryEntryCollection

    def __init__(
        self,
        model: ExtendedDirectoryEntryCollection,
        request: OrgRequest
    ) -> None:

        super().__init__(model, request)

        self.init_markers()
        if self.directory.numbering == 'standard':
            self.custom_body_attributes['data-default-marker-icon'] = 'numbers'
        elif self.directory.numbering == 'custom':
            self.custom_body_attributes['data-default-marker-icon'] = 'custom'

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Directories'), self.request.class_link(
                DirectoryCollection
            )),
            Link(_(self.model.directory.title), self.request.class_link(
                ExtendedDirectoryEntryCollection, {
                    'directory_name': self.model.directory_name
                }
            ))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:

        export_link = Link(
            text=_('Export'),
            url=self.request.link(self.model, name='+export'),
            attrs={'class': 'export-link'}
        )

        def links() -> Iterator[Link | LinkGroup]:
            qr_link = None
            if self.request.is_admin:
                yield Link(
                    text=_('Configure'),
                    url=self.request.link(self.model, '+edit'),
                    attrs={'class': 'edit-link'}
                )

            if self.request.is_manager:
                yield export_link

                yield Link(
                    text=_('Import'),
                    url=self.request.class_link(
                        ExtendedDirectoryEntryCollection, {
                            'directory_name': self.model.directory_name
                        }, name='+import'
                    ),
                    attrs={'class': 'import-link'}
                )

                qr_link = QrCodeLink(
                    text=_('QR'),
                    url=self.request.link(self.model),
                    attrs={'class': 'qr-code-link'}
                )

                yield IFrameLink(
                    text=_('iFrame'),
                    url=self.request.link(self.model),
                    attrs={'class': 'new-iframe'}
                )

            if self.request.is_admin:
                yield Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete "${title}"?',
                                mapping={
                                    'title': self.model.directory.title
                                }
                            ),
                            _('All entries will be deleted as well!'),
                            _('Delete directory'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                DirectoryCollection
                            )
                        )
                    )
                )
                yield Link(
                    text=self.request.translate(_('Change URL')),
                    url=self.request.link(
                        self.model.directory,
                        'change-url'),
                    attrs={'class': 'internal-link'},
                )

            if self.request.is_manager:
                yield LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Entry'),
                            url=self.request.link(
                                self.model,
                                name='+new'
                            ),
                            attrs={'class': 'new-directory-entry'}
                        )
                    ]
                )

            if not self.request.is_logged_in:
                yield export_link

            if qr_link:
                yield qr_link
        return list(links())

    def get_pub_link(
        self,
        text: str,
        filter: str | None = None,
        toggle_active: bool = True
    ) -> Link:

        filter_data = {}
        classes = []
        if filter:
            filter_data[filter] = True
            if toggle_active and self.request.params.get(filter) == '1':
                classes.append('active')

        return Link(
            text=text,
            url=self.request.class_link(
                ExtendedDirectoryEntryCollection,
                {**filter_data, 'directory_name': self.directory.name}
            ),
            attrs={'class': classes}
        )

    @property
    def publication_filters(self) -> dict[str, str]:
        if not self.request.is_logged_in:
            return {}
        if self.request.is_manager:
            return {
                'published_only': _('Published'),
                'upcoming_only': _('Upcoming'),
                'past_only': _('Past'),
            }
        return {
            'published_only': _('Published'),
            'past_only': _('Past'),
        }

    @property
    def publication_filter_title(self) -> str:
        default_title = self.request.translate(_('Publication'))
        for filter in self.publication_filters:
            if filter in self.request.params:
                applied_title = self.request.translate(
                    self.publication_filters[filter])
                return f'{default_title}: {applied_title}'
        return f'{default_title}: {self.request.translate(_("Choose filter"))}'

    @property
    def publication_links(self) -> Iterator[Link]:
        return (
            self.get_pub_link(text, filter_kw)
            for filter_kw, text in self.publication_filters.items()
        )


@OrgApp.layout(model=DirectoryEntry)
class DirectoryEntryLayout(DefaultLayout, DirectoryEntryMixin):
    request: OrgRequest
    model: ExtendedDirectoryEntry

    def __init__(
        self,
        model: ExtendedDirectoryEntry,
        request: OrgRequest
    ) -> None:

        super().__init__(model, request)
        self.init_markers()

    def show_label(self, field: Field) -> bool:
        return field.id not in self.model.hidden_label_fields

    @cached_property
    def og_image(self) -> File | None:
        return self.thumbnail_file(self.model) or super().og_image

    @property
    def og_description(self) -> str | None:
        return self.directory.lead

    @property
    def thumbnail_field_ids(self) -> list[str]:
        return [
            as_internal_id(e) for e in getattr(
                self.model.directory.configuration,
                'show_as_thumbnails', []) or []
        ]

    def field_download_link(
        self,
        field: Field
    ) -> list[str | None] | str | None:

        url = super().field_download_link(field)
        if field.id in self.thumbnail_field_ids:
            if isinstance(url, list):
                return [self.thumbnail_url(u) for u in url]
            return self.thumbnail_url(url)
        return url

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Directories'), self.request.class_link(
                DirectoryCollection
            )),
            Link(_(self.model.directory.title), self.request.class_link(
                ExtendedDirectoryEntryCollection, {
                    'directory_name': self.model.directory.name
                }
            )),
            Link(_(self.model.title), self.request.link(self.model))
        ]

    @overload
    def linkify(self, text: str) -> Markup: ...
    @overload
    def linkify(self, text: None) -> None: ...

    def linkify(self, text: str | None) -> Markup | None:
        linkified = super().linkify(text)
        return linkified.replace(
            '\\n', Markup('<br>')) if linkified else linkified

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, '+edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete "${title}"?',
                                mapping={
                                    'title': self.model.title
                                }
                            ),
                            _('This cannot be undone.'),
                            _('Delete entry'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                ExtendedDirectoryEntryCollection(
                                    self.directory)
                            )
                        )
                    )
                ),
                QrCodeLink(
                    text=_('QR'),
                    url=self.request.link(self.model),
                    attrs={'class': 'qr-code-link'}
                )
            ]
        return None


class PublicationLayout(DefaultLayout):

    def __init__(self, model: Any, request: OrgRequest) -> None:
        super().__init__(model, request)
        self.request.include('filedigest')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Publications'), self.request.class_link(
                PublicationCollection
            ))
        ]


class DashboardLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Overview'), '#')
        ]


@OrgApp.layout(model=GeneralFile)
class GeneralFileCollectionLayout(DefaultLayout):
    def __init__(self, model: Any, request: OrgRequest) -> None:
        request.include('common')
        request.include('upload')
        request.include('prompt')
        super().__init__(model, request)


class ImageFileCollectionLayout(DefaultLayout):

    def __init__(self, model: Any, request: OrgRequest) -> None:
        request.include('common')
        request.include('upload')
        request.include('editalttext')
        super().__init__(model, request)


class ExternalLinkLayout(DefaultLayout):

    @property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if not self.request.is_manager:
            return None

        return [
            Link(
                _('Delete'),
                self.csrf_protected_url(self.request.link(self.model)),
                traits=(
                    Confirm(
                        _('Do you really want to delete this external link?'),
                        _('This cannot be undone.'),
                        _('Delete external link'),
                        _('Cancel')
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.class_link(
                            ExternalLinkCollection.target(self.model)
                        )
                    )
                ),
                attrs={'class': ('ticket-delete',)}
            )
        ]


class HomepageLayout(DefaultLayout):

    @property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    _('Edit'),
                    self.request.link(self.model, 'homepage-settings'),
                    attrs={'class': ('edit-link')}
                ),
                Link(
                    _('Sort'),
                    self.request.link(self.model, 'sort'),
                    attrs={'class': ('sort-link')}
                ),
                Link(
                    _('Add'),
                    self.request.link(Editor('new-root', self.model, 'page')),
                    attrs={'class': ('new-page')},
                    classes=(
                        'new-page',
                        'show-new-content-placeholder'
                    ),
                ),
            ]
        return None

    @cached_property
    def sortable_url_template(self) -> str:
        return self.csrf_protected_url(
            self.request.class_link(
                PageMove,
                {
                    'subject_id': '{subject_id}',
                    'target_id': '{target_id}',
                    'direction': '{direction}'
                }
            )
        )
