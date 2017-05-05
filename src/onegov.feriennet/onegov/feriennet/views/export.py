import sedate

from collections import OrderedDict
from onegov.activity import Activity, Occasion
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import ExportCollection
from onegov.feriennet.forms import PeriodExportForm
from onegov.feriennet.layout import ExportCollectionLayout
from onegov.feriennet.utils import decode_name
from onegov.org.elements import Link
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


@FeriennetApp.html(
    model=ExportCollection,
    permission=Secret,
    template='exportcollection.pt')
def view_export_collection(self, request):
    return {
        'layout': ExportCollectionLayout(self, request),
        'model': self,
        'title': _("Exports")
    }


@FeriennetApp.form(
    model=ExportCollection,
    name='export-durchfuehrungen',
    permission=Secret,
    form=PeriodExportForm,
    template='export.pt')
def handle_export_occasions(self, request, form):
    layout = ExportCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_("Export Occasions"), '#'))

    if form.submitted(request):
        rows = tuple(
            run_export_occasions(
                period=form.selected_period,
                session=request.app.session(),
                formatter=layout.export_formatter(form.format)))

        return form.as_export_response(rows, title=request.translate(_(
            "Occasions"
        )))

    return {
        'layout': layout,
        'form': form,
        'title': _("Occasions Export"),
        'explanation': _(
            "Exports activities which have an occasion in the given period."
        )
    }


def run_export_occasions(period, session, formatter):
    q = session.query(Occasion)
    q = q.filter(Occasion.period_id == period.id)
    q = q.options(joinedload(Occasion.activity).joinedload(Activity.user))
    q = q.order_by(Occasion.order)

    for occasion in q:
        for date in occasion.dates:
            start, end = date.localized_start, date.localized_end

            yield OrderedDict(
                (formatter(key), formatter(value))
                for key, value in occasion_fields(
                    period, occasion, start, end, formatter
                )
            )


def occasion_fields(period, occasion, start, end, formatter):
    o = occasion

    cost = 0 if period.all_inclusive else period.booking_cost
    cost += occasion.cost or 0

    organiser = occasion.activity.user
    org_data = organiser.data or {}
    salutation = org_data.get('salutation')
    first_name, last_name = decode_name(organiser.realname)
    daily_email = bool(org_data.get('daily_ticket_statistics'))

    weekdays_order = tuple(WEEKDAYS.values())
    weekdays = {WEEKDAYS[d.weekday()] for d in sedate.dtrange(start, end)}
    weekdays = list(weekdays)
    weekdays.sort(key=weekdays_order.index)
    weekdays = tuple(formatter(w) for w in weekdays)

    yield _("Status"), ACTIVITY_STATES[o.activity.state]
    yield _("Rescinded"), occasion.cancelled
    yield _("Start"), start
    yield _("End"), end
    yield _("Weekdays"), weekdays
    yield _("Title"), o.activity.title
    yield _("Age"), '{} - {}'.format(o.age.lower, o.age.upper - 1)
    yield _("Spots"), '{} - {}'.format(o.spots.lower, o.spots.upper - 1)
    yield _("Lead"), o.activity.lead
    yield _("Text"), o.activity.text
    yield _("Note"), o.note
    yield _("Cost"), '{:.2f}'.format(cost)
    yield _("Location"), o.activity.location
    yield _("Meeting Point"), o.meeting_point
    yield _("May Overlap"), o.exclude_from_overlap_check
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
