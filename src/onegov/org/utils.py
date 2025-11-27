from __future__ import annotations

import colorsys
import hashlib
import phonenumbers
import re
import sedate
import pytz

from contextlib import suppress
from collections import defaultdict, Counter, OrderedDict
from datetime import datetime, time, timedelta
from decimal import Decimal
from email.headerregistry import Address
from functools import lru_cache
from isodate import parse_date, parse_datetime
from itertools import groupby
from libres.modules import errors as libres_errors
from lxml.etree import ParserError
from lxml.html import fragments_fromstring, tostring
from markupsafe import escape, Markup
from onegov.core.layout import Layout
from onegov.core.mail import coerce_address
from onegov.file import File, FileCollection
from onegov.org import _
from onegov.org.elements import DeleteLink, Link
from onegov.org.models.search import Search
from onegov.pay import InvoiceItemMeta, Price
from onegov.reservation import Resource
from onegov.ticket import Ticket, TicketCollection, TicketPermission
from onegov.user import User, UserGroup
from operator import add, attrgetter
from sqlalchemy import case, nullsfirst  # type:ignore[attr-defined]
from webob.exc import HTTPBadRequest


from typing import overload, Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable, Iterable, Iterator, Sequence
    from lxml.etree import _Element
    from onegov.core.request import CoreRequest
    from onegov.form import Form, FormSubmission
    from onegov.org.models import ImageFile
    from onegov.org.request import OrgRequest
    from onegov.pay import InvoiceItem
    from onegov.pay.types import PriceDict
    from onegov.reservation import Allocation, Reservation
    from pytz.tzinfo import DstTzInfo, StaticTzInfo
    from sqlalchemy.orm import Query
    from sqlalchemy import Column
    from typing import Self, TypeAlias, TypeVar
    from uuid import UUID

    _T = TypeVar('_T')
    _DeltaT = TypeVar('_DeltaT')
    _SortT = TypeVar('_SortT', bound='SupportsRichComparison')
    _TransformedT = TypeVar('_TransformedT')
    _ItemT = TypeVar('_ItemT', bound=InvoiceItem | InvoiceItemMeta)
    TzInfo: TypeAlias = DstTzInfo | StaticTzInfo
    DateRange: TypeAlias = tuple[datetime, datetime]


# for our empty paragraphs approach we don't need a full-blown xml parser
# since we only remove a very limited set of paragraphs
EMPTY_PARAGRAPHS = re.compile(r'<p>\s*<br>\s*</p>')

# XXX this is doubly defined in onegov.search.utils, maybe move to a common
# regex module in in onegov.core
#
# additionally it is used in onegov.org's common.js in javascript variant
HASHTAG = re.compile(r'(?<![\w/])#\w{3,}')
IMG_URLS = re.compile(r'<img[^>]*?src="(.*?)"')

# some sensible colors to be used for labels in calendars
COLORS = [
    '#d3e3fb', '#c69943', '#2c9f42', '#ffb100', '#ef969d', '#ffc800',
    '#92baf6', '#d1d4d6', '#96cfa1', '#de2c3b', '#f8d5d8', '#ffe480',
]


def djb2_hash(text: str, size: int) -> int:
    """ Implementation of the djb2 hash, a simple hash function with a
    configurable table size.

    ** Do NOT use for cryptography! **

    """
    # arbitrary large prime number to initialize
    hash = 5381

    # hash(i) = hash(i-1) * 33 + str[i]
    for char in text:
        hash = ((hash << 5) + hash) + ord(char)

    # Output: integer between 0 and size-1 (inclusive)
    return hash % size


def get_random_color(seed: str, lightness: float, saturation: float) -> str:
    """ Gets a random color using the given seed (a text value).

    Since the colorspace is very limited there are lots of collisions.

    """

    hue = 100 / (djb2_hash(seed, 360) or 1)
    r, g, b = colorsys.hls_to_rgb(hue, lightness, saturation)

    return '#{:02x}{:02x}{:02x}'.format(
        round(r * 255),
        round(g * 255),
        round(b * 255)
    )


@lru_cache(maxsize=32)
def get_user_color(username: str) -> str:
    """ Gets a user color for each username which is used for the
    user-initials-* elements. Each username is mapped to a color.

    :returns: The user color in an css rgb string.

    """

    return get_random_color(username, lightness=0.9, saturation=0.5)


@lru_cache(maxsize=16)
def get_extension_color(extension: str) -> str:
    """ Gets an extension color for each file extension. This is similar to
    :func:`get_user_color`, but returns a darker color (text is white).

    """

    return get_random_color(extension, lightness=0.5, saturation=0.5)


def add_class_to_node(node: _Element, classname: str) -> None:
    """ Adds the given classname to the given lxml node's class list. """

    if 'class' in node.attrib:
        node.attrib['class'] += ' ' + classname
    else:
        node.attrib['class'] = classname


@overload
def annotate_html(
    html: Markup,
    request: CoreRequest | None = None
) -> Markup: ...


@overload
def annotate_html(html: None, request: CoreRequest | None = None) -> None:
    ...


