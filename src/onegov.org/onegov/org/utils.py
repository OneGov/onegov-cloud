import colorsys
import re
import sedate

from collections import defaultdict, Counter, OrderedDict
from datetime import datetime, time
from dateutil import rrule
from onegov.core.cache import lru_cache
from isodate import parse_date, parse_datetime
from itertools import groupby
from libres.modules import errors as libres_errors
from lxml.html import fragments_fromstring, tostring
from onegov.file import File, FileCollection
from onegov.org import _
from onegov.org.elements import DeleteLink, Link
from onegov.ticket import TicketCollection
from operator import attrgetter
from sqlalchemy import nullsfirst
from purl import URL


# for our empty paragraphs approach we don't need a full-blown xml parser
# since we only remove a very limited set of paragraphs
EMPTY_PARAGRAPHS = re.compile(r'<p>\s*<br>\s*</p>')


def djb2_hash(text, size):
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


@lru_cache(maxsize=32)
def get_user_color(username):
    """ Gets a user color for each username which is used for the
    user-initials-* elements. Each username is mapped to a color.

    Since the colorspace is very limited there are lots of collisions.

    :returns: The user color in an css rgb string.

    """

    h = 100 / djb2_hash(username, 360)
    l = 0.9  # noqa
    s = 0.5

    r, g, b = colorsys.hls_to_rgb(h, l, s)

    return '#{0:02x}{1:02x}{2:02x}'.format(
        int(round(r * 255)),
        int(round(g * 255)),
        int(round(b * 255))
    )


def format_time_range(start, end):
    return correct_time_range('{:%H:%M} - {:%H:%M}'.format(start, end))


def correct_time_range(string):
    if string.endswith('00:00'):
        return string[:-5] + '24:00'
    return string


def add_class_to_node(node, classname):
    """ Adds the given classname to the given lxml node's class list. """

    if 'class' in node.attrib:
        node.attrib['class'] += ' ' + classname
    else:
        node.attrib['class'] = classname


def annotate_html(html, request=None):
    """ Takes the given html and annotates the following elements for some
    advanced styling:

        * Every paragraph containing an img element will be marked with the
          `has-img` class.

        * If a link is found which points to a youtube or a vimeo video, the
          link itself as well as the surrounding paragraph is marked
          with the `has-video` class

    """

    if not html:
        return html

    fragments = fragments_fromstring(html)
    images = []

    # we perform a root xpath lookup, which will result in all paragraphs
    # being looked at - so we don't need to loop over all elements (yah, it's
    # a bit weird)
    for element in fragments[:1]:

        # instead of failing, lxml will return strings instead of elements if
        # they can't be parsed.. so we have to inspect the objects
        if not hasattr(element, 'xpath'):
            return html

        for paragraph in element.xpath('//p[img]'):
            add_class_to_node(paragraph, 'has-img')

        condition = ' or '.join(
            'starts-with(@href, "{}")'.format(url) for url in {
                'https://www.youtube.com',
                'https://www.vimeo.com',
                'https://vimeo',
            }
        )

        for a in element.xpath('//a[{}]'.format(condition)):
            add_class_to_node(a, 'has-video')

            # find the closest paragraph in the ancestrage, but don't look far
            parent = a.getparent()

            for i in range(0, 3):
                if parent.tag == 'p':
                    add_class_to_node(parent, 'has-video')
                    break
                parent = parent.getparent()

        for img in element.xpath('//img'):
            img.set('class', 'lazyload-alt')
            images.append(img)

    if request:
        set_image_sizes(images, request)

    return ''.join(tostring(e).decode('utf-8') for e in fragments)


def remove_empty_paragraphs(html):
    if not html:
        return html

    return EMPTY_PARAGRAPHS.sub('', html)


def set_image_sizes(images, request):
    internal_src = re.compile(r'.*/storage/([a-z0-9]+)')

    def get_image_id(img):
        match = internal_src.match(img.get('src', ''))

        if match and match.groups():
            return match.group(1)

    images = {get_image_id(img): img for img in images}

    if images:
        q = FileCollection(request.session, type='image').query()
        q = q.with_entities(File.id, File.reference)
        q = q.filter(File.id.in_(images))

        sizes = {i.id: i.reference for i in q}

        for id, image in images.items():
            if id in sizes:
                image.set('width', sizes[id].size[0])
                image.set('height', sizes[id].size[1])


def parse_fullcalendar_request(request, timezone):
    """ Parses start and end from the given fullcalendar request. It is
    expected that no timezone is passed (the default).

    See `<http://fullcalendar.io/docs/timezone/timezone/>`_

    :returns: A tuple of timezone-aware datetime objects or (None, None).

    """
    start = request.params.get('start')
    end = request.params.get('end')

    if start and end:
        if 'T' in start:
            start = parse_datetime(start)
            end = parse_datetime(end)
        else:
            start = datetime.combine(parse_date(start), time(0, 0))
            end = datetime.combine(parse_date(end), time(23, 59, 59, 999999))

        start = sedate.replace_timezone(start, timezone)
        end = sedate.replace_timezone(end, timezone)

        return start, end
    else:
        return None, None


