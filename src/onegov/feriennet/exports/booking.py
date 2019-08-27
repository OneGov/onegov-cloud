from onegov.activity import Activity, Attendee, Booking, Occasion
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.forms import PeriodExportForm
from onegov.feriennet.exports.base import FeriennetExport
from onegov.user import User
from sqlalchemy.orm import contains_eager, undefer


@FeriennetApp.export(
    id='buchungen',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_("Wishlist / Bookings"),
    explanation=_(
        "Exports wishlists or bookings, depending on the "
        "current state of the given period."
    ),
)
class BookingExport(FeriennetExport):

    def run(self, form, session):
        return self.rows(session, form.selected_period)

    def query(self, session, period):
        q = session.query(Booking)
        q = q.filter(Booking.period_id == period.id)

        q = q.join(Occasion)
        q = q.join(Activity)
        q = q.join(Attendee)
        q = q.join(User)
        q = q.options(undefer('*'))

        q = q.options(
            contains_eager(Booking.attendee).contains_eager(Attendee.user))
        q = q.options(
            contains_eager(Booking.occasion).contains_eager(Occasion.activity))

        q = q.order_by(
            Activity.order,
            Occasion.order,
            Attendee.name,
            User.username,
            Booking.priority
        )

        return q

    def rows(self, session, period):
        for booking in self.query(session, period):
            yield ((k, v) for k, v in self.fields(period, booking))

    def fields(self, period, booking):
        yield from self.booking_fields(booking)
        yield from self.activity_fields(booking.occasion.activity)
        yield from self.occasion_fields(booking.occasion)
        yield from self.attendee_fields(booking.attendee)
        yield from self.user_fields(booking.attendee.user)