def annotate_html(
    html: Markup | None,
    request: CoreRequest | None = None
) -> Markup | None:
    """ Takes the given html and annotates the following elements for some
    advanced styling:

        * Every paragraph containing an img element will be marked with the
          `has-img` class.

        * If a link is found which points to a youtube or a vimeo video, the
          link itself as well as the surrounding paragraph is marked
          with the `has-video` class

        * If a hashtag is found, the paragraph gets the 'has-hashtag' class.

    """

    if not html:
        return html

    try:
        fragments = fragments_fromstring(html, no_leading_text=True)
    except ParserError:
        return html
    images = []

    # we perform a root xpath lookup, which will result in all paragraphs
    # being looked at - so we don't need to loop over all elements (yah, it's
    # a bit weird)
    for element in fragments[:1]:

        for paragraph in element.xpath('//p[img]'):
            add_class_to_node(paragraph, 'has-img')

        condition = ' or '.join(
            'starts-with(@href, "{}")'.format(url) for url in {
                'https://youtu.be',
                'https://www.youtube.com',
                'https://www.vimeo.com',
                'https://vimeo',
            }
        )

        for a in element.xpath('//a[{}]'.format(condition)):
            add_class_to_node(a, 'has-video')

            # find the closest paragraph in the ancestrage, but don't look far
            parent = a.getparent()

            for i in range(3):
                if parent is None:
                    break
                if parent.tag == 'p':
                    add_class_to_node(parent, 'has-video')
                    break
                parent = parent.getparent()

        for img in element.xpath('//img'):
            img.set('class', 'lazyload-alt')
            images.append(img)

    # for the hashtag lookup we need all elements, as we do not use xpath
    for element in fragments:
        for text in element.itertext():
            if text and HASHTAG.search(text):
                add_class_to_node(element, 'has-hashtag')
                break

    if request:
        set_image_sizes(images, request)

    return Markup(  # nosec: B704
        ''.join(tostring(e, encoding=str) for e in fragments))


@overload
def remove_empty_paragraphs(html: None) -> None: ...
@overload
def remove_empty_paragraphs(html: Markup) -> Markup: ...


def remove_empty_paragraphs(html: Markup | None) -> Markup | None:
    if not html:
        return html

    return Markup(EMPTY_PARAGRAPHS.sub('', html))  # nosec: B704


def set_image_sizes(
    images: list[_Element],
    request: CoreRequest
) -> None:

    internal_src = re.compile(r'.*/storage/([a-z0-9]+)')

    def get_image_id(img: _Element) -> str | None:
        match = internal_src.match(img.get('src', ''))

        if match and match.groups():
            return match.group(1)
        return None

    images_dict = {get_image_id(img): img for img in images}

    if images_dict:
        q: Query[ImageFile]
        q = FileCollection(request.session, type='image').query()
        q = q.with_entities(File.id, File.reference)
        q = q.filter(File.id.in_(images_dict))

        sizes = {i.id: i.reference for i in q}

        for id, image in images_dict.items():
            if id in sizes:
                with suppress(AttributeError):
                    image.set('width', sizes[id].size[0])
                    image.set('height', sizes[id].size[1])


def parse_fullcalendar_request(
    request: CoreRequest,
    timezone: str
) -> tuple[datetime, datetime] | tuple[None, None]:
    """ Parses start and end from the given fullcalendar request. It is
    expected that no timezone is passed (the default).

    See `<https://fullcalendar.io/docs/timezone/timezone/>`_

    :returns: A tuple of timezone-aware datetime objects or (None, None).

    """
    start_str = request.params.get('start')
    end_str = request.params.get('end')

    if start_str and end_str:
        if 'T' in start_str:
            try:
                start = parse_datetime(start_str)
                end = parse_datetime(end_str)
            except Exception:
                raise HTTPBadRequest() from None
        else:
            try:
                start_date = parse_date(start_str)
                end_date = parse_date(end_str)
            except Exception:
                raise HTTPBadRequest() from None
            start = datetime.combine(start_date, time(0, 0))
            end = datetime.combine(end_date, time(23, 59, 59, 999999))

        start = sedate.replace_timezone(start, timezone)
        end = sedate.replace_timezone(end, timezone)

        return start, end
    else:
        return None, None


def render_time_range(start: datetime | time, end: datetime | time) -> str:
    if isinstance(end, datetime):
        end = end.time()

    if end in (time(0, 0), time(23, 59, 59, 999999)):
        end_str = '24:00'
    else:
        end_str = f'{end:%H:%M}'

    return f'{start:%H:%M} - {end_str}'


def complete_url(url: str | None) -> str | None:
    # fixes erroneous data retrospectively
    if url == 'https://' or url == 'https://keine':
        return None
    if url is None or url.startswith(('http://', 'https://', '/')):
        return url
    return f'https://{url}'


class ReservationInfo:

    __slots__ = ('resource', 'reservation', 'request', 'translate')

    def __init__(
        self,
        resource: Resource,
        reservation: Reservation,
        request: OrgRequest
    ) -> None:

        self.resource = resource
        self.reservation = reservation
        self.request = request
        self.translate = request.translate

    @property
    def date(self) -> str:
        return self.reservation.display_start().isoformat()

    @property
    def warning(self) -> str | None:
        if self.request.is_manager:
            return None

        reservation_date = self.reservation.display_start().date()

        if self.resource.is_zip_blocked(reservation_date):
            layout = Layout(self.resource, self.request)

            assert self.resource.zipcode_block is not None
            days = self.resource.zipcode_block['zipcode_days']
            assert self.reservation.start is not None
            date = self.reservation.start - timedelta(days=days)

            zipcodes = map(str, self.resource.zipcode_block['zipcode_list'])

            return self.request.translate(_(
                (
                    'You can only reserve this allocation before ${date} '
                    'if you live in the following zipcodes: ${zipcodes}'
                ), mapping={
                    'date': layout.format_date(date, 'date_long'),
                    'zipcodes': ', '.join(zipcodes),
                }
            ))
        return None

    @property
    def time(self) -> str:
        assert self.reservation.start is not None
        assert self.reservation.end is not None
        assert self.reservation.timezone is not None

        if sedate.is_whole_day(
            self.reservation.start,
            self.reservation.end,
            self.reservation.timezone
        ):
            return self.translate(_('Whole day'))
        else:
            return render_time_range(
                self.reservation.display_start(),
                self.reservation.display_end()
            )

    @property
    def delete_link(self) -> str:
        return self.request.csrf_protected_url(
            self.request.link(self.reservation)
        )

    @property
    def price(self) -> PriceDict | None:
        price = self.reservation.price(self.resource)
        return price.as_dict() if price else None

    def as_dict(self) -> dict[str, Any]:
        return {
            'resource': self.resource.name,
            'title': self.resource.title,
            'date': self.date,
            'time': self.time,
            'delete': self.delete_link,
            'quota': self.reservation.quota,
            'created': self.reservation.created.isoformat(),
            'price': self.price,
            'warning': self.warning,
        }