def render_time_range(start, end):
    start = '{:%H:%M}'.format(start)

    if (end.time() == time(0, 0)):
        end = '24:00'
    else:
        end = '{:%H:%M}'.format(end)

    return ' - '.join((start, end))


class ReservationInfo(object):

    __slots__ = ['resource', 'reservation', 'request', 'translate']

    def __init__(self, resource, reservation, request):
        self.resource = resource
        self.reservation = reservation
        self.request = request
        self.translate = request.translate

    @property
    def date(self):
        return self.reservation.display_start().isoformat()

    @property
    def time(self):
        if sedate.is_whole_day(
            self.reservation.start,
            self.reservation.end,
            self.reservation.timezone
        ):
            return self.translate(_("Whole day"))
        else:
            return render_time_range(
                self.reservation.display_start(),
                self.reservation.display_end()
            )

    @property
    def delete_link(self):
        url = self.request.link(self.reservation)
        url = URL(url).query_param('csrf-token', self.request.new_csrf_token())

        return url.as_string()

    @property
    def price(self):
        price = self.reservation.price(self.resource)
        return price and price.as_dict()

    def as_dict(self):
        return {
            'date': self.date,
            'time': self.time,
            'delete': self.delete_link,
            'quota': self.reservation.quota,
            'created': self.reservation.created.isoformat(),
            'price': self.price
        }


class AllocationEventInfo(object):

    __slots__ = ['allocation', 'availability', 'request', 'translate']

    def __init__(self, allocation, availability, request):
        self.allocation = allocation
        self.availability = availability
        self.request = request
        self.translate = request.translate

    @classmethod
    def from_allocations(cls, request, scheduler, allocations):
        events = []

        for key, group in groupby(allocations, key=attrgetter('_start')):
            grouped = tuple(group)
            availability = scheduler.queries.availability_by_allocations(
                grouped
            )

            for allocation in grouped:
                if allocation.is_master:
                    events.append(
                        cls(
                            allocation,
                            availability,
                            request
                        )
                    )

        return events

    @property
    def event_start(self):
        return self.allocation.display_start().isoformat()

    @property
    def event_end(self):
        return self.allocation.display_end().isoformat()

    @property
    def event_identification(self):
        return '{:%d.%m.%Y}: {}'.format(
            self.allocation.display_start(),
            self.event_time
        )

    @property
    def event_time(self):
        if self.allocation.whole_day:
            return self.translate(_("Whole day"))
        else:
            return render_time_range(
                self.allocation.display_start(),
                self.allocation.display_end()
            )

    @property
    def quota(self):
        return self.allocation.quota

    @property
    def quota_left(self):
        return int(self.quota * self.availability / 100)

    @property
    def event_title(self):
        if self.allocation.partly_available:
            available = self.translate(_("${percent}% Available", mapping={
                'percent': int(self.availability)
            }))
        else:

            quota = self.quota
            quota_left = self.quota_left

            if quota == 1:
                if quota_left:
                    available = self.translate(_("Available"))
                else:
                    available = self.translate(_("Unavailable"))
            else:
                available = self.translate(
                    _("${num}/${max} Available", mapping={
                        'num': quota_left,
                        'max': quota
                    })
                )

        # add an extra space at the end of the event time, so we can hide
        # the <br> tag on the output without having the time and the
        # availability seemingly joined together without space.
        return '\n'.join((self.event_time + ' ', available))

    @property
    def event_class(self):
        if self.quota > 1:
            if self.quota_left == self.quota:
                return 'event-available'
            elif self.quota_left > 0:
                return 'event-partly-available'
            else:
                return 'event-unavailable'
        else:
            if self.availability >= 80.0:
                return 'event-available'
            if self.availability >= 20.0:
                return 'event-partly-available'
            else:
                return 'event-unavailable'

    @property
    def event_actions(self):
        if self.request.is_manager:
            yield Link(
                _("Edit"),
                self.request.link(self.allocation, name='edit'),
            )

            yield Link(
                _("Tickets"),
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
                    _("Delete"),
                    self.request.link(self.allocation),
                    confirm=_("Do you really want to delete this allocation?"),
                    extra_information=self.event_identification,
                    yes_button_text=_("Delete allocation")
                )
            else:
                yield DeleteLink(
                    _("Delete"),
                    self.request.link(self.allocation),
                    confirm=_(
                        "This allocation can't be deleted because there are "
                        "existing reservations associated with it."
                    ),
                    extra_information=_(
                        "To delete this allocation, all existing reservations "
                        "need to be cancelled first."
                    )
                )

    def as_dict(self):
        return {
            'id': self.allocation.id,
            'start': self.event_start,
            'end': self.event_end,
            'title': self.event_title,
            'wholeDay': self.allocation.whole_day,
            'partlyAvailable': self.allocation.partly_available,
            'quota': self.allocation.quota,
            'quotaLeft': self.quota_left,
            'className': self.event_class,
            'partitions': self.allocation.availability_partitions(),
            'actions': [
                link(self.request).decode('utf-8')
                for link in self.event_actions
            ],
            'editurl': self.request.link(self.allocation, name='edit'),
            'reserveurl': self.request.link(self.allocation, name='reserve')
        }


