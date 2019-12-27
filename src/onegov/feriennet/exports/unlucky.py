from onegov.activity import AttendeeCollection, Attendee, Booking
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodSelectForm
from onegov.form import merge_forms
from onegov.org.forms import ExportForm
from sqlalchemy import and_, not_


@FeriennetApp.export(
    id='unlucky',
    form_class=merge_forms(ExportForm, PeriodSelectForm),
    permission=Secret,
    title=_("Attendees without Bookings"),
    explanation=_("Attendees who were not granted any of their wishes"),
)
class UnluckyExport(FeriennetExport):

    def run(self, form, session):
        return self.rows(session, form.selected_period)

    def query(self, session, period):
        with_any_bookings = session.query(Booking.attendee_id).filter(
            Booking.period_id == period.id).subquery()

        with_accepted_bookings = session.query(Booking.attendee_id).filter(
            Booking.state == 'accepted',
            Booking.period_id == period.id).subquery()

        return AttendeeCollection(session).query().filter(
            and_(
                Attendee.id.in_(with_any_bookings),
                not_(Attendee.id.in_(with_accepted_bookings)),
            ))

    def rows(self, session, period):
        for user in self.query(session, period):
            yield ((k, v) for k, v in self.fields(user))

    def fields(self, attendee):
        yield from self.attendee_fields(attendee)
        yield from self.user_fields(attendee.user)