class AllocationEventInfo:

    __slots__ = ('resource', 'allocation', 'availability', 'request',
                 'translate')

    def __init__(
        self,
        resource: Resource,
        allocation: Allocation,
        availability: float,
        request: OrgRequest
    ) -> None:

        self.resource = resource
        self.allocation = allocation
        self.availability = availability
        self.request = request
        self.translate = request.translate

    @classmethod
    def from_allocations(
        cls,
        request: OrgRequest,
        resource: Resource,
        allocations: Iterable[Allocation]
    ) -> list[Self]:

        events = []

        scheduler = resource.scheduler
        allocations = request.exclude_invisible(allocations)

        for key, group in groupby(allocations, key=attrgetter('_start')):
            grouped = tuple(group)
            if len(grouped) == 1 and grouped[0].partly_available:
                # in this case we might need to normalize the availability
                availability = grouped[0].normalized_availability
            else:
                availability = scheduler.queries.availability_by_allocations(
                    grouped
                )

            for allocation in grouped:
                if allocation.is_master:
                    events.append(  # noqa: PERF401
                        cls(
                            resource,
                            allocation,
                            availability,
                            request
                        )
                    )

        return events

    @property
    def event_start(self) -> str:
        return self.allocation.display_start().isoformat()

    @property
    def event_end(self) -> str:
        return self.allocation.display_end().isoformat()

    @property
    def event_identification(self) -> str:
        return '{:%d.%m.%Y}: {}'.format(
            self.allocation.display_start(),
            self.event_time
        )

    @property
    def event_time(self) -> str:
        if self.allocation.whole_day:
            return self.translate(_('Whole day'))
        else:
            return render_time_range(
                self.allocation.display_start(),
                self.allocation.display_end()
            )

    @property
    def quota(self) -> int:
        return self.allocation.quota

    @property
    def quota_left(self) -> int:
        return int(self.quota * self.availability / 100)

    @property
    def event_title(self) -> str:
        if self.allocation.partly_available:
            available = self.translate(_('${percent}% Available', mapping={
                'percent': int(self.availability)
            }))
        else:

            quota = self.quota
            quota_left = self.quota_left

            if quota == 1:
                if quota_left:
                    available = self.translate(_('Available'))
                else:
                    available = self.translate(_('Unavailable'))
            else:
                available = self.translate(
                    _('${num} Available', mapping={
                        'num': quota_left
                    })
                )

        # add an extra space at the end of the event time, so we can hide
        # the <br> tag on the output without having the time and the
        # availability seemingly joined together without space.
        return '\n'.join((self.event_time + ' ', available))

    @property
    def event_classes(self) -> Iterator[str]:
        if self.allocation.end < sedate.utcnow():
            yield 'event-in-past'

        elif not self.request.is_manager and (
            self.resource.is_past_deadline(
                # for partly available allocations we use the end of the
                # allocation, since some small sliver of the allocation
                # may still be before the deadline, we could get a slightly
                # more accurate result by subtracting the raster, but it
                # doesn't seem worth the extra CPU cycles.
                self.allocation.end
                if self.allocation.partly_available
                else self.allocation.start
            ) or self.resource.is_before_lead_time(
                self.allocation.start
            )
        ):
            yield 'event-outside-booking-window'

        if self.quota > 1:
            if self.quota_left == self.quota:
                yield 'event-available'
            elif self.quota_left > 0:
                yield 'event-partly-available'
            else:
                yield 'event-unavailable'
        else:
            if self.availability >= 80.0:
                yield 'event-available'
            elif self.availability >= 20.0:
                yield 'event-partly-available'
            else:
                yield 'event-unavailable'

    @property
    def occupancy_link(self) -> str:
        return self.request.class_link(
            Resource,
            {
                'name': self.resource.name,
                'date': self.allocation.display_start(),
                'view': 'timeGridDay'
            },
            name='occupancy'
        )

    @property
    def event_actions(self) -> Iterator[Link]:
        if self.request.is_manager:
            yield Link(
                _('Edit'),
                self.request.link(self.allocation, name='edit'),
            )

            yield Link(
                _('Tickets'),
                self.request.link(TicketCollection(
                    session=self.request.session,
                    handler='RSV',
                    state='all',
                    extra_parameters={
                        'allocation_id': str(self.allocation.id)
                    }
                )),
            )

            if self.availability == 100.0:
                yield DeleteLink(
                    _('Delete'),
                    self.request.link(self.allocation),
                    confirm=_('Do you really want to delete this allocation?'),
                    extra_information=self.event_identification,
                    yes_button_text=_('Delete allocation')
                )
            else:
                yield Link(
                    _('Occupancy'),
                    self.occupancy_link
                )

                yield DeleteLink(
                    _('Delete'),
                    self.request.link(self.allocation),
                    confirm=_(
                        "This allocation can't be deleted because there are "
                        "existing reservations associated with it."
                    ),
                    extra_information=_(
                        'To delete this allocation, all existing reservations '
                        'need to be cancelled first.'
                    )
                )
        elif self.availability < 100.0 and self.request.has_role('member'):
            if getattr(
                self.resource,
                'occupancy_is_visible_to_members',
                False
            ):
                yield Link(
                    _('Occupancy'),
                    self.occupancy_link
                )

    def as_dict(self) -> dict[str, Any]:
        return {
            'id': self.allocation.id,
            'start': self.event_start,
            'end': self.event_end,
            'title': self.event_title,
            'classNames': list(self.event_classes),
            'display': 'block',
            # extended properties
            'wholeDay': self.allocation.whole_day,
            'partlyAvailable': self.allocation.partly_available,
            'quota': self.allocation.quota,
            'quotaLeft': self.quota_left,
            'partitions': self.allocation.availability_partitions(),
            'actions': [
                link(self.request)
                for link in self.event_actions
            ],
            'editurl': self.request.link(self.allocation, name='edit'),
            'reserveurl': self.request.link(self.allocation, name='reserve')
        }