libres_error_messages = {
    libres_errors.OverlappingAllocationError:
    _("A conflicting allocation exists for the requested time period."),

    libres_errors.OverlappingReservationError:
    _("A conflicting reservation exists for the requested time period."),

    libres_errors.AffectedReservationError:
    _("An existing reservation would be affected by the requested change."),

    libres_errors.AffectedPendingReservationError:
    _("A pending reservation would be affected by the requested change."),

    libres_errors.AlreadyReservedError:
    _("The requested period is no longer available."),

    libres_errors.NotReservableError:
    _("No reservable slot found."),

    libres_errors.ReservationTooLong:
    _("Reservations can't be made for more than 24 hours at a time."),

    libres_errors.ReservationParametersInvalid:
    _("The given reservation paramters are invalid."),

    libres_errors.InvalidReservationToken:
    _("The given reservation token is invalid."),

    libres_errors.InvalidReservationError:
    _("The given reservation paramters are invalid."),

    libres_errors.QuotaOverLimit:
    _("The requested number of reservations is higher than allowed."),

    libres_errors.InvalidQuota:
    _("The requested quota is invalid (must be at least one)."),

    libres_errors.QuotaImpossible:
    _("The allocation does not have enough free spots."),

    libres_errors.InvalidAllocationError:
    _("The resulting allocation would be invalid."),

    libres_errors.NoReservationsToConfirm:
    _("No reservations to confirm."),

    libres_errors.TimerangeTooLong:
    _("The given timerange is longer than the existing allocation."),

    libres_errors.ReservationTooShort:
    _("Reservation too short. A reservation must last at least 5 minutes.")
}


def get_libres_error(e, request):
    assert type(e) in libres_error_messages, (
        "Unknown libres error {}".format(type(e))
    )

    return request.translate(libres_error_messages.get(type(e)))


def show_libres_error(e, request):
    """ Shows a human readable error message for the given libres exception,
    using request.alert.

    """
    request.alert(get_libres_error(e, request))


def predict_next_daterange(dateranges, min_probability=0.8):
    """ Takes a list of dateranges (start, end) and tries to predict the next
    daterange in the list.

    See :func:`predict_next_value` for more information.

    """

    return predict_next_value(
        values=dateranges,
        min_probability=min_probability,
        compute_delta=lambda x, y: y[0] - x[0],
        add_delta=lambda x, d: (x[0] + d, x[1] + d)
    )


def predict_next_value(values, min_probability=0.8,
                       compute_delta=lambda x, y: y - x,
                       add_delta=lambda x, d: x + d):
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

    deltas = defaultdict(list)

    previous = values[0]
    previous_delta = None

    for current in values[1:]:
        delta = compute_delta(previous, current)

        if previous_delta is not None:
            deltas[previous_delta].append(delta)

        previous = current
        previous_delta = delta

    next_deltas = deltas[previous_delta]

    if not next_deltas:
        return None

    predicted_delta, count = Counter(next_deltas).most_common(1)[0]
    probability = count / len(next_deltas)

    if probability >= min_probability:
        return add_delta(values[-1], predicted_delta)
    else:
        return None


def group_by_column(request, query, group_column, sort_column,
                    default_group=None, transform=None):
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

    default_group = default_group or request.translate(_("General"))

    records = query.order_by(nullsfirst(group_column))
    records = request.exclude_invisible(records)

    grouped = OrderedDict()

    def group_key(record):
        return getattr(record, group_column.name) or default_group

    def sort_key(record):
        return getattr(record, sort_column.name)

    transform = transform or (lambda v: v)

    for group, items in groupby(records, group_key):
        grouped[group] = sorted([i for i in items], key=sort_key)
        grouped[group] = [transform(i) for i in grouped[group]]

    return grouped


def keywords_first(keywords):
    """ Returns a sort key which preferrs values matching the given keywords
    before other values which are sorted alphabetically.

    """
    assert hasattr(keywords, 'index')

    def sort_key(v):
        try:
            return keywords.index(v) - len(keywords), ''
        except ValueError:
            return 0, v


def rrulestr(recurrence, **kwargs):
    """ A dateutil rrulestr wrapper that works around
    https://github.com/dateutil/dateutil/issues/652

    """

    if 'DTSTART' not in recurrence and 'dtstart' not in kwargs:
        kwargs['dtstart'] = sedate.utcnow()

    return rrule.rrulestr(recurrence, **kwargs)
