import re

from itertools import chain
from html import unescape
from onegov.core import mail
from onegov.feriennet import _
from onegov.feriennet.exports.const import ACTIVITY_STATES
from onegov.feriennet.exports.const import BOOKING_STATES
from onegov.feriennet.exports.const import FREQUENCIES
from onegov.feriennet.exports.const import GENDERS
from onegov.feriennet.exports.const import ROLES
from onegov.feriennet.exports.const import SALUTATIONS
from onegov.feriennet.utils import decode_name
from onegov.org.models import Export


SPACES = re.compile(r'[ ]+')

STREET = re.compile(r"""
    # street name
    (?P<street>[\D\-\.\s]+)

    # punctuation between
    [\s,]*

    # street number
    (?P<number>[0-9]{1}[0-9]*\s?[\w]?)?
    """, re.UNICODE | re.VERBOSE)


class Street:

    __slots__ = ('name', 'number')

    def __init__(self, name, number):
        self.name = name and name.strip(' \n,').title()
        self.number = number and number.strip(' \n,').lower().replace(' ', '')


def score_street_match(match):
    score = 0

    if match:
        if match.group('street'):
            score += 1

        if match.group('street') and 'strasse' in match.group('street'):
            score += 1

        if match.group('number'):
            score += 1

    return score


def extract_street(address):
    if not address or not address.strip():
        return Street(None, None)

    lines = chain(address.splitlines(), (address.replace('\n', ' '), ))

    matches = [STREET.match(l) for l in lines]
    match = max(matches, key=score_street_match)

    if match:
        return Street(match.group('street'), match.group('number'))

    return Street(name=address.replace('\n', ''), number=None)


def remove_duplicate_spaces(text):
    return SPACES.sub(' ', text)


def html_to_text(html):
    if not html:
        return ''

    return remove_duplicate_spaces(mail.html_to_text(
        unescape(html),
        ul_item_mark='•',
        strong_mark='',
        emphasis_mark=''
    ))