class AvailabilityEventInfo:

    __slots__ = ('resource', 'allocation', 'request', 'translate')

    def __init__(
        self,
        resource: Resource,
        allocation: Allocation,
        request: OrgRequest
    ) -> None:

        self.resource = resource
        self.allocation = allocation
        self.request = request
        self.translate = request.translate

    @classmethod
    def from_allocations(
        cls,
        request: OrgRequest,
        resource: Resource,
        allocations: Iterable[Allocation]
    ) -> list[Self]:

        return [
            cls(resource, allocation, request)
            for allocation in allocations
            if allocation.is_master
        ]

    @property
    def event_start(self) -> str:
        return self.allocation.display_start().isoformat()

    @property
    def event_end(self) -> str:
        return self.allocation.display_end().isoformat()

    def as_dict(self) -> dict[str, Any]:
        return {
            'id': self.allocation.id,
            'start': self.event_start,
            'end': self.event_end,
            'editable': False,
            'display': 'background',
        }


@lru_cache(maxsize=64)
def event_color(event_name: str) -> str:
    # NOTE: We use sha256 for stability, we could also
    #       use a different stable hash, but we can't use
    #       the builtin Python hash, since it changes with
    #       every run
    h = hashlib.new('md5', event_name.encode('utf-8'), usedforsecurity=False)
    # NOTE: Currently we only need to use the last two digits
    #       but if we add more than 16 colors, then this would
    #       change.
    index = int(h.hexdigest()[-2:], base=16) % len(COLORS)
    return COLORS[index]


class ReservationEventInfo:

    __slots__ = ('resource', 'reservation', 'ticket', 'request', 'translate')

    def __init__(
        self,
        resource: Resource,
        reservation: Reservation,
        ticket: Ticket,
        request: OrgRequest,
    ) -> None:

        self.resource = resource
        self.reservation = reservation
        self.ticket = ticket
        self.request = request
        self.translate = request.translate

    @classmethod
    def from_reservations(
        cls,
        request: OrgRequest,
        resource: Resource,
        reservations: Iterable[tuple[Reservation, Ticket]]
    ) -> list[Self]:

        return [
            cls(
                resource,
                reservation,
                ticket,
                request
            )
            for reservation, ticket in reservations
        ]

    @classmethod
    def from_resources(
        cls,
        request: OrgRequest,
        reservations: Iterable[tuple[Resource, Reservation, Ticket]]
    ) -> list[Self]:

        return [
            cls(
                resource,
                reservation,
                ticket,
                request
            )
            for resource, reservation, ticket in reservations
        ]

    @property
    def event_start(self) -> str:
        return self.reservation.display_start().isoformat()

    @property
    def event_end(self) -> str:
        return self.reservation.display_end().isoformat()

    @property
    def whole_day(self) -> bool:
        start = self.reservation.display_start()
        end = self.reservation.display_end()
        tz = self.reservation.timezone
        assert tz is not None
        return sedate.is_whole_day(start, end, tz)

    @property
    def event_time(self) -> str:
        if self.whole_day:
            return self.translate(_('Whole day'))
        else:
            return render_time_range(
                self.reservation.display_start(),
                self.reservation.display_end()
            )

    @property
    def quota(self) -> int:
        return self.reservation.quota

    @property
    def accepted(self) -> bool:
        if self.reservation.data and self.reservation.data.get('accepted'):
            return True
        return False

    @property
    def event_title(self) -> str:
        return '\n'.join(part for part in (
            self.ticket.number,
            self.event_time,
            f'{self.translate(_("Quota"))}: {self.quota}'
            if getattr(self.resource, 'show_quota', False) else '',
            self.ticket.tag,
            self.reservation.email,
            self.translate(_('Pending approval')) if not self.accepted else '',
        ) if part)

    @property
    def event_classes(self) -> Iterator[str]:
        if self.accepted:
            yield 'event-accepted'
        else:
            yield 'event-pending'

        # HACK: Find event element by id, it would be better if fullcalendar
        #       generated an element id we could use, but we'll work with
        #       what we have.
        yield f'event-{self.reservation.id}'

    @property
    def color(self) -> str | None:
        tag = self.ticket.tag
        if not tag:
            return None

        for tag_config in self.request.app.org.ticket_tags or ():
            if not isinstance(tag_config, dict):
                continue

            meta = tag_config.get(tag)
            if not meta:
                continue

            color = meta.get('Color')
            if color is None:
                break
            return color
        return event_color(tag)

    @property
    def editable(self) -> bool:
        if self.reservation.display_start() < sedate.utcnow():
            return False
        return not self.accepted

    def as_dict(self) -> dict[str, Any]:
        is_manager = self.request.is_manager
        return {
            'id': self.reservation.id,
            'start': self.event_start,
            'end': self.event_end,
            'backgroundColor': self.color,
            'title': self.event_title,
            'classNames': list(self.event_classes),
            'url': self.request.link(self.ticket),
            'display': 'block',
            # extended properties
            'wholeDay': self.whole_day,
            'editable': is_manager and self.editable,
            'editurl': self.request.csrf_protected_url(self.request.link(
                self.ticket,
                name='adjust-reservation',
                query_params={'reservation-id': str(self.reservation.id)}
            )) if is_manager else None,
        }


