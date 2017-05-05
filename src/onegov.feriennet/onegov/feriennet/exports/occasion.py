import sedate

from onegov.activity import Activity, Occasion
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.forms import PeriodExportForm
from onegov.feriennet.utils import decode_name
from onegov.org.models import Export
from sqlalchemy.orm import joinedload


ACTIVITY_STATES = {
    'accepted': _("Accepted"),
    'archived': _("Archived"),
    'preview': _("Preview"),
    'proposed': _("Proposed"),
    'published': _("Published")
}

WEEKDAYS = {
    0: _("Monday"),
    1: _("Tuesday"),
    2: _("Wednesday"),
    3: _("Thursday"),
    4: _("Friday"),
    5: _("Saturday"),
    6: _("Sunday")
}

SALUTATIONS = {
    'mr': _("Mr."),
    'ms': _("Ms.")
}


@FeriennetApp.export(
    id='durchfuehrungen',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_("Occasions"),
    explanation=_("Exports activities with an occasion in the given period."),
)
class OccasionExport(Export):

    def run(self, form, session):
        return self.rows(session, form.selected_period)

    def query(self, session, period):
        q = session.query(Occasion)
        q = q.filter(Occasion.period_id == period.id)
        q = q.options(joinedload(Occasion.activity).joinedload(Activity.user))
        q = q.order_by(Occasion.order)

        return q

    def rows(self, session, period):
        for occasion in self.query(session, period):
            for date in occasion.dates:
                start, end = date.localized_start, date.localized_end

                yield (
                    (k, v) for k, v in self.fields(
                        period, occasion, start, end)
                )

    def fields(self, period, occasion, start, end):
        yield from self.activity_fields(occasion.activity)
        yield from self.occasion_fields(period, occasion, start, end)
        yield from self.organiser_fields(occasion.activity.user)

    def activity_fields(self, activity):
        yield _("Title"), activity.title
        yield _("Lead"), activity.lead
        yield _("Text"), activity.text
        yield _("Status"), ACTIVITY_STATES[activity.state]
        yield _("Location"), activity.location

    def occasion_fields(self, period, occasion, start, end):
        o = occasion

        cost = 0 if period.all_inclusive else period.booking_cost
        cost += occasion.cost or 0

        weekdays_order = tuple(WEEKDAYS.values())
        weekdays = {WEEKDAYS[d.weekday()] for d in sedate.dtrange(start, end)}
        weekdays = list(weekdays)
        weekdays.sort(key=weekdays_order.index)

        cost = 0 if period.all_inclusive else period.booking_cost
        cost += occasion.cost or 0

        yield _("Rescinded"), o.cancelled
        yield _("Start"), start
        yield _("End"), end
        yield _("Weekdays"), weekdays
        yield _("Note"), o.note
        yield _("Age"), '{} - {}'.format(o.age.lower, o.age.upper - 1)
        yield _("Spots"), '{} - {}'.format(o.spots.lower, o.spots.upper - 1)
        yield _("Cost"), '{:.2f}'.format(cost)
        yield _("Meeting Point"), o.meeting_point
        yield _("May Overlap"), o.exclude_from_overlap_check

    def organiser_fields(self, organiser):
        org_data = organiser.data or {}
        salutation = org_data.get('salutation')
        first_name, last_name = decode_name(organiser.realname)
        daily_email = bool(org_data.get('daily_ticket_statistics'))

        yield _("Organiser Salutation"), SALUTATIONS.get(salutation, '')
        yield _("Organiser First Name"), first_name or ''
        yield _("Organiser Last Name"), last_name or ''
        yield _("Organiser Organisation"), org_data.get('organisation', '')
        yield _("Organiser Address"), org_data.get('address', '')
        yield _("Organiser Zipcode"), org_data.get('zip_code', '')
        yield _("Organiser Location"), org_data.get('place', '')
        yield _("Organiser E-Mail"), organiser.username
        yield _("Organiser Phone"), org_data.get('phone', '')
        yield _("Organiser Emergency"), org_data.get('emergency', '')
        yield _("Organiser Website"), org_data.get('website', '')
        yield _("Organiser Bank Account"), org_data.get('bank_account', '')
        yield _("Organiser Beneficiary"), org_data.get('bank_beneficiary', '')
        yield _("Organiser Status E-Mail"), daily_email
