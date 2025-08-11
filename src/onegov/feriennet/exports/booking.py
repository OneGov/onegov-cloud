from __future__ import annotations

from onegov.activity import Activity, Attendee, Booking, Occasion
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.forms import PeriodExportForm
from onegov.feriennet.exports.base import FeriennetExport
from onegov.user import User
from sqlalchemy.orm import contains_eager, undefer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.activity.models import BookingPeriod
    from sqlalchemy.orm import Query, Session


@FeriennetApp.export(
    id='buchungen',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_('Wishlist / Bookings'),
    explanation=_(
        'Exports wishlists or bookings, depending on the '
        'current state of the given period.'
    ),
)
class BookingExport(FeriennetExport):

    def run(
        self,
        form: PeriodExportForm,  # type:ignore[override]
        session: Session
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        assert form.selected_period is not None

        self.users = {
            user.username: user for user in
            session.query(User).options(undefer('*'))
        }

        return self.rows(session, form.selected_period)

    def query(self, session: Session, period: BookingPeriod) -> Query[Booking]:
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

    def rows(
        self,
        session: Session,
        period: BookingPeriod
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        for booking in self.query(session, period):
            yield ((k, v) for k, v in self.fields(period, booking))

    def fields(
        self,
        period: BookingPeriod,
        booking: Booking
    ) -> Iterator[tuple[str, Any]]:

        yield from self.booking_fields(booking)
        yield from self.activity_fields(booking.occasion.activity)
        yield from self.occasion_fields(booking.occasion)
        yield from self.attendee_fields(booking.attendee)
        yield from self.invoice_attendee_fields(booking.attendee)
        yield from self.user_fields(booking.attendee.user)
        yield from self.organiser_fields(
            self.users[booking.occasion.activity.username])