class MyReservationEventInfo:

    __slots__ = (
        'id',
        'token',
        'start',
        'end',
        'timezone',
        'accepted',
        'resource',
        'resource_id',
        'ticket_id',
        'handler_code',
        'ticket_number',
        'key_code',
        'request',
        'translate',
    )

    def __init__(
        self,
        id: int,
        token: UUID,
        start: datetime,
        end: datetime,
        accepted: bool,
        timezone: str,
        resource: str,
        resource_id: UUID,
        ticket_id: UUID,
        handler_code: str,
        ticket_number: str,
        key_code: str | None,
        request: OrgRequest,
    ) -> None:

        self.id = id
        self.token = token
        self.start = sedate.to_timezone(start, timezone)
        self.end = sedate.to_timezone(
            end + timedelta(microseconds=1),
            timezone
        )
        self.timezone = timezone
        self.accepted = accepted
        self.resource = resource
        self.resource_id = resource_id
        self.ticket_id = ticket_id
        self.handler_code = handler_code
        self.key_code = key_code
        self.request = request
        self.translate = request.translate

    @property
    def event_start(self) -> str:
        return self.start.isoformat()

    @property
    def event_end(self) -> str:
        return self.end.isoformat()

    @property
    def whole_day(self) -> bool:
        start = self.start
        end = self.end
        tz = self.timezone
        return sedate.is_whole_day(start, end, tz)

    @property
    def event_time(self) -> str:
        if self.whole_day:
            return self.translate(_('Whole day'))
        else:
            return render_time_range(self.start, self.end)

    @property
    def event_title(self) -> str:
        return '\n'.join(part for part in (
            self.resource,
            self.event_time,
            f'{self.translate(_("Key Code"))}: {self.key_code}'
            if self.key_code else '',
            self.translate(_('Pending approval')) if not self.accepted else '',
        ) if part)

    @property
    def event_classes(self) -> Iterator[str]:
        if self.accepted:
            yield 'event-accepted'
        else:
            yield 'event-pending'

        # HACK: Find event element by id, it would be better if fullcalendar
        #       generated an element id we could use, but we'll work with
        #       what we have.
        yield f'event-{self.id}'

    def as_dict(self) -> dict[str, Any]:
        is_manager = self.request.is_manager
        return {
            'id': self.id,
            'start': self.event_start,
            'end': self.event_end,
            'title': self.event_title,
            'classNames': list(self.event_classes),
            'url': self.request.class_link(
                Ticket,
                {
                    'handler_code': self.handler_code,
                    'id': self.ticket_id
                },
                name='' if is_manager else 'status'
            ),
            'display': 'block',
            # extended properties
            'wholeDay': self.whole_day,
            'editable': False,
            'editurl': None,
        }


class FindYourSpotEventInfo:

    __slots__ = ('allocation', 'slot_time', 'availability', 'quota_left',
                 'request', 'translate', 'adjustable')

    def __init__(
        self,
        allocation: Allocation,
        slot_time: DateRange | None,
        availability: float,
        quota_left: int,
        request: OrgRequest,
        *,
        adjustable: bool = False
    ) -> None:

        self.allocation = allocation
        self.slot_time = slot_time
        self.availability = availability
        self.quota_left = quota_left
        self.request = request
        self.adjustable = adjustable
        self.translate = request.translate

    @property
    def event_start(self) -> str:
        if self.slot_time and self.allocation.partly_available:
            return self.slot_time[0].isoformat()
        return self.allocation.display_start().isoformat()

    @property
    def event_end(self) -> str:
        if self.slot_time and self.allocation.partly_available:
            return self.slot_time[1].isoformat()
        return self.allocation.display_end().isoformat()

    @property
    def event_time(self) -> str:
        if self.slot_time and self.allocation.partly_available:
            return render_time_range(*self.slot_time)

        if self.allocation.whole_day:
            return self.translate(_('Whole day'))
        else:
            return render_time_range(
                self.allocation.display_start(),
                self.allocation.display_end()
            )

    @property
    def quota(self) -> int:
        return self.allocation.quota

    @property
    def whole_day(self) -> str:
        if self.allocation.whole_day:
            return 'true'
        else:
            return 'false'

    @property
    def partly_available(self) -> str:
        if self.allocation.partly_available:
            return 'true'
        else:
            return 'false'

    @property
    def available(self) -> str:
        if self.allocation.partly_available:
            available = self.translate(_('${percent}% Available', mapping={
                'percent': int(self.availability)
            }))
        else:

            quota = self.quota
            quota_left = self.quota_left

            if quota == 1:
                if quota_left:
                    available = self.translate(_('Available'))
                else:
                    available = self.translate(_('Unavailable'))
            else:
                available = self.translate(
                    _('${num} Available', mapping={
                        'num': quota_left
                    })
                )

        return available

    @property
    def event_classes(self) -> Iterator[str]:
        if self.allocation.end < sedate.utcnow():
            yield 'event-in-past'

        if self.quota > 1:
            if self.quota_left == self.quota:
                yield 'event-available'
            elif self.quota_left > 0:
                yield 'event-partly-available'
            else:
                yield 'event-unavailable'
        else:
            if self.availability == 100.0 or (
                self.availability > 100.0 and self.adjustable
            ):
                yield 'event-available'
            elif self.availability >= 5.0:
                yield 'event-partly-available'
            else:
                yield 'event-unavailable'

        if self.adjustable:
            yield 'event-adjustable'

    @property
    def css_class(self) -> str:
        return ' '.join(self.event_classes)

    @property
    def reserveurl(self) -> str:
        return self.request.link(self.allocation, 'reserve')