class FeriennetExport(Export):

    def activity_fields(self, activity):
        yield _("Activity Title"), activity.title
        yield _("Activity Lead"), activity.lead
        yield _("Activity Text"), html_to_text(activity.text)
        yield _("Activity Text (HTML)"), activity.text
        yield _("Activity Status"), ACTIVITY_STATES[activity.state]
        yield _("Activity Location"), activity.location
        yield _("Activity Tags"), "\n".join(sorted(activity.tags or []))

    def booking_fields(self, booking):
        yield _("Booking State"), BOOKING_STATES[booking.state]
        yield _("Booking Priority"), booking.priority
        yield _("Booking Cost"), booking.cost
        yield _("Booking Date"), booking.created.date()

    def attendee_fields(self, attendee):
        first_name, last_name = decode_name(attendee.name)

        yield _("Attendee First Name"), first_name or ''
        yield _("Attendee Last Name"), last_name or ''
        yield _("Attendee Birth Date"), attendee.birth_date
        yield _("Attendee Gender"), GENDERS.get(attendee.gender, '')
        yield _("Attendee Notes"), attendee.notes
        yield _("Attendee Booking-Limit"), attendee.limit or ''

    def occasion_fields(self, occasion):
        dates = [
            (d.localized_start, d.localized_end)
            for d in occasion.dates
        ]

        yield _("Occasion Rescinded"), occasion.cancelled
        yield _("Occasion Dates"), dates
        yield _("Occasion Note"), occasion.note
        yield _("Occasion Age"), '{} - {}'.format(
            occasion.age.lower, occasion.age.upper - 1)
        yield _("Occasion Spots"), '{} - {}'.format(
            occasion.spots.lower, occasion.spots.upper - 1)
        yield _("Occasion Cost"), occasion.cost or 0
        yield _("Occasion Custom Booking Cost"), occasion.booking_cost or 0
        yield _("Occasion Meeting Point"), occasion.meeting_point
        yield _("Occasion May Overlap"), occasion.exclude_from_overlap_check

    def occasion_need_fields(self, need):
        yield _("Need Number"), '{} - {}'.format(
            need.number.lower, need.number.upper - 1)
        yield _("Need Name"), need.name
        yield _("Need Description"), need.description

    def activity_tags(self, tags):
        yield _("Activity Tags"), "\n".join(sorted(tags or []))

    def user_fields(self, user):
        user_data = user.data or {}
        salutation = user_data.get('salutation')
        first_name, last_name = decode_name(user.realname)
        status_email = user_data.get('ticket_statistics', 'never')
        street = extract_street(user_data.get('address', None))

        yield _("User Login"), user.username
        yield _("User Role"), ROLES[user.role]
        yield _("User Active"), user.active
        yield _("User Tags"), user_data.get('tags', ())
        yield _("User Salutation"), SALUTATIONS.get(salutation, '')
        yield _("User First Name"), first_name or ''
        yield _("User Last Name"), last_name or ''
        yield _("User Organisation"), user_data.get('organisation', '')
        yield _("User Address"), user_data.get('address', '')
        yield _("User Street"), street.name or ''
        yield _("User Street Number"), street.number or ''
        yield _("User Zipcode"), user_data.get('zip_code', '')
        yield _("User Location"), user_data.get('place', '')
        yield _("User Political Municipality"), \
            user_data.get('political_municipality', '')
        yield _("User E-Mail"), user_data.get('email', '')
        yield _("User Phone"), user_data.get('phone', '')
        yield _("User Emergency"), user_data.get('emergency', '')
        yield _("User Website"), user_data.get('website', '')
        yield _("User Bank Account"), user_data.get('bank_account', '')
        yield _("User Beneficiary"), user_data.get('bank_beneficiary', '')
        yield _("User Status E-Mail"), FREQUENCIES.get(status_email, '')
        yield _("User TOS Accepted"), user_data.get('tos_accepted', False)

    def invoice_item_fields(self, item):
        yield _("Invoice Item Group"), item.group
        yield _("Invoice Item Text"), item.text
        yield _("Invoice Item Paid"), item.paid
        yield _("Invoice Item Payment Date"), item.payment_date
        yield _("Invoice Item Transaction ID"), item.tid or ''
        yield _("Invoice Item Source"), item.source or ''
        yield _("Invoice Item Unit"), item.unit
        yield _("Invoice Item Quantity"), item.quantity
        yield _("Invoice Item Amount"), item.amount

        yield _("Invoice Item References"), '\n'.join(
            r.readable for r in item.invoice.references
        )

    def organiser_fields(self, organiser):
        user_data = organiser.data or {}
        first_name, last_name = decode_name(organiser.realname)
        street = extract_street(user_data.get('address', None))

        yield _("Organiser Last Name"), last_name or ''
        yield _("Organiser First Name"), first_name or ''
        yield _("Organiser Organisation"), user_data.get('organisation', '')
        yield _("Organiser Address"), user_data.get('address', '')
        yield _("Organiser Street"), street.name or ''
        yield _("Organiser Street Number"), street.number or ''
        yield _("Organiser Zipcode"), user_data.get('zip_code', '')
        yield _("Organiser Location"), user_data.get('place', '')
        yield _("Organiser E-Mail"), user_data.get('email', '')
        yield _("Organiser Phone"), user_data.get('phone', '')
        yield _("Organiser Website"), user_data.get('website', '')
        yield _("Organiser Bank Account"), user_data.get('bank_account', '')
        yield _("Organiser Beneficiary"), user_data.get('bank_beneficiary', '')

    def volunteer_fields(self, volunteer):
        need = volunteer.need
        occasion = need.occasion
        activity = occasion.activity
        dates = [
            (d.localized_start, d.localized_end)
            for d in occasion.dates
        ]

        yield _("Activity Title"), activity.title
        yield _("Occasion Dates"), dates
        yield _("Occasion Rescinded"), occasion.cancelled
        yield _("Need Name"), need.name
        yield _("Need Number"), '{} - {}'.format(
            need.number.lower, need.number.upper - 1)
        yield _("Confirmed Volunteers"), sum(
            v.state == "confirmed" for v in need.volunteers)
        yield _("Volunteer State"), volunteer.state
        yield _("First Name"), volunteer.first_name
        yield _("Last Name"), volunteer.last_name
        yield _("Birth Date"), volunteer.birth_date
        yield _("Organisation"), volunteer.organisation
        yield _("Place"), volunteer.place
        yield _("E-Mail"), volunteer.email
        yield _("Phone"), volunteer.phone
        yield _("Address"), volunteer.address
