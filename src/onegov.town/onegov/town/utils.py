import sedate

from datetime import datetime, time
from isodate import parse_date, parse_datetime
from libres.modules import errors as libres_errors
from lxml import etree
from lxml.html import fragments_fromstring
from onegov.ticket import TicketCollection
from onegov.town import _
from onegov.town.elements import DeleteLink, Link


def as_time(text):
    """ Takes the given text and turns it into a time. """
    if text == '24:00':
        text = '00:00'

    return time(*(int(s) for s in text.split(':'))) if text else None


def mark_images(html):
    """ Takes the given html and marks every paragraph with an 'has-img'
    class, if the paragraph contains an img element.

    """

    if not html:
        return html

    fragments = fragments_fromstring(html)

    # we perform a root xpath lookup, which will result in all paragraphs
    # being looked at - so we don't need to loop over all elements (yah, it's
    # a bit weird)
    for element in fragments[:1]:

        # instead of failing, lxml will return strings instead of elements if
        # they can't be parsed.. so we have to inspect the objects
        if not hasattr(element, 'xpath'):
            return html

        for paragraph in element.xpath('//p[img]'):
            if 'class' in paragraph.attrib:
                paragraph.attrib['class'] += ' has-img'
            else:
                paragraph.attrib['class'] = 'has-img'

    return ''.join(etree.tostring(e).decode('utf-8') for e in fragments)


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


class AllocationEventInfo(object):

    __slots__ = ['allocation', 'availability', 'request', 'translate']

    def __init__(self, allocation, availability, request):
        self.allocation = allocation
        self.availability = availability
        self.request = request
        self.translate = request.translate

    @property
    def event_start(self):
        return self.allocation.display_start().isoformat()

    @property
    def event_end(self):
        return self.allocation.display_end().isoformat()

    @property
    def event_identification(self):
        return u'{:%d.%m.%Y}: {}'.format(
            self.allocation.display_start(),
            self.event_time
        )

    @property
    def event_time(self):
        if self.allocation.whole_day:
            return self.translate(_("Whole day"))
        else:
            return '{:%H:%M} - {:%H:%M}'.format(
                self.allocation.display_start(),
                self.allocation.display_end()
            )

    @property
    def event_title(self):
        if self.allocation.partly_available:
            available = self.translate(_("${percent}% Available", mapping={
                'percent': self.availability
            }))
        else:
            quota = self.allocation.quota
            quota_left = int(quota * self.availability / 100)

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

        return '\n'.join((self.event_time, available))

    @property
    def event_class(self):
        if self.availability >= 80.0:
            return 'event-available'
        if self.availability >= 20.0:
            return 'event-partly-available'
        else:
            return 'event-unavailable'

    @property
    def event_actions(self):
        yield Link(
            _("Reserve"),
            self.request.link(self.allocation, name='reservieren'),
            classes=('new-reservation', )
        )

        if self.request.is_logged_in:
            yield Link(
                _("Edit"),
                self.request.link(self.allocation, name='bearbeiten'),
                classes=('edit-link', )
            )

            yield Link(
                _("Tickets"),
                self.request.link(TicketCollection(
                    session=self.request.app.session,
                    handler='RSV',
                    state='all',
                    extra_parameters={
                        'allocation_id': self.allocation.id
                    }
                )),
                classes=('RSV-link', )
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
            'className': self.event_class,
            'actions': [
                link(self.request).decode('utf-8')
                for link in self.event_actions
            ],
            'editurl': self.request.link(self.allocation, name='bearbeiten')
        }


libres_error_messages = {

    libres_errors.OverlappingAllocationError:
    _("A conflicting allocation exists for the requested time period."),

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
    _("The given timerange is longer than the existing allocation.")
}


def show_libres_error(e, request):
    """ Shows a human readable error message for the given libres exception,
    using request.alert.

    """

    assert type(e) in libres_error_messages, (
        "Unknown libres error {}".format(e)
    )

    request.alert(request.translate(libres_error_messages.get(type(e))))