libres_error_messages = {
    libres_errors.OverlappingAllocationError:
    _('A conflicting allocation exists for the requested time period.'),

    libres_errors.OverlappingReservationError:
    _('A conflicting reservation exists for the requested time period.'),

    libres_errors.AffectedReservationError:
    _('An existing reservation would be affected by the requested change.'),

    libres_errors.AffectedPendingReservationError:
    _("This change cannot be made because there is still an open reservation "
      "in someone's cart. The reservation needs to be submitted or expire "
      "before you can proceed."),

    libres_errors.AlreadyReservedError:
    _('The requested period is no longer available.'),

    libres_errors.NotReservableError:
    _('No reservable slot found.'),

    libres_errors.ReservationTooLong:
    _("Reservations can't be made for more than 24 hours at a time."),

    libres_errors.ReservationParametersInvalid:
    _('The given reservation paramters are invalid.'),

    libres_errors.InvalidReservationToken:
    _('The given reservation token is invalid.'),

    libres_errors.InvalidReservationError:
    _('The given reservation paramters are invalid.'),

    libres_errors.QuotaOverLimit:
    _('The requested number of reservations is higher than allowed.'),

    libres_errors.InvalidQuota:
    _('The requested quota is invalid (must be at least one).'),

    libres_errors.QuotaImpossible:
    _('The allocation does not have enough free spots.'),

    libres_errors.InvalidAllocationError:
    _('The resulting allocation would be invalid.'),

    libres_errors.NoReservationsToConfirm:
    _('No reservations to confirm.'),

    libres_errors.TimerangeTooLong:
    _('The given timerange is longer than the existing allocation.'),

    libres_errors.ReservationTooShort:
    _('Reservation too short. A reservation must last at least 5 minutes.')
}


def get_libres_error(e: Exception, request: OrgRequest) -> str:
    etype = type(e)
    assert etype in libres_error_messages, f'Unknown libres error {etype}'

    return request.translate(libres_error_messages[etype])


def show_libres_error(
    e: Exception,
    request: OrgRequest
) -> None:
    """ Shows a human readable error message for the given libres exception,
    using request.alert.

    """
    request.alert(get_libres_error(e, request))


def predict_next_daterange(
    dateranges: Sequence[DateRange],
    min_probability: float = 0.8,
    tzinfo: TzInfo | None = None
) -> DateRange | None:
    """ Takes a list of dateranges (start, end) and tries to predict the next
    daterange in the list.

    See :func:`predict_next_value` for more information.

    """

    if not dateranges:
        return None

    if tzinfo is None:
        # we remember the original tzinfo of the final date
        # since that is the one we will need to transform back
        last_end = dateranges[-1][1]
        if hasattr(last_end, 'tzinfo'):
            # FIXME: we assume we only ever use pytz timezones
            #        but we probably should still check here
            #        that we actually do
            tzinfo = last_end.tzinfo  # type:ignore[assignment]

    if tzinfo is not None:
        # if we did get a tz aware datetime then we need to strip
        # the tzinfo on the input dateranges so calculations won't
        # have different results in summer vs. standard time
        dateranges = [
            (s.replace(tzinfo=None), e.replace(tzinfo=None))
            for s, e in dateranges
        ]

    def add_delta(
        time_range: DateRange,
        delta: timedelta
    ) -> DateRange | None:

        start, end = time_range

        # after calculating the tz-naive suggestion we need to
        # add the original tzinfo back, but handle DST <-> ST
        # transitions correctly
        start += delta
        end += delta

        if tzinfo is None:
            # we never were localized to begin with so just return
            return start, end

        # if we didn't get a pytz tzinfo we just add it back and
        # hope it does the correct thing (it probably won't) but
        # at that point it is no longer our responsibility
        if not hasattr(tzinfo, 'localize'):
            return start.replace(tzinfo=tzinfo), end.replace(tzinfo=tzinfo)

        try:
            # try to return the localized daterange without worrying
            # about DST and ST, pytz will throw an exception if we
            # use an ambiguous or non-existent time
            return (tzinfo.localize(start, is_dst=None),
                    tzinfo.localize(end, is_dst=None))
        except pytz.NonExistentTimeError:
            # in this case we don't make a suggestion (because we can't)
            return None
        except pytz.AmbiguousTimeError:
            # we treat ambiguous times as standard time always, in the
            # calendar it shouldn't make a visual difference anyways
            return (tzinfo.localize(start, is_dst=False),
                    tzinfo.localize(end, is_dst=False))

    return predict_next_value(
        values=dateranges,
        min_probability=min_probability,
        compute_delta=lambda x, y: y[0] - x[0],
        add_delta=add_delta
    )


# NOTE: We could increase type safety by providing a _T that's bound
#       to a protocol which implements subtraction and addition, but
#       __add__ vs __radd__ and __sub__ vs __rsub__ makes this difficult
@overload
def predict_next_value(
    values: Sequence[_T],
    min_probability: float = 0.8,
) -> _T | None: ...


@overload
def predict_next_value(
    values: Sequence[_T],
    min_probability: float,
    compute_delta: Callable[[_T, _T], _DeltaT],
    add_delta: Callable[[_T, _DeltaT], _T | None]
) -> _T | None: ...


@overload
def predict_next_value(
    values: Sequence[_T],
    min_probability: float = 0.8,
    *,
    compute_delta: Callable[[_T, _T], _DeltaT],
    add_delta: Callable[[_T, _DeltaT], _T | None]
) -> _T | None: ...


