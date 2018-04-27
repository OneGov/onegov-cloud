import re

from html import unescape
from onegov.core import mail
from onegov.feriennet import _
from onegov.feriennet.exports.const import ACTIVITY_STATES
from onegov.feriennet.exports.const import BOOKING_STATES
from onegov.feriennet.exports.const import GENDERS
from onegov.feriennet.exports.const import ROLES
from onegov.feriennet.exports.const import SALUTATIONS
from onegov.feriennet.utils import decode_name
from onegov.org.models import Export


SPACES = re.compile(r'[ ]+')


def remove_duplicate_spaces(text):
    return SPACES.sub(' ', text)


def html_to_text(html):
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

    def booking_fields(self, booking):
        state = booking.period_bound_booking_state(booking.period)

        yield _("Booking State"), BOOKING_STATES[state]
        yield _("Booking Priority"), booking.priority
        yield _("Booking Cost"), booking.cost

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

        if occasion.period.all_inclusive:
            cost = 0
        else:
            cost = occasion.period.booking_cost or 0

        cost = occasion.cost or 0

        yield _("Occasion Rescinded"), occasion.cancelled
        yield _("Occasion Dates"), dates
        yield _("Occasion Note"), occasion.note
        yield _("Occasion Age"), '{} - {}'.format(
            occasion.age.lower, occasion.age.upper - 1)
        yield _("Occasion Spots"), '{} - {}'.format(
            occasion.spots.lower, occasion.spots.upper - 1)
        yield _("Occasion Cost"), cost
        yield _("Occasion Meeting Point"), occasion.meeting_point
        yield _("Occasion May Overlap"), occasion.exclude_from_overlap_check

    def user_fields(self, user):
        user_data = user.data or {}
        salutation = user_data.get('salutation')
        first_name, last_name = decode_name(user.realname)
        daily_email = bool(user_data.get('daily_ticket_statistics'))

        yield _("User Login"), user.username
        yield _("User Role"), ROLES[user.role]
        yield _("User Active"), user.active
        yield _("User Tags"), user_data.get('tags', ())
        yield _("User Salutation"), SALUTATIONS.get(salutation, '')
        yield _("User First Name"), first_name or ''
        yield _("User Last Name"), last_name or ''
        yield _("User Organisation"), user_data.get('organisation', '')
        yield _("User Address"), user_data.get('address', '')
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
        yield _("User Status E-Mail"), daily_email

    def invoice_item_fields(self, item):
        yield _("Invoice Item Group"), item.group
        yield _("Invoice Item Text"), item.text
        yield _("Invoice Item Code"), item.display_code
        yield _("Invoice Item ESR"), item.display_esr_code
        yield _("Invoice Item Paid"), item.paid
        yield _("Invoice Item Transaction ID"), item.tid or ''
        yield _("Invoice Item Source"), item.source or ''
        yield _("Invoice Item Unit"), item.unit
        yield _("Invoice Item Quantity"), item.quantity
        yield _("Invoice Item Amount"), item.amount