def predict_next_value(
    values: Sequence[_T],
    min_probability: float = 0.8,
    compute_delta: Callable[[Any, Any], Any] = lambda x, y: y - x,
    add_delta: Callable[[Any, Any], Any | None] = add
) -> _T | None:
    """ Takes a list of values and tries to predict the next value in the
    series.

    Meant to work on a small set of ranges (with first predictions
    appearing with only three values), this algorithm will look at all
    possible deltas between the values and keep track of the probability
    of delta y following delta x.

    If the delta between the second last and last value has a high
    probability of being followed by some delta p, then delta p is used to
    predict the next range.

    If the probability is too low (signified by min_probability), then None
    is returned.

    For large ranges better statistical models should be used. Here we are
    concerned with small series of data to answer the question "if a user
    selected three values, what will his fourth be?"

    If we for example know that the user selected 1, 2 and 3, then 4 is the
    next probable value in the series.

    """

    if len(values) < 3:
        return None

    deltas: dict[Any, list[Any]] = defaultdict(list)

    previous = values[0]
    previous_delta: Any | None = None

    for current in values[1:]:
        delta = compute_delta(previous, current)

        if previous_delta is not None:
            deltas[previous_delta].append(delta)

        previous = current
        previous_delta = delta

    assert previous_delta is not None
    next_deltas = deltas[previous_delta]

    if not next_deltas:
        return None

    predicted_delta, count = Counter(next_deltas).most_common(1)[0]
    probability = count / len(next_deltas)

    if probability >= min_probability:
        return add_delta(values[-1], predicted_delta)
    else:
        return None


@overload
def group_by_column(
    request: OrgRequest,
    query: Query[_T],
    group_column: Column[str] | Column[str | None],
    sort_column: Column[_SortT],
    default_group: str | None = None,
    transform: Callable[[_T], _T] | None = None
) -> dict[str, list[_T]]: ...


@overload
def group_by_column(
    request: OrgRequest,
    query: Query[_T],
    group_column: Column[str] | Column[str | None],
    sort_column: Column[_SortT],
    default_group: str | None,
    transform: Callable[[_T], _TransformedT]
) -> dict[str, list[_TransformedT]]: ...


@overload
def group_by_column(
    request: OrgRequest,
    query: Query[_T],
    group_column: Column[str] | Column[str | None],
    sort_column: Column[_SortT],
    default_group: str | None = None,
    *,
    transform: Callable[[_T], _TransformedT]
) -> dict[str, list[_TransformedT]]: ...


def group_by_column(
    request: OrgRequest,
    query: Query[_T],
    group_column: Column[str] | Column[str | None],
    sort_column: Column[_SortT],
    default_group: str | None = None,
    transform: Callable[[Any], Any] | None = None
) -> dict[str, list[Any]]:
    """ Groups the given query by the given group.

    :param request:
        The current request used for translation and to exclude invisible
        records.

    :param query:
        The query that should be grouped

    :param group_column:
        The column by which the grouping should happen.

    :param sort_column:
        The column by which the records should be sorted.

    :param default_group:
        The group in use if the found group is empty (optional).

    :param transform:
        Called with each record to transform the result (optional).

    """

    default_group = default_group or request.translate(_('General'))

    query = query.order_by(nullsfirst(group_column))
    records = request.exclude_invisible(query)

    grouped = OrderedDict()

    def group_key(record: _T) -> str:
        return getattr(record, group_column.name) or default_group

    def sort_key(record: _T) -> _SortT:
        return getattr(record, sort_column.name)

    transform = transform or (lambda v: v)

    # groupby expects the input iterable (records) to already be sorted
    records = sorted(records, key=group_key)
    for group, items in groupby(records, group_key):
        grouped[group] = [
            transform(i)
            for i in sorted(items, key=sort_key)
        ]

    return grouped


def keywords_first(
    keywords: Sequence[str]
) -> Callable[[str], tuple[int, str]]:
    """ Returns a sort key which prefers values matching the given keywords
    before other values which are sorted alphabetically.

    """
    assert hasattr(keywords, 'index')

    def sort_key(v: str) -> tuple[int, str]:
        try:
            return keywords.index(v) - len(keywords), ''
        except ValueError:
            return 0, v
    return sort_key


def hashtag_elements(request: OrgRequest, text: str) -> Markup:
    """ Takes a text and adds html around the hashtags found inside. """

    def replace_tag(match: re.Match[str]) -> str:
        tag = match.group()
        link = request.link(Search(request, query=tag, page=0))
        return f'<a class="hashtag" href="{link}">{tag}</a>'

    # NOTE: We need to restore Markup after re.sub call
    return Markup(HASHTAG.sub(replace_tag, escape(text)))  # nosec: B704


def emails_for_new_ticket(
    request: OrgRequest,
    ticket: Ticket,
) -> Iterator[Address]:
    """ Returns a set of e-mail addressed that would like to be notified
    about the creation of this ticket.

    Users can be part of a UserGroup with ticket permissions. This means the
    users in this group are interested in/responsible for a subset of tickets.

    This allows for more granular control over who gets notified.

    """
    seen = set()
    if request.email_for_new_tickets:
        # adding this to seen ensures it does not receive two emails
        address = coerce_address(request.email_for_new_tickets)
        seen.add(address.addr_spec)
        yield address

    permissions = request.app.ticket_permissions.get(ticket.handler_code, {})
    exclusive_group_ids = permissions.get(ticket.group, [])

    # even if there are no exclusive permissions for this group
    # there may still be exclusive permissions for the handler code
    if not exclusive_group_ids and ticket.group:
        exclusive_group_ids = permissions.get(None, [])

    query = request.session .query(UserGroup).join(TicketPermission)
    query = query.filter(TicketPermission.immediate_notification.is_(True))
    query = query.filter(TicketPermission.handler_code == ticket.handler_code)

    # if the permission applies to the whole handler_code
    # then there can't be any exclusive permissions for any
    # specific group we're not a part of, since then we won't
    # have permission to access the ticket
    general_condition = TicketPermission.group.is_(None)
    if exclusive_group_ids:
        general_condition &= UserGroup.id.in_(exclusive_group_ids)
    query = query.filter(
        general_condition | (TicketPermission.group == ticket.group)
    )

    for email, name in query.join(UserGroup.users).with_entities(
        case([(
            UserGroup.meta['shared_email'].isnot(None),
            UserGroup.meta['shared_email'].astext,
        )], else_=User.username),
        case([(
            UserGroup.meta['shared_email'].isnot(None),
            UserGroup.name,
        )], else_=User.realname),
    ).distinct():

        if email in seen:
            continue

        seen.add(email)
        try:
            yield Address(
                display_name=name or '',
                addr_spec=email
            )
        except ValueError:
            # if it's not a valid address then skip it
            pass


# from most narrow to widest
ORDERED_ACCESS = (
    'private',
    'member',
    'secret_mtan',
    'mtan',
    'secret',
    'public'
)


def widest_access(*accesses: str) -> str:
    index = 0
    for access in accesses:
        try:
            # we only want to look at indexes starting with the one
            # we're already at, otherwise we're lowering the access
            index = ORDERED_ACCESS.index(access, index)
        except ValueError:
            pass
    return ORDERED_ACCESS[index]


def narrowest_access(*accesses: str) -> str:
    index = len(ORDERED_ACCESS) - 1
    for access in accesses:
        try:
            # we only want to look at indexes starting with the one
            # we're already at, otherwise we're lowering the access
            index = ORDERED_ACCESS.index(access, 0, index)
        except ValueError:
            pass
    return ORDERED_ACCESS[index]


@overload
def extract_categories_and_subcategories(
    categories: Sequence[dict[str, list[str]] | str],
    flattened: Literal[False] = False
) -> tuple[list[str], list[list[str]]]: ...

@overload
def extract_categories_and_subcategories(
    categories: Sequence[dict[str, list[str]] | str],
    flattened: Literal[True]
) -> list[str]: ...


def extract_categories_and_subcategories(
    categories: Sequence[dict[str, list[str]] | str],
    flattened: bool = False
) -> tuple[list[str], list[list[str]]] | list[str]:
    """
    Extracts categories and subcategories from the `newsletter categories`
    dictionary in `newsletter settings`.

    Example for categories dict:
    [
        {'main_category_1'},
        {'main_category_2': ['sub_category_21', 'sub_category_22']}
    ]
    returning a tuple of lists:
        ['main_category_1', 'main_category_2'],
        [[], ['sub_category_21', 'sub_category_22']]
    if `flattened` is True, it returns a flat list of the above tuple:
        ['main_category_1', 'main_category_2', 'sub_category_21',
        'sub_category_22']

    """
    cats: list[str] = []
    sub_cats: list[list[str]] = []

    if not categories:
        return cats, sub_cats

    for item in categories:
        if isinstance(item, dict):
            for topic, subs in item.items():
                cats.append(topic)
                sub_cats.append(subs or [])
        else:
            cats.append(item)
            sub_cats.append([])

    if flattened:
        cats.extend(
            item
            for sublist in sub_cats
            if sublist
            for item in sublist
        )
        return cats

    return cats, sub_cats


def format_phone_number(phone_number: str) -> str:
    """
    Returns phone number in the international format +41 79 123 45 67
    """
    if not phone_number:
        return ''

    try:
        parsed = phonenumbers.parse(phone_number, 'CH')

        return phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )
    except phonenumbers.phonenumberutil.NumberParseException:
        return phone_number


def get_current_tickets_url(request: OrgRequest) -> str:
    """ Get the tickets url with the parameters we last visited. """
    state = request.browser_session.get('tickets_state')
    return request.class_link(
        TicketCollection,
        state or {'handler': 'ALL', 'state': 'open', 'page': 0}
    )


def invoice_items_for_submission(
    request: CoreRequest,
    form: Form,
    submission: FormSubmission
) -> list[InvoiceItemMeta]:

    # NOTE: Eventually we may need something more sophisticated
    vat_rate = Decimal(org.vat_rate) if (
        getattr(submission.form, 'show_vat', False)
        and (org := getattr(request.app, 'org', None))
        and org.vat_rate
    ) else None
    extra = {'submission_id': submission.id}
    items = form.invoice_items(extra=extra, vat_rate=vat_rate)
    discounts = form.discount_items(extra=extra, vat_rate=vat_rate)

    # for backwards compatibility we still support a raw price
    # instead of a more complete invoice item
    if 'invoice_item' in submission.meta:
        items.insert(0, InvoiceItemMeta(**submission.meta['invoice_item']))
    elif 'price' in submission.meta:
        price = Price(**submission.meta['price'])
        items.insert(0, InvoiceItemMeta(
            text=request.translate(_('Lump sum')),
            group='submission',
            unit=price.amount,
            vat_rate=vat_rate,
        ))

    total = InvoiceItemMeta.total(items)
    if discounts:
        remainder = total
        for discount in discounts:
            item = discount.apply_discount(total, remainder)
            remainder += item.amount
            assert remainder >= 0.0
            items.append(item)
        total = remainder

    return items


def currency_for_submission(form: Form, submission: FormSubmission) -> str:
    if 'currency' in submission.meta:
        return submission.meta['currency']

    if 'price' in submission.meta:
        return submission.meta['price'].get('currency', 'CHF')

    # We just pick the first currency from any pricing rule we can find
    # if we can't find any, then we fall back to 'CHF'. Although that
    # should be an invalid form definition.
    for field in form._fields.values():
        if not hasattr(field, 'pricing'):
            continue

        rules = field.pricing.rules
        if not rules:
            continue

        return next(iter(rules.values())).currency or 'CHF'
    return 'CHF'


def group_invoice_items(
    invoice_items: Iterable[_ItemT]
) -> dict[str, list[_ItemT]]:

    def sort_key(item: _ItemT) -> tuple[int, str]:
        match item.group:
            case 'submission' | 'reservation' | 'migration':
                return 0, item.group
            case 'form':
                return 1, item.group
            case 'manual' | 'reduced_amount':
                return 99, 'manual'
            case _:
                return 2, item.group

    return {
        group: list(items)
        for (__, group), items in groupby(
            sorted(invoice_items, key=sort_key),
            key=sort_key
        )
    }
